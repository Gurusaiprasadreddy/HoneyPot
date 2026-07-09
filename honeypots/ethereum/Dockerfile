FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt
COPY . .
EXPOSE 8545
CMD ["uvicorn", "eth_honeypot:app", "--host", "0.0.0.0", "--port", "8545"]
