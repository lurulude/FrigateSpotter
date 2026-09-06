# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _bool_value(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _int_value(value: Any, default: int) -> int:
    if value in (None, ""):
        return default
    return int(value)


def _load_app_options() -> dict[str, Any]:
    path = Path(os.getenv("SUPERVISOR_OPTIONS_PATH", "/data/options.json"))
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _value(options: dict[str, Any], env_name: str, option_name: str, default: Any = None) -> Any:
    env_value = os.getenv(env_name)
    if env_value is not None:
        return env_value
    return options.get(option_name, default)


def _supervisor_get(path: str) -> dict[str, Any] | None:
    token = os.getenv("SUPERVISOR_TOKEN")
    if not token:
        return None
    request = urllib.request.Request(
        f"http://supervisor{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def _auto_frigate_url() -> str:
    supervisor = _supervisor_get("/addons")
    addons = supervisor.get("addons", []) if supervisor else []
    candidates: list[tuple[int, str]] = []
    for addon in addons:
        if not isinstance(addon, dict):
            continue
        name = str(addon.get("name", ""))
        slug = str(addon.get("slug", ""))
        haystack = f"{name} {slug}".lower()
        if "frigate" not in haystack or "proxy" in haystack or not slug:
            continue
        score = 0
        if name.strip().lower() == "frigate":
            score += 100
        if addon.get("state") == "started":
            score += 30
        if "beta" not in haystack:
            score += 10
        if "full access" not in haystack and "-fa" not in slug:
            score += 5
        candidates.append((score, slug))
    if candidates:
        _, slug = max(candidates)
        return f"http://{slug.replace('_', '-')}:5000"
    return "http://ccab4aaf-frigate:5000"


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
    home_assistant_app: bool

    @classmethod
    def from_env(cls) -> Settings:
        options = _load_app_options()
        ha_app = bool(os.getenv("SUPERVISOR_TOKEN")) and bool(options)

        frigate_url = str(
            _value(options, "FRIGATE_URL", "frigate_url", "auto" if ha_app else "http://frigate:5000")
        ).strip()
        if frigate_url.lower() == "auto":
            frigate_url = _auto_frigate_url()

        mqtt_source = str(
            _value(options, "MQTT_SOURCE", "mqtt_source", "supervisor" if ha_app else "manual")
        ).strip().lower()
        mqtt_host = str(_value(options, "MQTT_HOST", "mqtt_host", "mqtt")).strip()
        mqtt_port = _int_value(_value(options, "MQTT_PORT", "mqtt_port", 1883), 1883)
        mqtt_username = str(_value(options, "MQTT_USERNAME", "mqtt_username", "")).strip() or None
        mqtt_password = str(_value(options, "MQTT_PASSWORD", "mqtt_password", "")).strip() or None
        mqtt_tls = _bool_value(_value(options, "MQTT_TLS", "mqtt_tls", False))
        mqtt_ca_cert = str(_value(options, "MQTT_CA_CERT", "mqtt_ca_cert", "")).strip() or None

        if mqtt_source == "supervisor":
            service = _supervisor_get("/services/mqtt")
            if service:
                mqtt_host = str(service.get("host") or mqtt_host)
                mqtt_port = _int_value(service.get("port"), mqtt_port)
                mqtt_username = str(service.get("username") or "").strip() or None
                mqtt_password = str(service.get("password") or "").strip() or None
                mqtt_tls = _bool_value(service.get("ssl"), mqtt_tls)

        data_default = "/data" if ha_app else "./data"
        return cls(
            frigate_url=frigate_url.rstrip("/"),
            frigate_api_token=str(_value(options, "FRIGATE_API_TOKEN", "frigate_api_token", "")).strip() or None,
            mqtt_host=mqtt_host,
            mqtt_port=mqtt_port,
            mqtt_username=mqtt_username,
            mqtt_password=mqtt_password,
            mqtt_tls=mqtt_tls,
            mqtt_ca_cert=mqtt_ca_cert,
            mqtt_client_id=str(_value(options, "MQTT_CLIENT_ID", "mqtt_client_id", "frigatespotter")).strip() or "frigatespotter",
            topic_prefix=str(_value(options, "FRIGATE_TOPIC_PREFIX", "frigate_topic_prefix", "frigate")).strip("/"),
            data_dir=Path(os.getenv("DATA_DIR", data_default)),
            api_token=os.getenv("SPOTTER_API_TOKEN") or None,
            log_level=str(_value(options, "LOG_LEVEL", "log_level", "INFO")).upper(),
            home_assistant_app=ha_app,
        )
