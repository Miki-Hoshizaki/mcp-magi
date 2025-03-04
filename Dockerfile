FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

ENV PYTHONPATH=/app
ENV MAGI_URL=ws://127.0.0.1:8000/ws

CMD ["python", "src/server.py", "--host", "0.0.0.0", "--port", "8080"] 