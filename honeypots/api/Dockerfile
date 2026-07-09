FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir --retries 5 --timeout 120 \
    fastapi==0.138.0 \
    uvicorn==0.49.0 \
    aiohttp==3.14.1 \
    requests \
    python-dotenv==1.2.2
COPY . .
EXPOSE 8081
CMD ["uvicorn", "api_honeypot:app", "--host", "0.0.0.0", "--port", "8081"]