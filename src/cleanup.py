import json
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_database():
    """Очистка базы данных от ошибок"""
    try:
        # Путь к файлу базы данных
        db_path = Path('data/posts.json')
        
        if not db_path.exists():
            logger.info("Database file not found, creating new one")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(db_path, 'w') as f:
                json.dump({"downloaded": [], "excluded": []}, f, indent=2)
            return
        
        # Читаем текущую базу данных
        with open(db_path, 'r') as f:
            data = json.load(f)
        
        # Сохраняем успешно загруженные посты
        downloaded = data.get("downloaded", [])
        
        # Создаем новую базу данных только с успешными загрузками
        new_data = {
            "downloaded": downloaded,
            "excluded": []
        }
        
        # Сохраняем обновленную базу данных
        with open(db_path, 'w') as f:
            json.dump(new_data, f, indent=2)
            
        logger.info(f"Database cleaned. Kept {len(downloaded)} downloaded posts")
        
    except Exception as e:
        logger.error(f"Error cleaning database: {str(e)}")
        # В случае ошибки создаем новую базу данных
        with open(db_path, 'w') as f:
            json.dump({"downloaded": [], "excluded": []}, f, indent=2)

if __name__ == '__main__':
    cleanup_database() 