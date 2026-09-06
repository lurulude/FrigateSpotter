# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from .models import Rule


class RuleStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        self._rules: dict[str, Rule] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._rules = {item["id"]: Rule.model_validate(item) for item in raw}
        except (OSError, ValueError, KeyError):
            self._rules = {}

    def snapshot(self) -> list[Rule]:
        return [rule.model_copy(deep=True) for rule in self._rules.values()]

    def get(self, rule_id: str) -> Rule | None:
        rule = self._rules.get(rule_id)
        return rule.model_copy(deep=True) if rule else None

    async def upsert(self, rule: Rule) -> Rule:
        async with self._lock:
            self._rules[rule.id] = rule.model_copy(deep=True)
            await self._save()
        return rule

    async def delete(self, rule_id: str) -> bool:
        async with self._lock:
            if rule_id not in self._rules:
                return False
            del self._rules[rule_id]
            await self._save()
            return True

    async def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        payload = [rule.model_dump(mode="json") for rule in self._rules.values()]
        data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        await asyncio.to_thread(tmp.write_text, data, "utf-8")
        await asyncio.to_thread(tmp.replace, self.path)
