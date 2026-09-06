# SPDX-License-Identifier: Apache-2.0
import asyncio

import pytest

from frigatespotter.engine import SpotterEngine
from frigatespotter.models import Rule, TimeoutMode
from frigatespotter.storage import RuleStore


@pytest.fixture
async def store(tmp_path):
    return RuleStore(tmp_path / "rules.json")


async def _event(
    event_id="e1",
    zones=None,
    event_type="update",
    label="dog",
    camera="kamera5",
):
    return {
        "type": event_type,
        "after": {
            "id": event_id,
            "camera": camera,
            "label": label,
            "current_zones": zones or [],
            "end_time": 1 if event_type == "end" else None,
        },
    }


@pytest.mark.asyncio
async def test_zone_match_routes_and_returns_after_clear(store):
    calls = []
    rule = Rule(
        source_camera="kamera5",
        source_zone="kamera5_portti",
        labels=["dog", "person"],
        target_camera="kamera4",
        target_preset="portti",
        return_preset="home",
        timeout_mode=TimeoutMode.AFTER_CLEAR,
        timeout_seconds=0,
    )
    await store.upsert(rule)
    engine = SpotterEngine(store, lambda camera, preset: calls.append((camera, preset)))

    await engine.handle_event(await _event(zones=["kamera5_portti"]))
    assert calls == [("kamera4", "portti")]

    await engine.handle_event(await _event(zones=[]))
    await asyncio.sleep(0.01)
    assert calls[-1] == ("kamera4", "home")


@pytest.mark.asyncio
async def test_wrong_label_does_not_route(store):
    calls = []
    rule = Rule(
        source_camera="kamera5",
        source_zone="kamera5_portti",
        labels=["dog"],
        target_camera="kamera4",
        target_preset="portti",
    )
    await store.upsert(rule)
    engine = SpotterEngine(store, lambda camera, preset: calls.append((camera, preset)))

    await engine.handle_event(await _event(zones=["kamera5_portti"], label="cat"))
    assert calls == []


@pytest.mark.asyncio
async def test_higher_priority_rule_wins(store):
    calls = []
    low = Rule(
        name="low",
        source_camera="cam1",
        source_zone="z1",
        labels=["dog"],
        target_camera="ptz",
        target_preset="low",
        priority=10,
    )
    high = Rule(
        name="high",
        source_camera="cam2",
        source_zone="z2",
        labels=["dog"],
        target_camera="ptz",
        target_preset="high",
        priority=100,
    )
    await store.upsert(low)
    await store.upsert(high)
    engine = SpotterEngine(store, lambda camera, preset: calls.append((camera, preset)))

    await engine.handle_event(await _event(camera="cam1", zones=["z1"]))
    await engine.handle_event(await _event(event_id="e2", camera="cam2", zones=["z2"]))
    assert calls == [("ptz", "low"), ("ptz", "high")]


@pytest.mark.asyncio
async def test_lower_priority_rule_resumes_when_high_rule_clears(store):
    calls = []
    low = Rule(
        source_camera="cam1",
        source_zone="z1",
        labels=["dog"],
        target_camera="ptz",
        target_preset="low",
        priority=10,
    )
    high = Rule(
        source_camera="cam2",
        source_zone="z2",
        labels=["dog"],
        target_camera="ptz",
        target_preset="high",
        timeout_seconds=0,
        priority=100,
    )
    await store.upsert(low)
    await store.upsert(high)
    engine = SpotterEngine(store, lambda camera, preset: calls.append((camera, preset)))

    await engine.handle_event(await _event(camera="cam1", zones=["z1"]))
    await engine.handle_event(await _event(event_id="e2", camera="cam2", zones=["z2"]))
    await engine.handle_event(await _event(event_id="e2", camera="cam2", zones=[]))
    await asyncio.sleep(0.01)

    assert calls[-1] == ("ptz", "low")


@pytest.mark.asyncio
async def test_fixed_timeout_suppresses_same_active_event_until_clear(store):
    calls = []
    rule = Rule(
        source_camera="cam1",
        source_zone="z1",
        labels=["dog"],
        target_camera="ptz",
        target_preset="gate",
        return_preset="home",
        timeout_mode=TimeoutMode.FIXED,
        timeout_seconds=0,
        extend_on_activity=False,
    )
    await store.upsert(rule)
    engine = SpotterEngine(store, lambda camera, preset: calls.append((camera, preset)))

    await engine.handle_event(await _event(camera="cam1", zones=["z1"]))
    await asyncio.sleep(0.01)
    assert calls == [("ptz", "gate"), ("ptz", "home")]

    await engine.handle_event(await _event(camera="cam1", zones=["z1"]))
    assert calls == [("ptz", "gate"), ("ptz", "home")]

    await engine.handle_event(await _event(camera="cam1", zones=[]))
    await engine.handle_event(await _event(event_id="e2", camera="cam1", zones=["z1"]))
    assert calls[-1] == ("ptz", "gate")
