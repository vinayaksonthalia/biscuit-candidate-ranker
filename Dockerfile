FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY rank.py .
COPY validate_submission.py .

# Default command matches the spec's reproduce command exactly
CMD ["python", "rank.py", "--candidates", "./candidates.jsonl", "--out", "./submission.csv"]
