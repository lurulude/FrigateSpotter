# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import json
import logging
import ssl
from collections.abc import Awaitable, Callable
from typing import Any

import paho.mqtt.client as mqtt

from .settings import Settings

_LOGGER = logging.getLogger(__name__)


class MqttBridge:
    def __init__(
        self,
        settings: Settings,
        on_event: Callable[[dict[str, Any]], Awaitable[None]],
    ):
        self.settings = settings
        self.on_event = on_event
        self.connected = False
        self.last_error: str | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.mqtt_client_id,
            protocol=mqtt.MQTTv311,
        )
        if settings.mqtt_username:
            self._client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        if settings.mqtt_tls:
            context = ssl.create_default_context(cafile=settings.mqtt_ca_cert)
            self._client.tls_set_context(context)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._client.connect_async(self.settings.mqtt_host, self.settings.mqtt_port, keepalive=60)
        self._client.loop_start()

    def stop(self) -> None:
        try:
            self._client.disconnect()
        finally:
            self._client.loop_stop()

    def publish_preset(self, camera: str, preset: str) -> None:
        topic = f"{self.settings.topic_prefix}/{camera}/ptz"
        info = self._client.publish(topic, f"preset_{preset}", qos=0, retain=False)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with rc={info.rc}")
        _LOGGER.info("PTZ command: %s -> %s", camera, preset)

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        if reason_code == 0:
            self.connected = True
            self.last_error = None
            client.subscribe(f"{self.settings.topic_prefix}/events")
            _LOGGER.info("Connected to MQTT broker and subscribed to Frigate events")
        else:
            self.connected = False
            self.last_error = f"MQTT connection failed: {reason_code}"
            _LOGGER.error(self.last_error)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        self.connected = False
        if reason_code != 0:
            self.last_error = f"MQTT disconnected: {reason_code}"
            _LOGGER.warning(self.last_error)

    def _on_message(self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:
        if self._loop is None:
            return
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _LOGGER.warning("Ignoring malformed Frigate MQTT event: %s", exc)
            return
        asyncio.run_coroutine_threadsafe(self.on_event(payload), self._loop)
