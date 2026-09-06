# FrigateSpotter

FrigateSpotter is an open-source PTZ routing and automation project for Frigate-based camera systems.

It is intended to discover Frigate cameras, zones, tracked object labels, PTZ-capable cameras, and available PTZ presets, then provide a simple interface for mapping detections to camera movements without hand-writing automation YAML.

## Planned capabilities

- Discover all Frigate cameras and zones.
- Discover tracked object labels such as `person`, `dog`, and `cat`.
- Discover PTZ-capable cameras and available presets/locations.
- Map a source camera or zone to a destination PTZ camera and preset.
- Support multiple trigger labels per rule.
- Configure per-rule timeout behavior.
- Extend a timeout while activity continues.
- Return the PTZ camera to a configurable home preset when a rule clears or expires.
- Support conflict and priority handling when multiple zones trigger the same PTZ camera.
- Provide a test action for discovered PTZ presets.
- Prefer standards-based integrations such as Frigate MQTT, Home Assistant, and ONVIF where practical.

## Example

A fixed camera detects a dog or person in a gate zone:

```text
kamera5 / kamera5_portti / dog, person
                  ↓
kamera4 / preset: portti
                  ↓
return home after configured timeout or when the zone clears
```

## Project status

FrigateSpotter is in early development. Interfaces and configuration formats may change before the first stable release.

## License

Copyright 2026 lurulude.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md).

## Independence

FrigateSpotter is an independent project. It is not affiliated with or endorsed by Frigate, Home Assistant, Reolink, or their respective maintainers or companies.
