from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
import getpass

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("user_service.database")

# Для macOS используем имя текущего пользователя
CURRENT_USER = getpass.getuser()
POSTGRES_USER = os.getenv("POSTGRES_USER", CURRENT_USER)
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")  # пустой пароль для локального пользователя
POSTGRES_DB = os.getenv("POSTGRES_DB", "userdb")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Формирование строки подключения
if POSTGRES_PASSWORD:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

logger.info(f"Connecting to database: {SQLALCHEMY_DATABASE_URL}")

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
