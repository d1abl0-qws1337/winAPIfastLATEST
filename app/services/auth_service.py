from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from datetime import datetime, timedelta
from decimal import Decimal
from jose import jwt
from typing import Optional
from app.repositories import UserRepository, AccountRepository
from app.config import settings
from app.exceptions import AuthenticationError, AuthorizationError, AccountNotFoundError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.account_repo = AccountRepository(session)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    async def authenticate_user(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email_with_password(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not self.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "username": user.username
        }

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None
    ) -> dict:
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise AuthenticationError("Email already registered")

        existing_username = await self.user_repo.get_by_username(username)
        if existing_username:
            raise AuthenticationError("Username already taken")

        hashed_password = self.hash_password(password)
        user = await self.user_repo.create_user(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name
        )

        account_number = f"ACC{user.id:08d}"
        await self.account_repo.create_account(
            user_id=user.id,
            account_number=account_number,
            currency="USD",
            initial_balance=Decimal("0.0000")
        )

        access_token = self.create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "account_number": account_number
        }

    async def get_current_user(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")

            if email is None or user_id is None:
                raise AuthorizationError("Invalid token payload")

            user = await self.user_repo.get_by_email(email)
            if not user or not user.is_active:
                raise AuthorizationError("User not found or inactive")

            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name
            }
        except jwt.JWTError:
            raise AuthorizationError("Could not validate credentials")

    async def get_user_accounts(self, user_id: int) -> list[dict]:
        accounts = await self.account_repo.get_by_user_id(user_id)

        return [
            {
                "id": a.id,
                "account_number": a.account_number,
                "balance": float(a.balance),
                "currency": a.currency,
                "is_active": a.is_active
            }
            for a in accounts
        ]


class AccountService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_repo = AccountRepository(session)

    async def get_account(self, account_id: int, user_id: int) -> dict:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFoundError(str(account_id))

        if account.user_id != user_id:
            raise AuthorizationError("Not authorized to access this account")

        return {
            "id": account.id,
            "account_number": account.account_number,
            "balance": float(account.balance),
            "currency": account.currency,
            "is_active": account.is_active
        }

    async def get_balance(self, account_id: int, user_id: int) -> dict:
        account = await self.get_account(account_id, user_id)
        return {"balance": account["balance"], "currency": account["currency"]}
