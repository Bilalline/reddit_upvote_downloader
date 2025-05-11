FROM python:3.11-slim

WORKDIR /app

# Установка необходимых системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY requirements.txt .
COPY src/ ./src/
COPY config/ ./config/

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Создание директорий и установка прав
RUN mkdir -p /app/data /app/logs && \
    chmod -R 777 /app/data /app/logs

# Установка переменных окружения по умолчанию
ENV PYTHONUNBUFFERED=1

# Запуск скрипта очистки и основного приложения
CMD ["sh", "-c", "python src/cleanup.py && python src/main.py"] 