import logging
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import time
from app import crud, models, schemas, auth, utils
from app.database import engine, get_db
from datetime import timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("user_service")

# Создаем таблицы в БД
try:
    logger.info("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")
    raise

app = FastAPI(title="User Service API")

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request started: {request.method} {request.url}")

    # Обработка запроса
    response = await call_next(request)

    # Логирование ответа
    process_time = time.time() - start_time
    logger.info(f"Request completed: {request.method} {request.url} - Status: {response.status_code} - Took: {process_time:.4f}s")

    return response

@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registering new user: {user.username}")
    try:
        db_user = crud.create_user(db=db, user=user)
        logger.info(f"User {user.username} registered successfully with ID: {db_user.id}")
        return db_user
    except HTTPException as he:
        logger.warning(f"Registration failed for {user.username}: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )

@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Login attempt for user: {form_data.username}")
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Successful login for user: {form_data.username}")
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    logger.info(f"Fetching profile for user: {current_user.username}")
    return current_user

@app.put("/profile", response_model=schemas.UserResponse)
def update_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Updating profile for user: {current_user.username}")
    return crud.update_user(db=db, user_id=current_user.id, user_update=user_update)
