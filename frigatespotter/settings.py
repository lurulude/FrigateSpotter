# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(frozen=True, slots=True)
class Settings:
    frigate_url: str
    frigate_api_token: str | None
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None
    mqtt_tls: bool
    mqtt_ca_cert: str | None
    mqtt_client_id: str
    topic_prefix: str
    data_dir: Path
    api_token: str | None
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            frigate_url=os.getenv("FRIGATE_URL", "http://frigate:5000").rstrip("/"),
            frigate_api_token=os.getenv("FRIGATE_API_TOKEN") or None,
            mqtt_host=os.getenv("MQTT_HOST", "mqtt"),
            mqtt_port=_int("MQTT_PORT", 1883),
            mqtt_username=os.getenv("MQTT_USERNAME") or None,
            mqtt_password=os.getenv("MQTT_PASSWORD") or None,
            mqtt_tls=_bool("MQTT_TLS", False),
            mqtt_ca_cert=os.getenv("MQTT_CA_CERT") or None,
            mqtt_client_id=os.getenv("MQTT_CLIENT_ID", "frigatespotter"),
            topic_prefix=os.getenv("FRIGATE_TOPIC_PREFIX", "frigate").strip("/"),
            data_dir=Path(os.getenv("DATA_DIR", "/data")),
            api_token=os.getenv("SPOTTER_API_TOKEN") or None,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
