FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir --retries 5 --timeout 120 \
    aiohttp==3.14.1 \
    python-dotenv==1.2.2
COPY . .
EXPOSE 2222 8080 5433 8545 9090
CMD ["python", "proxy.py"]