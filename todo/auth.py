from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.orm import Session
import models
from database import db_dependency
from schemas import CreateUserRequest, Token

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY = "5fcbb1937ee77eae9d71ccf2836ba41ab35089f3cb404b85e789dd1d5d213ad0"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@router.post("/", status_code=status.HTTP_201_CREATED)
def register_user(db: db_dependency,
                  create_user_request: CreateUserRequest):
    try:
        create_user_model = models.Users(
            username=create_user_request.username,
            hashed_password=pwd_context.hash(create_user_request.password),
        )
        db.add(create_user_model)
        db.commit()
    except Exception as e:
        raise e


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials")
        token = create_access_token(user.username, user.id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise e

def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        raise e


def get_password_hash(password):
    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise e


def authenticate_user(db: Session, username: str, password: str):
    try:
        user = db.query(models.Users).filter(models.Users.username == username).first()
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        print(user)
        return user
    except Exception as e:
        raise e


def create_access_token(username: str, user_id: str, expires_delta: timedelta):
    try:
        to_encode = {"sub": username, "id": user_id}
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise e


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials")
        return {"username": username, "id": user_id}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials")

