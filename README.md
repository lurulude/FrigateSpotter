# FrigateSpotter

FrigateSpotter routes Frigate object detections from any camera or zone to PTZ presets on any PTZ-capable camera discovered by Frigate.

It is designed for setups where fixed cameras act as **spotters** for one or more PTZ cameras. A typical rule is:

```text
spotter_cam / entry_zone / dog, person
                  ↓
ptz_cam / preset: entry
                  ↓
zone clears + 15 seconds
                  ↓
ptz_cam / preset: home
```

No Home Assistant automation YAML and no vendor-specific camera API are required for the normal path. FrigateSpotter uses Frigate's HTTP API for discovery and Frigate MQTT topics for tracked-object events and PTZ commands.

## Features

- Discovers **all Frigate cameras**.
- Discovers zones for every camera.
- Discovers tracked object labels configured in Frigate.
- Probes every camera for ONVIF PTZ capabilities and preset names.
- Routes a camera-wide or zone-specific detection to any discovered PTZ preset.
- Supports multiple labels per rule, such as `dog` + `person`.
- Per-rule timeout modes:
  - **After zone clears**: wait until all matching objects leave, then start a delay.
  - **Fixed timeout**: return after a fixed time; optionally extend on activity.
  - **No automatic return**: leave the PTZ at the target preset.
- Optional return/home preset.
- Priorities when several spotter rules want the same PTZ camera.
- Equal-priority rules use the most recent trigger.
- Automatically resumes another active rule when a higher-priority rule releases the PTZ.
- Test button for every selected PTZ preset.
- Persistent JSON rule storage.
- Optional bearer-token protection for the web/API interface.
- MQTT authentication and TLS support.
- Docker/Compose deployment, CI, and tagged GHCR publishing.

## Requirements

- Frigate with MQTT enabled.
- Frigate HTTP API reachable from FrigateSpotter.
- An MQTT broker reachable from FrigateSpotter.
- For PTZ targets, ONVIF PTZ must be configured in Frigate and the camera must expose presets through Frigate.

Frigate's internal port `5000` is the simplest API target on a trusted Docker/Home Assistant network. If you expose Frigate through its authenticated frontend instead, configure the appropriate API access for your environment.

### Object labels

FrigateSpotter only receives labels Frigate is already tracking. For example:

```yaml
objects:
  track:
    - person
    - dog
```

## Quick start with Docker Compose

Clone the repository and edit `docker-compose.yml` for your network:

```yaml
services:
  frigatespotter:
    build: .
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      FRIGATE_URL: http://frigate:5000
      MQTT_HOST: mqtt
      MQTT_PORT: 1883
      MQTT_USERNAME: your-user
      MQTT_PASSWORD: your-password
      FRIGATE_TOPIC_PREFIX: frigate
    volumes:
      - ./data:/data
```

Then run:

```bash
docker compose up -d --build
```

Open `http://<host>:8080`.

FrigateSpotter will discover cameras, zones, tracked labels, PTZ cameras and preset names. Create routing rules in the browser.

## Example rule

| Setting | Example value |
| --- | --- |
| Source camera | `spotter_cam` |
| Zone | `entry_zone` |
| Objects | `dog`, `person` |
| PTZ camera | `ptz_cam` |
| Target preset | `entry` |
| Timeout mode | After zone clears |
| Timeout | `15` seconds |
| Return preset | `home` |

When a matching object is tracked inside `entry_zone`, FrigateSpotter sends `ptz_cam` to the `entry` preset. When the last matching object leaves, the timeout starts. If activity returns before it expires, the return is cancelled.

## Configuration

Copy `.env.example` or set environment variables directly.

| Variable | Default | Description |
| --- | --- | --- |
| `FRIGATE_URL` | `http://frigate:5000` | Frigate base URL, without `/api`. |
| `FRIGATE_API_TOKEN` | empty | Optional bearer token sent to the Frigate API. |
| `FRIGATE_TOPIC_PREFIX` | `frigate` | Frigate MQTT topic prefix. |
| `MQTT_HOST` | `mqtt` | MQTT broker hostname/IP. |
| `MQTT_PORT` | `1883` | MQTT broker port. |
| `MQTT_USERNAME` | empty | MQTT username. |
| `MQTT_PASSWORD` | empty | MQTT password. |
| `MQTT_TLS` | `false` | Enable MQTT TLS. |
| `MQTT_CA_CERT` | empty | Optional CA certificate path for MQTT TLS. |
| `MQTT_CLIENT_ID` | `frigatespotter` | MQTT client ID. |
| `DATA_DIR` | `./data` | Persistent state directory. The Docker image sets this to `/data`. |
| `SPOTTER_API_TOKEN` | empty | Optional bearer token protecting FrigateSpotter APIs. |
| `LOG_LEVEL` | `INFO` | Python logging level. |

If `SPOTTER_API_TOKEN` is set, the browser UI asks for it and stores it in that browser's local storage.

## Frigate interfaces used

FrigateSpotter intentionally relies on documented Frigate interfaces:

- `GET /api/config` for cameras, zones, and tracked-object configuration.
- `GET /api/<camera>/ptz/info` for PTZ features and preset names.
- `<topic_prefix>/events` for tracked object updates, including camera, label, and `current_zones`.
- `<topic_prefix>/<camera>/ptz` with payload `preset_<preset_name>` for PTZ preset movement.

This keeps the application camera-vendor neutral. Reolink, Dahua, Amcrest, Hikvision, or other cameras can be targets when their ONVIF PTZ/presets work through Frigate.

## Rule behavior

### After zone clears

Every matching tracked-object ID is retained. The return timer starts only after the final matching object has left the zone or ended. New activity cancels the pending return.

### Fixed timeout

The timer begins when the PTZ route triggers. With **extend on activity**, Frigate event updates restart the timer. After a fixed timeout expires, updates from the same already-active object are suppressed until it clears; a newly entering matching object may trigger the route again.

### Priorities

Priorities are numeric. Higher numbers win. A high-priority rule can preempt a lower-priority rule using the same target PTZ camera. When the high-priority route clears, FrigateSpotter first looks for another active route before sending the camera to a return preset.

## Data and security

Rules are saved to `${DATA_DIR}/rules.json`. FrigateSpotter does **not** store camera credentials; PTZ control is delegated to Frigate.

Camera systems are security-sensitive. Recommended deployment:

- Keep FrigateSpotter, Frigate, and MQTT on a trusted network/VLAN.
- Use MQTT authentication and TLS where appropriate.
- Set `SPOTTER_API_TOKEN` if the web UI is accessible outside a trusted LAN.
- Do not expose Frigate's unauthenticated internal API port directly to the Internet.

See [SECURITY.md](SECURITY.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
python -m frigatespotter
```

The UI is served at `http://localhost:8080`.

## Project status

`0.1.0` is the first usable beta. The core discovery, routing, timeout, return, and conflict-management paths are implemented. Feedback from different Frigate/PTZ camera combinations is welcome.

## License

Copyright 2026 FrigateSpotter contributors.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md).

## Independence

FrigateSpotter is an independent project. It is not affiliated with or endorsed by Frigate, Home Assistant, Reolink, or their respective maintainers or companies.
