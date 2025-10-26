FROM python:3.10-slim

# Install system deps for OpenCV / easyocr (may need more depending on platform)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 libsm6 libxrender1 libxext6 libgl1-mesa-glx \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Allow choosing CPU requirements at build time via --build-arg REQ=requirements-cpu.txt
ARG REQ=requirements.txt
COPY ${REQ} ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5000
CMD ["python", "app.py"]
