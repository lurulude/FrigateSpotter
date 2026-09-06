# Architecture

FrigateSpotter intentionally sits beside Frigate rather than modifying it.

## Data flow

1. The web/API service calls Frigate `GET /api/config` to discover cameras, zones, and tracked labels.
2. It calls `GET /api/<camera>/ptz/info` for each camera to discover ONVIF PTZ capability and preset names.
3. The MQTT bridge subscribes to `<topic_prefix>/events`.
4. The rule engine evaluates each tracked-object event using camera, label, and `current_zones`.
5. A matching rule publishes `preset_<preset>` to `<topic_prefix>/<ptz_camera>/ptz`.
6. The rule engine manages per-target priority, active object IDs, fixed/clear timeouts, and optional return presets.

## Timeout modes

- `after_clear`: wait until all matching tracked objects have left the zone, then start the timeout.
- `fixed`: start the timeout as soon as the rule triggers. `extend_on_activity` can restart that timer on updates.
- `never`: leave the camera at the target preset until another rule moves it.

## Conflict handling

Only one rule owns a target PTZ camera at a time. A higher-priority active rule can preempt a lower-priority rule. For equal priorities, the most recently triggered rule wins. When a rule releases the PTZ, another active rule for the same target is selected before the camera is returned home.

## Persistence

Rules are stored as JSON under `DATA_DIR` (default `/data/rules.json`). Camera credentials are not persisted by FrigateSpotter.

## Trust boundaries

FrigateSpotter needs network access to the Frigate HTTP API and MQTT broker. It never needs direct camera credentials when Frigate provides ONVIF PTZ control. Deploy it on a trusted network, use MQTT authentication/TLS where available, and set `SPOTTER_API_TOKEN` if the web interface is exposed beyond a trusted LAN.
