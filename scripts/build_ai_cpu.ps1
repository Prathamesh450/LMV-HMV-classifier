# Build AI Docker image using CPU-optimized requirements
param(
    [string]$ImageName = "lmv_ai"
)

docker build --build-arg REQ=requirements-cpu.txt -t $ImageName ./ai
