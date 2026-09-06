# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data
WORKDIR /app
RUN addgroup --system spotter && adduser --system --ingroup spotter spotter && mkdir /data && chown spotter:spotter /data
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY frigatespotter ./frigatespotter
RUN pip install --no-cache-dir .
USER spotter
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3)"
CMD ["python", "-m", "frigatespotter"]
