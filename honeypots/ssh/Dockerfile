FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir --retries 5 --timeout 120 \
    asyncssh==2.23.1 \
    aiohttp==3.14.1 \
    httpx==0.28.1 \
    redis==8.0.1 \
    python-dotenv==1.2.2
COPY . .
EXPOSE 2223
CMD ["python", "ssh_honeypot.py"]