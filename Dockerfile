# xcela (018): container image for shape-agnostic deployment (Docker/compose/k8s/PaaS).
# Config via environment or a mounted .env (harness/runtime_env.py: env always wins).
# STATE LIVES ON DISK: mount volumes for output/ (runs), brands/ (uploaded assets), and
# answer_keys/ (the onboarding wizard WRITES brand keys there at runtime) or they vanish
# with the container. See docker-compose.yml for the canonical wiring.
FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 \
    XCELA_BIND=0.0.0.0 XCELA_PORT=8765
# 0.0.0.0 binds inside the container only; publish thoughtfully (compose maps to localhost;
# put your TLS proxy or gateway in front for anything public).
EXPOSE 8765

CMD ["python", "frontend/server.py"]
