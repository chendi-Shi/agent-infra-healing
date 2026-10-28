FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask prometheus-client

# Copy app
COPY app.py .

EXPOSE 8080

CMD ["python", "app.py"]
