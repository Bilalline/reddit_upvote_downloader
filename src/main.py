import os
import logging
import praw
import requests
import telebot
from dotenv import load_dotenv
from tqdm import tqdm
from database import Database
from datetime import datetime
import re
from pathlib import Path

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация Reddit API
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='script',
    username=os.getenv('REDDIT_USERNAME'),
    password=os.getenv('REDDIT_PASSWORD')
)

# Инициализация Telegram бота
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
chat_id = os.getenv('TELEGRAM_CHAT_ID')

# Создание директорий
storage_path = Path(os.getenv('STORAGE_PATH', 'data'))
storage_path.mkdir(parents=True, exist_ok=True)

def download_file(url, file_path):
    """Скачивает файл с отображением прогресса"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    
    with open(file_path, 'wb') as f, tqdm(
        desc=file_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(block_size):
            size = f.write(data)
            pbar.update(size)

def process_video_post(post, db: Database):
    """Обрабатывает видео пост"""
    try:
        # Получаем URL видео и аудио
        video_url = post.media['reddit_video']['fallback_url']
        audio_url = video_url.split('DASH_')[0] + 'audio'
        
        # Создаем временные файлы
        temp_video = storage_path / f'temp_video_{post.id}.mp4'
        temp_audio = storage_path / f'temp_audio_{post.id}.mp4'
        final_video = storage_path / f'video_{post.id}.mp4'
        
        # Скачиваем видео
        download_file(video_url, temp_video)
        
        # Пытаемся скачать аудио
        try:
            download_file(audio_url, temp_audio)
            # Объединяем видео и аудио
            os.system(f'ffmpeg -i {temp_video} -i {temp_audio} -c:v copy -c:a aac {final_video}')
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.info(f'No audio for post {post.id}')
                final_video = temp_video
            else:
                raise
        
        # Отправляем файл в Telegram
        with open(final_video, 'rb') as video_file:
            if os.path.getsize(final_video) <= int(os.getenv('MAX_FILE_SIZE', 52428800)):
                bot.send_video(chat_id, video_file, caption=post.title)
            else:
                bot.send_document(chat_id, video_file, caption=post.title)
        
        # Сохраняем информацию в базу данных
        db.add_downloaded_post(post.id, post.title, video_url, str(final_video))
        
        # Очищаем временные файлы
        temp_video.unlink(missing_ok=True)
        temp_audio.unlink(missing_ok=True)
        if os.getenv('SAVE_FILES', 'true').lower() != 'true':
            final_video.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f'Error processing video post {post.id}: {str(e)}')
        db.add_excluded_post(post.id, post.title, str(e))

def process_gif_post(post, db: Database):
    """Обрабатывает GIF пост"""
    try:
        # Получаем URL GIF
        gif_url = post.url
        
        # Скачиваем GIF
        gif_path = storage_path / f'gif_{post.id}.gif'
        download_file(gif_url, gif_path)
        
        # Отправляем GIF в Telegram
        with open(gif_path, 'rb') as gif_file:
            bot.send_animation(chat_id, gif_file, caption=post.title)
        
        # Сохраняем информацию в базу данных
        db.add_downloaded_post(post.id, post.title, gif_url, str(gif_path))
        
        # Удаляем файл если не нужно сохранять
        if os.getenv('SAVE_FILES', 'true').lower() != 'true':
            gif_path.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f'Error processing GIF post {post.id}: {str(e)}')
        db.add_excluded_post(post.id, post.title, str(e))

def get_redgifs_token():
    """Получает токен для API RedGIFs"""
    try:
        # Формируем URL для получения токена
        token_url = 'https://api.redgifs.com/v2/auth/temporary'
        
        # Добавляем заголовки для запроса
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Origin': 'https://www.redgifs.com',
            'Referer': 'https://www.redgifs.com/'
        }
        
        # Получаем токен
        response = requests.get(token_url, headers=headers)
        response.raise_for_status()
        token_data = response.json()
        
        return token_data.get('token')
    except Exception as e:
        logger.error(f'Error getting RedGIFs token: {str(e)}')
        return None

def process_redgifs_post(post, db: Database):
    """Обрабатывает видео пост с RedGIFs"""
    try:
        # Получаем URL видео из iframe
        iframe_html = post.media['oembed']['html']
        video_id = iframe_html.split('/ifr/')[1].split('"')[0]
        
        # Получаем токен для API
        token = get_redgifs_token()
        if not token:
            raise Exception("Failed to get RedGIFs token")
        
        # Формируем URL для API RedGIFs
        api_url = f'https://api.redgifs.com/v2/gifs/{video_id}'
        
        # Добавляем заголовки для API с аутентификацией
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Origin': 'https://www.redgifs.com',
            'Referer': 'https://www.redgifs.com/',
            'Authorization': f'Bearer {token}'
        }
        
        try:
            # Получаем информацию о видео через API
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            video_info = response.json()
            
            # Получаем URL видео
            video_url = video_info['gif']['urls']['hd']
            
            # Скачиваем видео
            video_path = storage_path / f'video_{post.id}.mp4'
            download_file(video_url, video_path)
            
            # Отправляем файл в Telegram
            with open(video_path, 'rb') as video_file:
                if os.path.getsize(video_path) <= int(os.getenv('MAX_FILE_SIZE', 52428800)):
                    bot.send_video(chat_id, video_file, caption=post.title)
                else:
                    bot.send_document(chat_id, video_file, caption=post.title)
            
            # Сохраняем информацию в базу данных
            db.add_downloaded_post(post.id, post.title, video_url, str(video_path))
            
            # Удаляем файл если не нужно сохранять
            if os.getenv('SAVE_FILES', 'true').lower() != 'true':
                video_path.unlink(missing_ok=True)
                
        except requests.exceptions.RequestException as e:
            logger.error(f'API request failed for RedGIFs post {post.id}: {str(e)}')
            db.add_excluded_post(post.id, post.title, str(e))
            return
            
    except Exception as e:
        logger.error(f'Error processing RedGIFs post {post.id}: {str(e)}')
        db.add_excluded_post(post.id, post.title, str(e))

def main():
    """Основная функция"""
    logger.info('Starting Reddit to Telegram bot')
    
    try:
        # Инициализация базы данных
        db = Database()
        
        while True:
            try:
                # Получаем понравившиеся посты
                saved_posts = reddit.user.me().upvoted(limit=None)
                
                for post in saved_posts:
                    try:
                        # Проверяем, не был ли пост уже обработан или исключен
                        if db.is_post_downloaded(post.id):
                            logger.info(f'Post {post.id} already processed, skipping')
                            continue
                            
                        if db.is_post_excluded(post.id):
                            logger.info(f'Post {post.id} is in excluded list, skipping')
                            continue
                        
                        # Логируем подробную информацию о посте для отладки
                        logger.info(f'Processing post {post.id}:')
                        logger.info(f'  Title: {post.title}')
                        logger.info(f'  URL: {post.url}')
                        logger.info(f'  Domain: {post.domain}')
                        logger.info(f'  Is video: {hasattr(post, "is_video") and post.is_video}')
                        logger.info(f'  Is GIF: {post.url.endswith(".gif") or "gifv" in post.url}')
                        logger.info(f'  Post hint: {getattr(post, "post_hint", "None")}')
                        logger.info(f'  Media: {getattr(post, "media", "None")}')
                        
                        # Определяем тип поста и обрабатываем соответственно
                        if hasattr(post, 'is_video') and post.is_video:
                            process_video_post(post, db)
                        elif post.url.endswith('.gif') or 'gifv' in post.url:
                            process_gif_post(post, db)
                        elif post.domain in ['redgifs.com', 'v3.redgifs.com'] and getattr(post, 'post_hint', '') == 'rich:video':
                            process_redgifs_post(post, db)
                        else:
                            logger.info(f'Skipping unsupported post type: {post.id}')
                            db.add_excluded_post(post.id, post.title, "Unsupported post type")
                    except Exception as e:
                        logger.error(f'Error processing post {post.id}: {str(e)}')
                        db.add_excluded_post(post.id, post.title, str(e))
                        continue
                
                # Ждем перед следующей итерацией
                time.sleep(60)  # Пауза в 1 минуту между итерациями
                
            except Exception as e:
                logger.error(f'Error in main loop iteration: {str(e)}')
                time.sleep(60)  # Пауза перед следующей попыткой
                
    except Exception as e:
        logger.error(f'Error in main loop: {str(e)}')
        raise

if __name__ == '__main__':
    main() 
