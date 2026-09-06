# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

from frigatespotter import settings as settings_module


def _clear_env(monkeypatch):
    for name in (
        "FRIGATE_URL",
        "FRIGATE_API_TOKEN",
        "MQTT_SOURCE",
        "MQTT_HOST",
        "MQTT_PORT",
        "MQTT_USERNAME",
        "MQTT_PASSWORD",
        "MQTT_TLS",
        "MQTT_CA_CERT",
        "MQTT_CLIENT_ID",
        "FRIGATE_TOPIC_PREFIX",
        "DATA_DIR",
        "SPOTTER_API_TOKEN",
        "LOG_LEVEL",
    ):
        monkeypatch.delenv(name, raising=False)


def test_home_assistant_app_discovers_frigate_and_mqtt(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    options = {
        "frigate_url": "auto",
        "frigate_api_token": "",
        "mqtt_source": "supervisor",
        "mqtt_host": "",
        "mqtt_port": 1883,
        "mqtt_username": "",
        "mqtt_password": "",
        "mqtt_tls": False,
        "mqtt_ca_cert": "",
        "frigate_topic_prefix": "frigate",
        "log_level": "INFO",
    }
    options_path = tmp_path / "options.json"
    options_path.write_text(json.dumps(options), encoding="utf-8")
    monkeypatch.setenv("SUPERVISOR_OPTIONS_PATH", str(options_path))
    monkeypatch.setenv("SUPERVISOR_TOKEN", "test-token")

    def supervisor_get(path):
        if path == "/addons":
            return {
                "addons": [
                    {"name": "Frigate", "slug": "example_frigate", "state": "started"}
                ]
            }
        if path == "/services/mqtt":
            return {
                "host": "mqtt-service",
                "port": "1883",
                "username": "service-user",
                "password": "service-password",
                "ssl": False,
            }
        raise AssertionError(path)

    monkeypatch.setattr(settings_module, "_supervisor_get", supervisor_get)
    settings = settings_module.Settings.from_env()

    assert settings.home_assistant_app is True
    assert settings.frigate_url == "http://example-frigate:5000"
    assert settings.mqtt_host == "mqtt-service"
    assert settings.mqtt_port == 1883
    assert settings.mqtt_username == "service-user"
    assert settings.mqtt_password == "service-password"
    assert settings.data_dir.as_posix() == "/data"


def test_manual_home_assistant_configuration(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    options_path = tmp_path / "options.json"
    options_path.write_text(
        json.dumps(
            {
                "frigate_url": "http://nvr.example:8971",
                "frigate_api_token": "token",
                "mqtt_source": "manual",
                "mqtt_host": "broker.example",
                "mqtt_port": 8883,
                "mqtt_username": "user",
                "mqtt_password": "password",
                "mqtt_tls": True,
                "mqtt_ca_cert": "",
                "frigate_topic_prefix": "frigate",
                "log_level": "WARNING",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SUPERVISOR_OPTIONS_PATH", str(options_path))
    monkeypatch.setenv("SUPERVISOR_TOKEN", "test-token")
    monkeypatch.setattr(settings_module, "_supervisor_get", lambda path: None)

    settings = settings_module.Settings.from_env()

    assert settings.frigate_url == "http://nvr.example:8971"
    assert settings.frigate_api_token == "token"
    assert settings.mqtt_host == "broker.example"
    assert settings.mqtt_port == 8883
    assert settings.mqtt_tls is True
    assert settings.log_level == "WARNING"
