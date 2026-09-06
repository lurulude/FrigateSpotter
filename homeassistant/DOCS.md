# FrigateSpotter Home Assistant App

## What it does

FrigateSpotter listens to Frigate tracked-object events over MQTT. Rules can route detections from any Frigate camera or zone to any ONVIF PTZ preset exposed by Frigate.

The App supports:
- all Frigate cameras and zones
- multiple object labels per rule
- target and return presets
- after-clear, fixed, or no-return timeout modes
- activity-based timeout extension
- per-PTZ priorities
- preset test commands
- persistent rules stored in `/data`
- Home Assistant Ingress

## Requirements

- Home Assistant OS or another Supervisor/App-capable Home Assistant installation
- Frigate with MQTT enabled
- MQTT available either through a Home Assistant MQTT service or a manually configured broker
- ONVIF PTZ configured in Frigate for cameras that should receive preset commands

## Configuration

### Frigate URL

`frigate_url: auto` is recommended when Frigate is installed as a Home Assistant App. FrigateSpotter asks Supervisor for installed Apps, selects a Frigate App, and uses its internal port 5000.

For Frigate on another host, set a full URL such as:

```yaml
frigate_url: http://192.0.2.20:8971
```

If that Frigate endpoint requires a bearer token, set `frigate_api_token`.

### MQTT

With:

```yaml
mqtt_source: supervisor
```

FrigateSpotter reads the MQTT host, port, username, password, and TLS state from Supervisor's MQTT service. This avoids copying broker credentials into the App configuration.

If the MQTT broker is external or is not published as a Supervisor MQTT service, select `manual` and provide the MQTT fields.

### Frigate topic prefix

The default is:

```yaml
frigate_topic_prefix: frigate
```

Only change it if the Frigate MQTT `topic_prefix` has been customized.

## First start

1. Install and start FrigateSpotter.
2. Click **Open Web UI**.
3. Confirm MQTT shows connected.
4. Click **Refresh discovery**.
5. Choose a source camera and optional zone.
6. Choose object labels.
7. Choose a PTZ camera and target preset.
8. Choose timeout behavior and an optional return preset.
9. Use **Test** to confirm the preset moves correctly.
10. Save the rule.

## Ingress and security

The App's host port is disabled by default. The UI is intended to be used through Home Assistant Ingress. FrigateSpotter restricts normal UI/API requests to the Home Assistant Ingress gateway while running as a Home Assistant App. The health endpoint remains available internally for the Supervisor watchdog.

Do not expose Frigate's unauthenticated port 5000 outside a trusted internal network.
