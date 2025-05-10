from datetime import datetime, timezone
from typing import Optional, Dict, List
from uuid import UUID
import logging

from pydantic import ValidationError
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password, generate_verification_token
from app.utils.nickname_gen import generate_nickname
from app.services.email_service import EmailService
from app.dependencies import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        return await cls._fetch_user(session, email=email)

    @classmethod
    async def get_by_nickname(cls, session: AsyncSession, nickname: str) -> Optional[User]:
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def create(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        try:
            validated_data = UserCreate(**user_data).model_dump()
            if await cls.get_by_email(session, validated_data["email"]):
                logger.error("User with this email already exists.")
                return None

            validated_data["hashed_password"] = hash_password(validated_data.pop("password"))
            new_user = User(**validated_data)
            nickname = generate_nickname()
            while await cls.get_by_nickname(session, nickname):
                nickname = generate_nickname()
            new_user.nickname = nickname

            count = await cls.count(session)
            new_user.role = UserRole.ADMIN if count == 0 else UserRole.ANONYMOUS

            if new_user.role == UserRole.ADMIN:
                new_user.email_verified = True
            else:
                new_user.verification_token = generate_verification_token()
                await email_service.send_verification_email(new_user)

            session.add(new_user)
            await session.commit()
            return new_user
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None

    @classmethod
    async def update(cls, session: AsyncSession, user_id: UUID, update_data: Dict[str, str]) -> Optional[User]:
        try:
            # ✅ Catch invalid emails and other bad fields
            validated_data = UserUpdate(**update_data).model_dump(exclude_unset=True)

            if 'password' in validated_data:
                validated_data['hashed_password'] = hash_password(validated_data.pop('password'))
            query = update(User).where(User.id == user_id).values(**validated_data).execution_options(synchronize_session="fetch")
            await cls._execute_query(session, query)
            return await cls.get_by_id(session, user_id)
        except Exception as e:
            logger.error(f"Update error: {e}")
            return None

    @classmethod
    async def delete(cls, session: AsyncSession, user_id: UUID) -> bool:
        user = await cls.get_by_id(session, user_id)
        if not user:
            return False
        await session.delete(user)
        await session.commit()
        return True

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        result = await session.execute(select(func.count()).select_from(User))
        return result.scalar()

    @classmethod
    async def list_users(cls, session: AsyncSession, skip: int = 0, limit: int = 10) -> List[User]:
        query = select(User).offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def login_user(cls, session: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await cls.get_by_email(session, email)
        if user and user.email_verified and not user.is_locked and verify_password(password, user.hashed_password):
            user.failed_login_attempts = 0
            user.last_login_at = datetime.now(timezone.utc)
            session.add(user)
            await session.commit()
            return user
        elif user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.is_locked = True
            session.add(user)
            await session.commit()
        return None

    @classmethod
    async def is_account_locked(cls, session: AsyncSession, email: str) -> bool:
        user = await cls.get_by_email(session, email)
        return user.is_locked if user else False

    @classmethod
    async def reset_password(cls, session: AsyncSession, user_id: UUID, new_password: str) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user:
            user.hashed_password = hash_password(new_password)
            user.failed_login_attempts = 0
            user.is_locked = False
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def verify_email_with_token(cls, session: AsyncSession, user_id: UUID, token: str) -> bool:
        user = await cls.get_by_id(session, user_id)
        if user and user.verification_token == token:
            user.email_verified = True
            user.verification_token = None
            user.role = UserRole.AUTHENTICATED
            session.add(user)
            await session.commit()
            return True
        return False

    @classmethod
    async def register_user(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        return await cls.create(session, user_data, email_service)

    @classmethod
    async def upgrade_to_professional(cls, session: AsyncSession, user_id: UUID, email_service: EmailService) -> Optional[User]:
        logger.debug(f"[UPGRADE] Attempting to upgrade user {user_id} to professional...")

        user = await cls.get_by_id(session, user_id)
        if not user:
            logger.warning(f"[UPGRADE] User {user_id} not found.")
            return None

        user.is_professional = True
        user.professional_status_updated_at = datetime.now(timezone.utc)
        session.add(user)
        await session.commit()
        logger.info(f"[UPGRADE] User {user.email} upgraded to professional.")

        try:
            await email_service.send_user_email({
                "name": user.first_name,
                "email": str(user.email)
            }, "professional_upgrade")
            logger.info(f"[EMAIL] Professional upgrade email sent to {user.email}")
        except Exception as e:
            logger.error(f"[EMAIL ERROR] Failed to send professional upgrade email: {e}")

        return user
