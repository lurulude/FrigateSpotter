# Security Policy

FrigateSpotter interacts with camera systems and home-automation infrastructure, so security reports should be handled carefully.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for a vulnerability that could expose credentials, camera feeds, network access, or remote-control capabilities.

Use GitHub's private vulnerability reporting feature if it is enabled for this repository. If it is not available, contact the repository owner privately through an available GitHub contact method and provide enough information to reproduce and assess the issue.

Please include:

- A clear description of the vulnerability and impact.
- Affected FrigateSpotter version or commit.
- Relevant Frigate, Home Assistant, MQTT, ONVIF, or camera environment details.
- Reproduction steps or a proof of concept that does not expose third-party systems.
- Suggested mitigation, if known.

Never include real passwords, tokens, private camera URLs, public-facing IP addresses, or private video/snapshots unless explicitly requested through a secure channel.

## Supported versions

Until FrigateSpotter reaches its first stable release, security fixes will normally target the current development branch. A supported-version table will be added when stable releases exist.

## Security principles

The project should prefer least-privilege access, avoid logging secrets, validate untrusted input, and use established authentication and transport mechanisms offered by upstream systems rather than inventing custom security protocols.
