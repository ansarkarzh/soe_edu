from sqlalchemy.orm import Session
from app import models, schemas, utils
from fastapi import HTTPException, status
import logging

logger = logging.getLogger("user_service.crud")

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Проверка на существующий username
    if get_user_by_username(db, user.username):
        logger.warning(f"Username already registered: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # Проверка на существующий email
    if get_user_by_email(db, user.email):
        logger.warning(f"Email already registered: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    logger.info(f"Creating new user: {user.username}")
    hashed_password = utils.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created successfully: {user.username}")
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    logger.info(f"Updating user with ID: {user_id}")
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        logger.warning(f"User not found with ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_update.dict(exclude_unset=True)

    # Проверка на уникальность email при обновлении
    if "email" in update_data and update_data["email"] != db_user.email:
        if get_user_by_email(db, update_data["email"]):
            logger.warning(f"Email already registered: {update_data['email']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    for key, value in update_data.items():
        logger.debug(f"Updating user field: {key}")
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    logger.info(f"User updated successfully: {db_user.username}")
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        logger.warning(f"User not found: {username}")
        return False
    if not utils.verify_password(password, user.password_hash):
        logger.warning(f"Invalid password for user: {username}")
        return False
    logger.info(f"User authenticated successfully: {username}")
    return user
