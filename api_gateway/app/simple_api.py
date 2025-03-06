from fastapi import FastAPI
import logging
import sys

# Настройка вывода логов в консоль
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Вывод в консоль при старте
print("======= STARTING SIMPLE API =======")

app = FastAPI()

@app.get("/")
async def root():
    print("Root endpoint called!")
    logger.info("Root endpoint called via logging")
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    print("Health check endpoint called!")
    return {"status": "ok"}
