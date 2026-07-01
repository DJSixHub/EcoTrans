from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from app.core.security import decode_access_token
from app.services.auth import authenticate_user, create_access_token_for_user
from app.services.users import create_user, get_user_by_username
from app.schemas.auth import Token, UserCreate
from app.schemas.users import UserRead
from app.db.session import async_session

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload["sub"]
    user = await get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user


@router.post("/auth/register", response_model=UserRead)
async def register(user_create: UserCreate):
    if user_create.role not in {"analyst", "inspector", "admin"}:
        raise HTTPException(status_code=400, detail="Role debe ser analyst, inspector o admin")
    existing = await get_user_by_username(user_create.username)
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    user = await create_user(user_create.username, user_create.email, user_create.password, user_create.role)
    return user


@router.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = await create_access_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserRead)
async def me(current_user=Depends(get_current_user)):
    return current_user
