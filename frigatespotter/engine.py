# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .models import Rule, TimeoutMode
from .storage import RuleStore

_LOGGER = logging.getLogger(__name__)


@dataclass
class TargetState:
    current_rule_id: str | None = None
    timer: asyncio.Task[None] | None = None


class SpotterEngine:
    def __init__(self, store: RuleStore, publish_preset: Callable[[str, str], None]):
        self.store = store
        self.publish_preset = publish_preset
        self.active_events: dict[str, set[str]] = defaultdict(set)
        self.last_triggered: dict[str, float] = {}
        self.fixed_expired: set[str] = set()
        self.targets: dict[str, TargetState] = defaultdict(TargetState)
        self.last_event_at: float | None = None
        self.last_action: str | None = None
        self._lock = asyncio.Lock()

    async def handle_event(self, payload: dict[str, Any]) -> None:
        after = payload.get("after") or payload.get("before") or {}
        event_id = str(after.get("id") or "")
        camera = str(after.get("camera") or "")
        label = str(after.get("label") or "")
        if not event_id or not camera or not label:
            return

        event_type = str(payload.get("type") or "update")
        current_zones = set(after.get("current_zones") or [])
        ended = event_type == "end" or after.get("end_time") is not None
        self.last_event_at = time.time()

        async with self._lock:
            for rule in self.store.snapshot():
                if not rule.enabled or rule.source_camera != camera or label not in rule.labels:
                    continue
                in_zone = rule.source_zone == "*" or rule.source_zone in current_zones
                was_active = event_id in self.active_events[rule.id]

                if in_zone and not ended:
                    self.active_events[rule.id].add(event_id)
                    if rule.id in self.fixed_expired:
                        if was_active:
                            continue
                        self.fixed_expired.discard(rule.id)
                    await self._activate(rule, refresh=was_active)
                elif was_active:
                    self.active_events[rule.id].discard(event_id)
                    if not self.active_events[rule.id]:
                        self.fixed_expired.discard(rule.id)
                    await self._deactivate_if_clear(rule)

    async def test_preset(self, camera: str, preset: str) -> None:
        self.publish_preset(camera, preset)
        self.last_action = f"test: {camera} -> {preset}"

    async def rule_removed(self, rule: Rule) -> None:
        async with self._lock:
            self.active_events.pop(rule.id, None)
            self.fixed_expired.discard(rule.id)
            state = self.targets.get(rule.target_camera)
            if state and state.current_rule_id == rule.id:
                await self._release_target(
                    rule.target_camera,
                    state,
                    allow_same_rule=False,
                    fallback_return_preset=rule.return_preset,
                )

    async def rule_changed(self, old_rule: Rule, new_rule: Rule) -> None:
        if old_rule == new_rule:
            return
        await self.rule_removed(old_rule)

    async def _activate(self, rule: Rule, refresh: bool) -> None:
        self.last_triggered[rule.id] = time.time()
        state = self.targets[rule.target_camera]
        current = self.store.get(state.current_rule_id) if state.current_rule_id else None

        if current and current.id != rule.id and self.active_events[current.id]:
            if current.priority > rule.priority:
                return

        if state.current_rule_id != rule.id:
            self._cancel_timer(state)
            self.publish_preset(rule.target_camera, rule.target_preset)
            state.current_rule_id = rule.id
            self.last_action = (
                f"route: {rule.source_camera}/{rule.source_zone} -> "
                f"{rule.target_camera}/{rule.target_preset}"
            )
            _LOGGER.info(self.last_action)

        if rule.timeout_mode == TimeoutMode.FIXED:
            if state.timer is None or rule.extend_on_activity or not refresh:
                self._schedule_return(rule, state, rule.timeout_seconds)
        elif rule.timeout_mode == TimeoutMode.AFTER_CLEAR:
            self._cancel_timer(state)

    async def _deactivate_if_clear(self, rule: Rule) -> None:
        if self.active_events[rule.id]:
            return
        state = self.targets[rule.target_camera]
        if state.current_rule_id != rule.id:
            return
        if rule.timeout_mode == TimeoutMode.AFTER_CLEAR:
            self._schedule_return(rule, state, rule.timeout_seconds)

    def _schedule_return(self, rule: Rule, state: TargetState, delay: int) -> None:
        self._cancel_timer(state)
        state.timer = asyncio.create_task(self._return_after(rule.id, rule.target_camera, delay))

    async def _return_after(self, rule_id: str, target_camera: str, delay: int) -> None:
        try:
            await asyncio.sleep(delay)
            async with self._lock:
                state = self.targets[target_camera]
                if state.current_rule_id != rule_id:
                    return
                state.timer = None
                rule = self.store.get(rule_id)
                if rule is None:
                    await self._release_target(target_camera, state, allow_same_rule=False)
                    return
                if rule.timeout_mode == TimeoutMode.AFTER_CLEAR and self.active_events[rule_id]:
                    return
                if rule.timeout_mode == TimeoutMode.FIXED:
                    self.fixed_expired.add(rule_id)
                await self._release_target(
                    target_camera,
                    state,
                    allow_same_rule=rule.timeout_mode != TimeoutMode.FIXED,
                    fallback_return_preset=rule.return_preset,
                )
        except asyncio.CancelledError:
            raise

    async def _release_target(
        self,
        target_camera: str,
        state: TargetState,
        *,
        allow_same_rule: bool,
        fallback_return_preset: str | None = None,
    ) -> None:
        current_id = state.current_rule_id
        self._cancel_timer(state)
        candidate = self._best_active_rule(
            target_camera,
            exclude_rule_id=None if allow_same_rule else current_id,
        )
        if candidate and candidate.id != current_id:
            state.current_rule_id = None
            await self._activate(candidate, refresh=False)
            return
        if fallback_return_preset:
            self.publish_preset(target_camera, fallback_return_preset)
            self.last_action = f"return: {target_camera} -> {fallback_return_preset}"
            _LOGGER.info(self.last_action)
        state.current_rule_id = None

    def _best_active_rule(
        self, target_camera: str, exclude_rule_id: str | None = None
    ) -> Rule | None:
        candidates = [
            rule
            for rule in self.store.snapshot()
            if rule.enabled
            and rule.target_camera == target_camera
            and rule.id != exclude_rule_id
            and self.active_events[rule.id]
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda rule: (rule.priority, self.last_triggered.get(rule.id, 0.0)),
        )

    @staticmethod
    def _cancel_timer(state: TargetState) -> None:
        if state.timer is not None and not state.timer.done():
            state.timer.cancel()
        state.timer = None

    def status(self) -> dict[str, Any]:
        return {
            "last_event_at": self.last_event_at,
            "last_action": self.last_action,
            "targets": {
                camera: {"current_rule_id": state.current_rule_id}
                for camera, state in self.targets.items()
                if state.current_rule_id
            },
            "active_rules": {
                rule_id: len(events)
                for rule_id, events in self.active_events.items()
                if events
            },
        }
