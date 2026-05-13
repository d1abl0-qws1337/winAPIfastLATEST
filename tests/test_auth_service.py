import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth_service import AuthService, AccountService
from app.exceptions import AuthenticationError, AuthorizationError, AccountNotFoundError
from app.models import User, Account


class TestAuthService:
    """Unit tests for AuthService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "secure_password_123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("wrong_password", hashed)

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes."""
        password = "test_password"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        assert hash1 != hash2
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)

    @pytest.mark.asyncio
    async def test_create_access_token(self, mock_session):
        """Test JWT token creation."""
        service = AuthService(mock_session)
        
        with patch("app.services.auth_service.UserRepository"):
            token = service.create_access_token(
                data={"sub": "test@example.com", "user_id": 1},
                expires_delta=None
            )

            assert token is not None
            assert isinstance(token, str)
            assert len(token) > 0

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mock_session):
        """Test successful user authentication."""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.hashed_password = AuthService.hash_password("password123")
        user.is_active = True

        with patch("app.services.auth_service.UserRepository") as MockUserRepo:
            user_repo = AsyncMock()
            user_repo.get_by_email_with_password.return_value = user
            MockUserRepo.return_value = user_repo

            service = AuthService(mock_session)
            result = await service.authenticate_user("test@example.com", "password123")

            assert "access_token" in result
            assert result["token_type"] == "bearer"
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mock_session):
        """Test authentication with non-existent user."""
        with patch("app.services.auth_service.UserRepository") as MockUserRepo:
            user_repo = AsyncMock()
            user_repo.get_by_email_with_password.return_value = None
            MockUserRepo.return_value = user_repo

            service = AuthService(mock_session)

            with pytest.raises(AuthenticationError) as exc_info:
                await service.authenticate_user("nonexistent@example.com", "password123")

            assert exc_info.value.code == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mock_session):
        """Test authentication with wrong password."""
        user = MagicMock()
        user.hashed_password = AuthService.hash_password("correct_password")

        with patch("app.services.auth_service.UserRepository") as MockUserRepo:
            user_repo = AsyncMock()
            user_repo.get_by_email_with_password.return_value = user
            MockUserRepo.return_value = user_repo

            service = AuthService(mock_session)

            with pytest.raises(AuthenticationError) as exc_info:
                await service.authenticate_user("test@example.com", "wrong_password")

            assert exc_info.value.code == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, mock_session):
        """Test authentication with inactive user."""
        user = MagicMock()
        user.hashed_password = AuthService.hash_password("password123")
        user.is_active = False

        with patch("app.services.auth_service.UserRepository") as MockUserRepo:
            user_repo = AsyncMock()
            user_repo.get_by_email_with_password.return_value = user
            MockUserRepo.return_value = user_repo

            service = AuthService(mock_session)

            with pytest.raises(AuthenticationError) as exc_info:
                await service.authenticate_user("test@example.com", "password123")

            assert "disabled" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_register_user_success(self, mock_session):
        """Test successful user registration."""
        with patch("app.services.auth_service.UserRepository") as MockUserRepo, \
             patch("app.services.auth_service.AccountRepository") as MockAccountRepo, \
             patch("app.services.auth_service.AuthService.create_access_token") as MockToken:
            
            user_repo = AsyncMock()
            user_repo.get_by_email.return_value = None
            user_repo.get_by_username.return_value = None
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "new@example.com"
            mock_user.username = "newuser"
            user_repo.create_user.return_value = mock_user
            MockUserRepo.return_value = user_repo

            account_repo = AsyncMock()
            mock_account = MagicMock()
            mock_account.account_number = "ACC00000001"
            account_repo.create_account.return_value = mock_account
            MockAccountRepo.return_value = account_repo

            MockToken.return_value = "mock_jwt_token"

            service = AuthService(mock_session)
            result = await service.register_user(
                email="new@example.com",
                username="newuser",
                password="password123"
            )

            assert "access_token" in result
            assert result["access_token"] == "mock_jwt_token"
            assert result["email"] == "new@example.com"

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, mock_session):
        """Test registration with existing email."""
        existing_user = MagicMock()
        
        with patch("app.services.auth_service.UserRepository") as MockUserRepo:
            user_repo = AsyncMock()
            user_repo.get_by_email.return_value = existing_user
            user_repo.get_by_username.return_value = None
            MockUserRepo.return_value = user_repo

            service = AuthService(mock_session)

            with pytest.raises(AuthenticationError) as exc_info:
                await service.register_user(
                    email="existing@example.com",
                    username="newuser",
                    password="password123"
                )

            assert "email" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_register_user_username_taken(self, mock_session):
        """Test registration with existing username."""
        with patch("app.services.auth_service.UserRepository") as MockUserRepo:
            user_repo = AsyncMock()
            user_repo.get_by_email.return_value = None
            user_repo.get_by_username.return_value = MagicMock()
            MockUserRepo.return_value = user_repo

            service = AuthService(mock_session)

            with pytest.raises(AuthenticationError) as exc_info:
                await service.register_user(
                    email="new@example.com",
                    username="taken",
                    password="password123"
                )

            assert "username" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_session):
        """Test get current user from token."""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.is_active = True

        with patch("app.services.auth_service.UserRepository") as MockUserRepo, \
             patch("app.services.auth_service.jwt") as MockJWT:
            
            MockJWT.decode.return_value = {"sub": "test@example.com", "user_id": 1}
            
            user_repo = AsyncMock()
            user_repo.get_by_email.return_value = user
            MockUserRepo.return_value = user_repo

            service = AuthService(mock_session)
            token = "valid_jwt_token"
            
            result = await service.get_current_user(token)

            assert result["email"] == "test@example.com"
            assert result["id"] == 1


class TestAccountService:
    """Unit tests for AccountService."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_account_success(self, mock_session):
        """Test get account details successfully."""
        account = MagicMock()
        account.id = 1
        account.user_id = 1
        account.account_number = "ACC00000001"
        account.balance = Decimal("1000.00")
        account.currency = "USD"
        account.is_active = True

        with patch("app.services.auth_service.AccountRepository") as MockAccountRepo:
            account_repo = AsyncMock()
            account_repo.get_by_id.return_value = account
            MockAccountRepo.return_value = account_repo

            service = AccountService(mock_session)
            result = await service.get_account(account_id=1, user_id=1)

            assert result["id"] == 1
            assert result["balance"] == 1000.00

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, mock_session):
        """Test get non-existent account."""
        with patch("app.services.auth_service.AccountRepository") as MockAccountRepo:
            account_repo = AsyncMock()
            account_repo.get_by_id.return_value = None
            MockAccountRepo.return_value = account_repo

            service = AccountService(mock_session)

            with pytest.raises(AccountNotFoundError):
                await service.get_account(account_id=999, user_id=1)

    @pytest.mark.asyncio
    async def test_get_account_unauthorized(self, mock_session):
        """Test get account belonging to another user."""
        account = MagicMock()
        account.id = 1
        account.user_id = 2

        with patch("app.services.auth_service.AccountRepository") as MockAccountRepo:
            account_repo = AsyncMock()
            account_repo.get_by_id.return_value = account
            MockAccountRepo.return_value = account_repo

            service = AccountService(mock_session)

            with pytest.raises(AuthorizationError):
                await service.get_account(account_id=1, user_id=1)
