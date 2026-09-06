# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class TimeoutMode(StrEnum):
    AFTER_CLEAR = "after_clear"
    FIXED = "fixed"
    NEVER = "never"


class RuleFields(BaseModel):
    name: str = ""
    enabled: bool = True
    source_camera: str
    source_zone: str = "*"
    labels: list[str] = Field(default_factory=lambda: ["person"])
    target_camera: str
    target_preset: str
    return_preset: str | None = None
    timeout_mode: TimeoutMode = TimeoutMode.AFTER_CLEAR
    timeout_seconds: int = Field(default=15, ge=0, le=86400)
    extend_on_activity: bool = True
    priority: int = Field(default=50, ge=0, le=1000)

    @field_validator("labels")
    @classmethod
    def labels_must_not_be_empty(cls, value: list[str]) -> list[str]:
        clean = sorted({label.strip() for label in value if label.strip()})
        if not clean:
            raise ValueError("at least one object label is required")
        return clean

    @field_validator("source_camera", "target_camera", "target_preset")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value

    @field_validator("source_zone")
    @classmethod
    def normalize_zone(cls, value: str) -> str:
        return value.strip() or "*"

    @field_validator("return_preset")
    @classmethod
    def normalize_return_preset(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class Rule(RuleFields):
    id: str = Field(default_factory=lambda: uuid4().hex)


class RuleCreate(RuleFields):
    def to_rule(self, rule_id: str | None = None) -> Rule:
        return Rule(id=rule_id or uuid4().hex, **self.model_dump())


class PtzTestRequest(BaseModel):
    camera: str
    preset: str


class PtzInfo(BaseModel):
    camera: str
    name: str | None = None
    features: list[str] = Field(default_factory=list)
    presets: list[str] = Field(default_factory=list)


class CameraDiscovery(BaseModel):
    name: str
    friendly_name: str | None = None
    enabled: bool = True
    zones: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    ptz: PtzInfo | None = None


class Discovery(BaseModel):
    cameras: list[CameraDiscovery] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    topic_prefix: str = "frigate"
