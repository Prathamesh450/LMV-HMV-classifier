# Run development stack via docker compose (builds images as needed)
# Builds AI with CPU requirements by default
docker compose build --build-arg REQ=requirements-cpu.txt ai_worker
docker compose up --build
