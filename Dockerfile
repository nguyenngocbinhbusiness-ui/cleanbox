# CleanBox Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies (exclude windows-only if needed, or allow fail)
# For Linux container, we skip windows-specific modules
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy source
COPY src/ .
COPY project/ . 2>/dev/null || true

# Entry point
CMD ["python", "src/main.py"]
