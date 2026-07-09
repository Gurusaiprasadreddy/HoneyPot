FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt
COPY . .
EXPOSE 9091
CMD ["uvicorn", "cicd_honeypot:app", "--host", "0.0.0.0", "--port", "9091"]