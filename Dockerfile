# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

ARG BUILD_VERSION=0.2.0
ARG BUILD_ARCH=amd64

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

LABEL io.hass.type="app" \
      io.hass.name="FrigateSpotter" \
      io.hass.version="${BUILD_VERSION}" \
      io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.title="FrigateSpotter" \
      org.opencontainers.image.description="Route Frigate detections to PTZ camera presets." \
      org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app
RUN addgroup --system spotter \
    && adduser --system --ingroup spotter spotter \
    && mkdir /data \
    && chown spotter:spotter /data

COPY pyproject.toml README.md LICENSE NOTICE ./
COPY frigatespotter ./frigatespotter
RUN pip install --no-cache-dir .

USER spotter
VOLUME ["/data"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3)"

CMD ["python", "-m", "frigatespotter"]
