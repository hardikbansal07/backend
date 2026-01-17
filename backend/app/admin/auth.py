from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from auth import verify_password, create_access_token, get_user
from models import UserInDB, UserRole
from mongo import mongo_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Admin Login Endpoint.
    Verifies username/password and checks if user has 'admin' role.
    Returns access token with role claim.
    """
    if mongo_db.db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    # 1. Fetch user (Try email first as it is the primary key in get_user)
    user = await get_user(form_data.username)
    
    # If not found by email, try finding by 'username' field explicitly
    if not user:
        user_dict = await mongo_db.db.users.find_one({"username": form_data.username})
        if user_dict:
            user = UserInDB(**user_dict)

    # 2. Verify Credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. CRITICAL SECURITY CHECK: Check if user.role == "admin"
    if user.role != UserRole.admin:
        logger.warning(f"Unauthorized admin login attempt by user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access the admin panel"
        )

    # 4. Issue Token
    access_token = create_access_token(
        data={"sub": user.email, "role": "admin"}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
