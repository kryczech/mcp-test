FROM python:3.11-slim as base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates && rm -rf /var/lib/apt/lists/*

FROM base as builder
WORKDIR /app
COPY pyproject.toml /app/
# Install poetry, try to export requirements.txt from pyproject. If export fails (no lockfile or network issues),
# fall back to a minimal known-good requirements.txt so the image can still be built for development.
RUN pip install --upgrade pip poetry \
 && poetry export -f requirements.txt --without-hashes -o requirements.txt || \
	 (printf "fastapi==0.101.0\nuvicorn[standard]==0.22.0\nhttpx==0.24.0\npydantic==1.10.12\n" > requirements.txt) \
 && pip install -r requirements.txt

FROM base
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ /app/
ENV PYTHONPATH=/app
EXPOSE 8765
# Use python -m uvicorn instead of the uvicorn console script so the container
# doesn't depend on console entrypoints being present in PATH. This works
# reliably when packages are installed into site-packages in the image.
CMD ["python", "-m", "uvicorn", "main:APP", "--host", "0.0.0.0", "--port", "8765"]
