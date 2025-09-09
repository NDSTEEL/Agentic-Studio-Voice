"""
Authentication endpoints for login, register, and user management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
import os

from ...auth.jwt_handler import create_access_token, verify_token
from ...auth.middleware import get_current_user
from ...auth.models import UserAuth

router = APIRouter()

# Pydantic models for request/response
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class AuthResponse(BaseModel):
    user: dict
    token: str
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str

# Mock user store (in production, use database)
MOCK_USERS = {}

def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256((password + "salt").encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    email = request.email.lower()
    
    # Check if user exists
    if email not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user_data = MOCK_USERS[email]
    
    # Verify password
    if not verify_password(request.password, user_data["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create JWT token
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "tenant_id": user_data["tenant_id"]
    }
    
    token = create_access_token(payload, expires_in=3600)
    
    return AuthResponse(
        user={
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "created_at": user_data["created_at"]
        },
        token=token,
        expires_in=3600
    )

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Registration endpoint"""
    email = request.email.lower()
    
    # Check if user already exists
    if email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Create new user
    import uuid
    from datetime import datetime
    
    user_id = str(uuid.uuid4())
    tenant_id = f"tenant_{user_id[:8]}"  # Generate tenant ID
    
    user_data = {
        "id": user_id,
        "email": email,
        "name": request.name or email.split("@")[0],
        "password": hash_password(request.password),
        "tenant_id": tenant_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store user (in production, save to database)
    MOCK_USERS[email] = user_data
    
    # Create JWT token
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "tenant_id": user_data["tenant_id"]
    }
    
    token = create_access_token(payload, expires_in=3600)
    
    return AuthResponse(
        user={
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "created_at": user_data["created_at"]
        },
        token=token,
        expires_in=3600
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserAuth = Depends(get_current_user)):
    """Get current user information"""
    email = current_user.email.lower()
    
    if email not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_data = MOCK_USERS[email]
    
    return UserResponse(
        id=user_data["id"],
        email=user_data["email"],
        name=user_data["name"],
        created_at=user_data["created_at"]
    )

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Successfully logged out"}

# Initialize with a test user for development
def init_test_user():
    """Initialize test user for development"""
    test_email = "test@example.com"
    if test_email not in MOCK_USERS:
        import uuid
        from datetime import datetime
        
        user_id = str(uuid.uuid4())
        tenant_id = f"tenant_{user_id[:8]}"
        
        MOCK_USERS[test_email] = {
            "id": user_id,
            "email": test_email,
            "name": "Test User",
            "password": hash_password("password123"),
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat()
        }

# Initialize test user on import
init_test_user()