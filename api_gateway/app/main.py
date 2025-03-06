from fastapi import FastAPI, Request, HTTPException, status
import httpx
import logging
import sys
import time
from fastapi.responses import JSONResponse
from app.schemas import UserCreate, UserUpdate, LoginForm

# Более явная настройка логирования
# Создаем обработчик для вывода в консоль
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Настройка корневого логгера
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)

# Настройка логгера API Gateway
logger = logging.getLogger("api_gateway")
logger.setLevel(logging.DEBUG)  # Устанавливаем DEBUG для максимальной детализации
logger.addHandler(handler)
logger.propagate = False  # Отключаем передачу логов вышестоящим логгерам

# Проверочные сообщения
print("API Gateway startup - print statement")
logger.critical("API Gateway startup - critical log")

app = FastAPI(title="API Gateway")

# Для локального запуска
USER_SERVICE_URL = "http://localhost:8000"

# Обработчик глобальных исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
    )

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        start_time = time.time()
        path = request.url.path
        print(f"Request received: {request.method} {path}")
        logger.info(f"Request started: {request.method} {path}")

        # Обработка запроса
        response = await call_next(request)

        # Логирование ответа
        process_time = time.time() - start_time
        print(f"Response sent: {response.status_code} for {request.method} {path}")
        logger.info(f"Request completed: {request.method} {path} - Status: {response.status_code} - Took: {process_time:.4f}s")

        return response
    except Exception as e:
        logger.error(f"Error in middleware: {e}", exc_info=True)
        print(f"Middleware error: {e}")
        raise

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    print("Root endpoint called via print")
    return {"message": "API Gateway is running"}

@app.post("/register")
async def register_user(user: UserCreate):
    logger.critical("IN REGISTER")
    logger.info(f"Registering user: {user.username}")
    print(f"Registering user (print): {user.username}")
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Sending request to User Service: POST {USER_SERVICE_URL}/register")
            response = await client.post(f"{USER_SERVICE_URL}/register", json=user.dict())
            logger.info(f"Response from User Service: Status {response.status_code}")
            return response.json()
    except Exception as e:
        logger.error(f"Error calling User Service: {e}", exc_info=True)
        print(f"Error (print): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with User Service: {str(e)}"
        )

@app.post("/login")
async def login(form_data: LoginForm):
    logger.info(f"Login attempt for user: {form_data.username}")
    try:
        async with httpx.AsyncClient() as client:
            oauth_form = {
                "username": form_data.username,
                "password": form_data.password
            }
            logger.info(f"Sending login request to User Service")
            response = await client.post(
                f"{USER_SERVICE_URL}/login",
                data=oauth_form,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            logger.info(f"Response from User Service: Status {response.status_code}")
            return response.json()
    except Exception as e:
        logger.error(f"Error calling User Service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with User Service: {str(e)}"
        )

@app.get("/profile")
async def get_profile(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        logger.warning("Unauthorized request to /profile - token missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    logger.info("Fetching user profile")
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Sending request to User Service: GET {USER_SERVICE_URL}/profile")
            response = await client.get(
                f"{USER_SERVICE_URL}/profile",
                headers={"Authorization": token}
            )
            logger.info(f"Response from User Service: Status {response.status_code}")
            return response.json()
    except Exception as e:
        logger.error(f"Error calling User Service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with User Service: {str(e)}"
        )

@app.put("/profile")
async def update_profile(user_update: UserUpdate, request: Request):
    token = request.headers.get("Authorization")
    if not token:
        logger.warning("Unauthorized request to update profile - token missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    logger.info("Updating user profile")
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Sending request to User Service: PUT {USER_SERVICE_URL}/profile")
            response = await client.put(
                f"{USER_SERVICE_URL}/profile",
                json=user_update.dict(exclude_unset=True),
                headers={"Authorization": token}
            )
            logger.info(f"Response from User Service: Status {response.status_code}")
            return response.json()
    except Exception as e:
        logger.error(f"Error calling User Service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with User Service: {str(e)}"
        )
