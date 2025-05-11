import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='data/posts.json'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_data()
        
    def _load_data(self):
        """Загрузка данных из JSON файла"""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                self.data = {
                    "downloaded": [],
                    "excluded": []
                }
                self._save_data()
        except json.JSONDecodeError as e:
            logger.error(f"Error loading database: {str(e)}")
            self.data = {
                "downloaded": [],
                "excluded": []
            }
            self._save_data()
        except Exception as e:
            logger.error(f"Unexpected error loading database: {str(e)}")
            self.data = {
                "downloaded": [],
                "excluded": []
            }
            self._save_data()
            
    def _save_data(self):
        """Сохранение данных в JSON файл"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving database: {str(e)}")
            
    def is_post_downloaded(self, post_id):
        """Проверка, был ли пост уже скачан"""
        return any(post['id'] == post_id for post in self.data['downloaded'])
        
    def is_post_excluded(self, post_id):
        """Проверка, находится ли пост в списке исключений"""
        return any(post['id'] == post_id for post in self.data['excluded'])
        
    def add_downloaded_post(self, post_id, title, url, file_path):
        """Добавление поста в список скачанных"""
        if not self.is_post_downloaded(post_id):
            self.data['downloaded'].append({
                'id': post_id,
                'title': title,
                'url': url,
                'file_path': file_path,
                'timestamp': datetime.now().isoformat()
            })
            self._save_data()
            
    def add_excluded_post(self, post_id, title, reason):
        """Добавление поста в список исключений"""
        if not self.is_post_excluded(post_id):
            self.data['excluded'].append({
                'id': post_id,
                'title': title,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
            self._save_data()
            
    def get_downloaded_posts(self):
        """Получение списка скачанных постов"""
        return self.data['downloaded']
        
    def get_excluded_posts(self):
        """Получение списка исключенных постов"""
        return self.data['excluded']

def init_db():
    """Инициализирует базу данных"""
    db_path = Path(os.path.join(os.getenv('STORAGE_PATH', 'data'), 'posts.json'))
    logger.info(f"Initializing database at {db_path}")
    return Database(db_path) 