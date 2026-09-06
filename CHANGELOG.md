# Changelog

All notable changes to FrigateSpotter will be documented here.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [0.2.0] - 2026-09-06

### Added
- Native Home Assistant App repository packaging.
- Home Assistant Ingress UI support.
- Supervisor MQTT service discovery with manual MQTT fallback.
- Automatic discovery of installed Frigate Home Assistant Apps.
- App configuration translations, persistent `/data` storage, and watchdog support.
- Multi-architecture Home Assistant image publishing for `amd64` and `aarch64`.

### Changed
- Browser API requests now work under Home Assistant Ingress path prefixes.
- Home Assistant App UI/API access is restricted to Ingress, except the internal health endpoint.
- Project documentation now treats the Home Assistant App as the recommended HA installation method.

## [0.1.0] - 2026-09-06

### Added
- Automatic discovery of Frigate cameras, zones, tracked labels, PTZ features, and presets.
- Browser UI for creating, editing, deleting, and testing PTZ routing rules.
- Camera-wide or zone-specific object triggers.
- Per-rule object labels.
- Fixed, after-clear, and no-return timeout modes.
- Optional return preset and extend-on-activity behavior.
- Per-target priority and conflict handling.
- MQTT event processing and Frigate PTZ preset commands.
- Persistent JSON rule storage.
- Optional web API bearer token.
- Docker image, Compose example, CI, and tagged GHCR publishing workflow.
