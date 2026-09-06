# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import yaml


def test_home_assistant_app_config():
    config_path = Path("frigatespotter/config.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config["slug"] == "frigatespotter"
    assert config["version"] == "0.2.0"
    assert config["ingress"] is True
    assert config["ingress_port"] == 8080
    assert config["hassio_api"] is True
    assert "mqtt:want" in config["services"]
    assert set(config["arch"]) == {"amd64", "aarch64"}
    assert "image" not in config
    assert Path("frigatespotter/Dockerfile").is_file()


def test_single_home_assistant_app_definition():
    configs = sorted(Path(".").glob("*/config.yaml"))
    assert configs == [Path("frigatespotter/config.yaml")]


def test_home_assistant_repository_config():
    repository = yaml.safe_load(Path("repository.yaml").read_text(encoding="utf-8"))
    assert repository["name"] == "FrigateSpotter"
    assert repository["maintainer"] == "FrigateSpotter contributors"
