from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_email_service, require_role, get_settings
from app.schemas.pagination_schema import EnhancedPagination
from app.schemas.token_schema import TokenResponse
from app.schemas.user_schemas import UserCreate, UserUpdate, UserListResponse, UserResponse
from app.services.user_service import UserService
from app.services.jwt_service import create_access_token
from app.services.email_service import EmailService
from app.utils.link_generation import create_user_links, generate_pagination_links

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
settings = get_settings()


@router.get("/users/{user_id}", response_model=UserResponse, tags=["User Management"])
async def get_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user).model_copy(update={
        "links": create_user_links(user.id, request)
    })


@router.put("/users/{user_id}", response_model=UserResponse, tags=["User Management"])
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    updated_user = await UserService.update(db, user_id, user_update.model_dump(exclude_unset=True))
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(updated_user).model_copy(update={
        "links": create_user_links(updated_user.id, request)
    })


@router.delete("/users/{user_id}", status_code=204, tags=["User Management"])
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    success = await UserService.delete(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=204)


@router.post("/users/", response_model=UserResponse, status_code=201, tags=["User Management"])
async def create_user(
    user: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
    token: str = Depends(oauth2_scheme),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    existing_user = await UserService.get_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    created_user = await UserService.create(db, user.model_dump(), email_service)
    if not created_user:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return UserResponse.model_validate(created_user).model_copy(update={
        "links": create_user_links(created_user.id, request)
    })


@router.get("/users/", response_model=UserListResponse, tags=["User Management"])
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    total_users = await UserService.count(db)
    users = await UserService.list_users(db, skip, limit)
    user_responses = [UserResponse.model_validate(u) for u in users]
    return UserListResponse(
        items=user_responses,
        total=total_users,
        page=skip // limit + 1,
        size=len(user_responses),
        links=generate_pagination_links(request, skip, limit, total_users)
    )


@router.post("/users/{user_id}/upgrade", response_model=UserResponse, tags=["User Management"])
async def upgrade_user_to_professional(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service),
    current_user: dict = Depends(require_role(["ADMIN", "MANAGER"]))
):
    user = await UserService.upgrade_to_professional(db, user_id, email_service)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user).model_copy(update={
        "links": create_user_links(user.id, request)
    })


@router.post("/register/", response_model=UserResponse, tags=["Login and Registration"])
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    user = await UserService.register_user(session, user_data.model_dump(), email_service)
    if user:
        return user
    raise HTTPException(status_code=400, detail="Email already exists")


@router.post("/login/", response_model=TokenResponse, tags=["Login and Registration"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    if await UserService.is_account_locked(session, form_data.username):
        raise HTTPException(status_code=400, detail="Account locked due to too many failed login attempts.")
    user = await UserService.login_user(session, form_data.username, form_data.password)
    if user:
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "role": str(user.role.name)},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect email or password")


@router.get("/verify-email/{user_id}/{token}", status_code=200, tags=["Login and Registration"])
async def verify_email(
    user_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    if await UserService.verify_email_with_token(db, user_id, token):
        return {"message": "Email verified successfully"}
    raise HTTPException(status_code=400, detail="Invalid or expired verification token")
