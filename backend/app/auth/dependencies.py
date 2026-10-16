from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.jwt import decode_token
from app.database import get_db
from app.models.user import User

_bearer = HTTPBearer()

ROLES = {"viewer": 0, "finance_reviewer": 1, "billing_admin": 2}


async def _get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email: str = payload.get("sub", "")
    result = await db.execute(select(User).where(User.email == email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _role_dependency(minimum_role: str):
    async def check(user: User = Depends(_get_current_user)) -> User:
        if ROLES.get(user.role, -1) < ROLES[minimum_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return check


require_viewer = _role_dependency("viewer")
require_finance_reviewer = _role_dependency("finance_reviewer")
require_billing_admin = _role_dependency("billing_admin")
