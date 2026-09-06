# FrigateSpotter

FrigateSpotter is a Home Assistant App that routes Frigate object detections from any camera or zone to PTZ presets on any PTZ-capable camera discovered by Frigate.

Use **Open Web UI** after the App starts. Home Assistant Ingress handles authentication and keeps the FrigateSpotter UI inside Home Assistant.

Typical route:

```text
source camera / zone / object labels
                ↓
PTZ camera / target preset
                ↓
timeout or zone clear
                ↓
optional return preset
```

See **Documentation** in the App page for configuration details.
