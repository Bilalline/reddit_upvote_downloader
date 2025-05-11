# Reddit to Telegram Bot

Бот для автоматического скачивания и отправки в Telegram постов с Reddit, которые вы отметили как понравившиеся.

## Возможности

- Скачивание видео с Reddit
- Скачивание GIF-анимаций
- Скачивание видео с RedGIFs
- Автоматическая отправка в Telegram
- Сохранение истории скачанных постов
- Поддержка аудио для видео с Reddit

## Требования

- Python 3.8+
- Docker и Docker Compose
- FFmpeg (для обработки видео)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/reddit-telegram-bot.git
cd reddit-telegram-bot
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

3. Заполните необходимые переменные окружения в файле `.env`:
```env
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Настройки
SAVE_FILES=true
MAX_FILE_SIZE=52428800
LOG_LEVEL=INFO
```

4. Запустите бота через Docker:
```bash
docker-compose up -d
```

## Структура проекта

```
reddit-telegram-bot/
├── src/
│   ├── main.py          # Основной код бота
│   ├── database.py      # Работа с базой данных
│   └── cleanup.py       # Скрипт очистки базы данных
├── data/                # Директория для хранения файлов
├── logs/                # Директория для логов
├── .env                 # Файл с переменными окружения
├── .env.example         # Пример файла с переменными окружения
├── .gitignore          # Исключения для Git
├── docker-compose.yml   # Конфигурация Docker Compose
├── Dockerfile          # Инструкции для сборки Docker образа
├── requirements.txt    # Зависимости Python
└── README.md           # Документация проекта
```

## Использование

1. Запустите бота:
```bash
docker-compose up -d
```

2. Проверьте логи:
```bash
docker-compose logs -f
```

3. Остановите бота:
```bash
docker-compose down
```

## Поддерживаемые типы постов

- Видео с Reddit (с поддержкой аудио)
- GIF-анимации
- Видео с RedGIFs

## Лицензия

MIT 
