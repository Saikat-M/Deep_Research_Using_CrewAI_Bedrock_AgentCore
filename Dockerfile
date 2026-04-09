# Use uv package manager, ARM64 compatible architecture
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.11-bookworm-slim 

WORKDIR /app

# Install build tools for compiling dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt
COPY requirements.txt .

# Install heavy packages first (separate layer)
RUN uv pip install --system --no-cache boto3 crewai-tools streamlit

# Install remaining dependencies
RUN uv pip install --system --no-cache -r requirements.txt

# Copy app source code and pyproject.toml
COPY src/ ./src/
COPY pyproject.toml .

# Expose port
EXPOSE 8080

# Startup command - Runs the app
CMD ["python", "src/deep_research/crew.py"]
