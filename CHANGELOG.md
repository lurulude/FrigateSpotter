# Changelog

All notable changes to FrigateSpotter will be documented here.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [0.1.0] - 2026-09-06

### Added
- Automatic discovery of Frigate cameras, zones, tracked labels, PTZ features, and presets.
- Browser UI for creating, editing, deleting, and testing PTZ routing rules.
- Camera-wide or zone-specific object triggers.
- Per-rule object labels, including dog/person use cases.
- Fixed, after-clear, and no-return timeout modes.
- Optional return preset and extend-on-activity behavior.
- Per-target priority and conflict handling.
- MQTT event processing and Frigate PTZ preset commands.
- Persistent JSON rule storage.
- Optional web API bearer token.
- Docker image, Compose example, CI, and tagged GHCR publishing workflow.
