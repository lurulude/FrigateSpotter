# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .engine import SpotterEngine
from .frigate import FrigateClient
from .models import Discovery, PtzTestRequest, Rule, RuleCreate
from .mqtt import MqttBridge
from .settings import Settings
from .storage import RuleStore

settings = Settings.from_env()
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
_LOGGER = logging.getLogger(__name__)


class AppState:
    def __init__(self) -> None:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.store = RuleStore(settings.data_dir / "rules.json")
        self.frigate = FrigateClient(settings)
        self.engine: SpotterEngine | None = None
        self.mqtt: MqttBridge | None = None
        self.discovery: Discovery | None = None
        self.discovery_lock = asyncio.Lock()


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bridge: MqttBridge
    engine = SpotterEngine(
        state.store, lambda camera, preset: bridge.publish_preset(camera, preset)
    )
    bridge = MqttBridge(settings, engine.handle_event)
    state.engine = engine
    state.mqtt = bridge
    bridge.start(asyncio.get_running_loop())
    try:
        yield
    finally:
        bridge.stop()
        await state.frigate.close()


app = FastAPI(title="FrigateSpotter", version=__version__, lifespan=lifespan)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not settings.api_token:
        return
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API token")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": __version__,
        "mqtt_connected": bool(state.mqtt and state.mqtt.connected),
    }


@app.get("/api/status", dependencies=[Depends(require_token)])
async def app_status() -> dict[str, Any]:
    assert state.engine is not None and state.mqtt is not None
    return {
        "version": __version__,
        "mqtt_connected": state.mqtt.connected,
        "mqtt_error": state.mqtt.last_error,
        **state.engine.status(),
    }


@app.get("/api/discovery", response_model=Discovery, dependencies=[Depends(require_token)])
async def discovery(refresh: bool = False) -> Discovery:
    if state.discovery is None or refresh:
        async with state.discovery_lock:
            if state.discovery is None or refresh:
                try:
                    state.discovery = await state.frigate.discover()
                except Exception as exc:  # HTTP client errors are normalized for the UI.
                    _LOGGER.exception("Frigate discovery failed")
                    raise HTTPException(
                        status_code=502, detail=f"Frigate discovery failed: {exc}"
                    ) from exc
    return state.discovery


@app.get("/api/rules", response_model=list[Rule], dependencies=[Depends(require_token)])
async def list_rules() -> list[Rule]:
    return state.store.snapshot()


@app.post("/api/rules", response_model=Rule, status_code=201, dependencies=[Depends(require_token)])
async def create_rule(payload: RuleCreate) -> Rule:
    rule = payload.to_rule()
    return await state.store.upsert(rule)


@app.put("/api/rules/{rule_id}", response_model=Rule, dependencies=[Depends(require_token)])
async def update_rule(rule_id: str, payload: RuleCreate) -> Rule:
    old_rule = state.store.get(rule_id)
    if old_rule is None:
        raise HTTPException(status_code=404, detail="rule not found")
    rule = payload.to_rule(rule_id=rule_id)
    saved = await state.store.upsert(rule)
    assert state.engine is not None
    await state.engine.rule_changed(old_rule, saved)
    return saved


@app.delete("/api/rules/{rule_id}", status_code=204, dependencies=[Depends(require_token)])
async def delete_rule(rule_id: str) -> None:
    old_rule = state.store.get(rule_id)
    if old_rule is None:
        raise HTTPException(status_code=404, detail="rule not found")
    await state.store.delete(rule_id)
    assert state.engine is not None
    await state.engine.rule_removed(old_rule)


@app.post("/api/ptz/test", dependencies=[Depends(require_token)])
async def test_ptz(payload: PtzTestRequest) -> dict[str, str]:
    assert state.engine is not None
    try:
        await state.engine.test_preset(payload.camera.strip(), payload.preset.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "sent"}


@app.get("/api/config/client", dependencies=[Depends(require_token)])
async def client_config(request: Request) -> dict[str, Any]:
    return {
        "token_required": bool(settings.api_token),
        "topic_prefix": settings.topic_prefix,
        "frigate_url": settings.frigate_url,
    }
