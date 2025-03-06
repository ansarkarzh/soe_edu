from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
from jose import JWTError, jwt
from app.utils import SECRET_KEY, ALGORITHM
import logging

logger = logging.getLogger("user_service.auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug("Decoding JWT token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token missing username claim")
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError as e:
        logger.warning(f"JWT error: {e}")
        raise credentials_exception

    logger.debug(f"Looking up user: {token_data.username}")
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        logger.warning(f"User not found: {token_data.username}")
        raise credentials_exception

    logger.info(f"User authenticated: {user.username}")
    return user
