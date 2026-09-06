# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import yaml


def test_home_assistant_app_config():
    config = yaml.safe_load(Path("homeassistant/config.yaml").read_text(encoding="utf-8"))
    assert config["slug"] == "frigatespotter"
    assert config["version"] == "0.2.0"
    assert config["ingress"] is True
    assert config["ingress_port"] == 8080
    assert config["hassio_api"] is True
    assert "mqtt:want" in config["services"]
    assert set(config["arch"]) == {"amd64", "aarch64"}
    assert config["image"].endswith("/frigatespotter")


def test_home_assistant_repository_config():
    repository = yaml.safe_load(Path("repository.yaml").read_text(encoding="utf-8"))
    assert repository["name"] == "FrigateSpotter"
    assert repository["maintainer"] == "FrigateSpotter contributors"
