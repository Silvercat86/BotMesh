FROM python:3.12-slim

WORKDIR /app

# системные зависимости (если не нужны — можно удалить)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# код
COPY . .

# запуск
CMD ["python", "main.py"]
