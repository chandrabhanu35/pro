FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code
COPY agents/ /app/agents/

# Expose dashboard port
EXPOSE 5050

# Default: run the main CLI
ENTRYPOINT ["python", "-m", "agents.clawbot.main"]
