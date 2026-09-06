# FrigateSpotter

FrigateSpotter routes Frigate object detections from any camera or zone to PTZ presets on any PTZ-capable camera discovered by Frigate.

It is designed for systems where one or more fixed cameras act as spotters for PTZ cameras:

```text
spotter_cam / entry_zone / dog, person
                  ↓
ptz_cam / preset: entry
                  ↓
zone clears + 15 seconds
                  ↓
ptz_cam / preset: home
```

FrigateSpotter is distributed as a **Home Assistant App** and as a standalone Docker container. Home Assistant is not required for the core routing engine.

## Features

- Discovers all Frigate cameras.
- Discovers zones and tracked object labels.
- Discovers ONVIF PTZ capabilities and preset names through Frigate.
- Routes camera-wide or zone-specific detections to PTZ presets.
- Multiple labels per rule.
- After-clear, fixed, and no-return timeout modes.
- Optional return preset.
- Extend-on-activity behavior.
- Per-target priority and conflict handling.
- Preset test button.
- Persistent rule storage.
- Home Assistant Ingress support.
- Automatic Home Assistant MQTT service discovery.
- Automatic discovery of installed Frigate Home Assistant Apps.
- Manual Frigate/MQTT configuration for external systems.
- Standalone Docker/Compose deployment.
- Apache-2.0 licensed.

## Home Assistant App

Home Assistant App is the recommended installation for Home Assistant OS and other Supervisor/App-capable installations.

The repository follows the current Home Assistant App repository format. Add this repository to the Home Assistant App Store, install **FrigateSpotter**, then start it and select **Open Web UI**.

Default Home Assistant settings are intentionally simple:

```yaml
frigate_url: auto
mqtt_source: supervisor
frigate_topic_prefix: frigate
```

With these defaults, FrigateSpotter:
1. asks Supervisor for the installed Frigate App and uses its internal API;
2. asks Supervisor for the MQTT service connection details;
3. uses Home Assistant Ingress for the UI;
4. stores routing rules in the App's persistent `/data` volume.

If Frigate or MQTT is external, switch to manual configuration in the App configuration screen.

App-specific documentation is in [`homeassistant/DOCS.md`](homeassistant/DOCS.md).

## Standalone Docker

For systems without Home Assistant Apps, use Docker Compose:

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

Then:

```bash
docker compose up -d --build
```

Open `http://<host>:8080`.

## Example rule

| Setting | Example |
| --- | --- |
| Source camera | `spotter_cam` |
| Zone | `entry_zone` |
| Objects | `dog`, `person` |
| PTZ camera | `ptz_cam` |
| Target preset | `entry` |
| Timeout mode | After zone clears |
| Timeout | `15` seconds |
| Return preset | `home` |

When the last matching object leaves the zone, the timeout begins. If matching activity returns before it expires, the pending return is cancelled.

## Frigate requirements

FrigateSpotter only receives labels that Frigate is already tracking. For example:

```yaml
objects:
  track:
    - person
    - dog
```

For PTZ targets, ONVIF must be configured in Frigate and the target camera must expose presets through Frigate.

## Standalone environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `FRIGATE_URL` | `http://frigate:5000` | Frigate base URL without `/api`. |
| `FRIGATE_API_TOKEN` | empty | Optional Frigate bearer token. |
| `FRIGATE_TOPIC_PREFIX` | `frigate` | Frigate MQTT topic prefix. |
| `MQTT_HOST` | `mqtt` | MQTT broker hostname/IP. |
| `MQTT_PORT` | `1883` | MQTT broker port. |
| `MQTT_USERNAME` | empty | MQTT username. |
| `MQTT_PASSWORD` | empty | MQTT password. |
| `MQTT_TLS` | `false` | Enable MQTT TLS. |
| `MQTT_CA_CERT` | empty | Optional MQTT CA certificate path. |
| `MQTT_CLIENT_ID` | `frigatespotter` | MQTT client ID. |
| `DATA_DIR` | `./data` | Persistent data directory outside the HA App. |
| `SPOTTER_API_TOKEN` | empty | Optional bearer token for standalone web/API access. |
| `LOG_LEVEL` | `INFO` | Logging level. |

## Security

The Home Assistant App uses Ingress and does not expose its web port by default. Standalone deployments should keep Frigate's port 5000 and the FrigateSpotter web interface on trusted networks or add appropriate authentication/reverse-proxy controls.

Do not commit credentials, private camera URLs, internal addresses, snapshots, or installation-specific names to the repository.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
