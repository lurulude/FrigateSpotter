# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .models import CameraDiscovery, Discovery, PtzInfo
from .settings import Settings

_LOGGER = logging.getLogger(__name__)


class FrigateClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        headers = {"Accept": "application/json"}
        if settings.frigate_api_token:
            headers["Authorization"] = f"Bearer {settings.frigate_api_token}"
        self._client = httpx.AsyncClient(
            base_url=f"{settings.frigate_url}/api",
            headers=headers,
            timeout=httpx.Timeout(8.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_config(self) -> dict[str, Any]:
        response = await self._client.get("/config")
        response.raise_for_status()
        return response.json()

    async def get_ptz_info(self, camera: str) -> PtzInfo | None:
        try:
            response = await self._client.get(f"/{camera}/ptz/info")
            response.raise_for_status()
            data = response.json()
            features = list(data.get("features") or [])
            presets = list(data.get("presets") or [])
            if not features and not presets:
                return None
            return PtzInfo(
                camera=camera,
                name=data.get("name"),
                features=features,
                presets=presets,
            )
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            _LOGGER.debug("PTZ discovery failed for %s: %s", camera, exc)
            return None

    async def discover(self) -> Discovery:
        config = await self.get_config()
        camera_config: dict[str, Any] = config.get("cameras") or {}
        global_labels = _extract_track_labels(config.get("objects"))

        names = list(camera_config)
        ptz_results = await asyncio.gather(*(self.get_ptz_info(name) for name in names))
        ptz_by_camera = {info.camera: info for info in ptz_results if info is not None}

        all_labels = set(global_labels)
        cameras: list[CameraDiscovery] = []
        for name, camera in camera_config.items():
            zones = sorted((camera.get("zones") or {}).keys())
            labels = _extract_track_labels(camera.get("objects")) or global_labels
            all_labels.update(labels)
            cameras.append(
                CameraDiscovery(
                    name=name,
                    friendly_name=camera.get("friendly_name"),
                    enabled=camera.get("enabled", True),
                    zones=zones,
                    labels=sorted(labels),
                    ptz=ptz_by_camera.get(name),
                )
            )

        return Discovery(
            cameras=sorted(cameras, key=lambda item: item.name.lower()),
            labels=sorted(all_labels),
            topic_prefix=self.settings.topic_prefix,
        )


def _extract_track_labels(objects: Any) -> list[str]:
    if not isinstance(objects, dict):
        return []
    track = objects.get("track") or []
    if isinstance(track, dict):
        return sorted(str(key) for key in track)
    if isinstance(track, list):
        return sorted(str(item) for item in track)
    return []
