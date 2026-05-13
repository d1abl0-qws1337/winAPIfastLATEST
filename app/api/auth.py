from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database import get_db
from app.services.auth_service import AuthService
from app.security import get_current_user
from app.exceptions import FinTechException, AuthenticationError

router = APIRouter()


class RegisterRequest(BaseModel):
    """User registration request schema."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class RegisterResponse(BaseModel):
    """User registration response schema."""
    access_token: str
    token_type: str
    user_id: int
    email: str
    username: str
    account_number: str


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str
    user_id: int
    email: str
    username: str


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    Creates a new user account with an associated financial account.
    """
    try:
        auth_service = AuthService(session)
        result = await auth_service.register_user(
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name
        )
        await session.commit()
        return result
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access token.

    Use email as username for OAuth2 compatible login.
    """
    try:
        auth_service = AuthService(session)
        result = await auth_service.authenticate_user(
            email=form_data.username,
            password=form_data.password
        )
        return result
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires valid JWT token.
    """
    return current_user
