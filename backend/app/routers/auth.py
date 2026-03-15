from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate, ForgotPassword
from app.core.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime
import pycurl
from urllib.parse import urlencode
import random
import string
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.error("Token payload missing 'sub' (email)")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT Decode error: {str(e)}")
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.error(f"User not found for email: {email}")
        raise credentials_exception
    return user


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        role=user.role,  # Use the role provided during registration
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user.last_login = datetime.now()
    db.commit()

    token = create_access_token({"sub": user.email, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Updating profile for user: {current_user.email}")
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        if user_update.email != current_user.email:
            existing = db.query(User).filter(User.email == user_update.email).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already taken")
            current_user.email = user_update.email
    
    if user_update.password is not None:
        current_user.password_hash = hash_password(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Allow admin and manager to get all users
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    
    users = db.query(User).all()
    return users


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserCreate,  # We'll reuse this for updates
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only allow admin users to update users
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    
    # Get the user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    user.full_name = user_update.full_name
    user.email = user_update.email
    user.role = user_update.role
    if user_update.password:  # Only update password if provided
        user.password_hash = hash_password(user_update.password)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only allow admin users to delete users
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    
    # Get the user to delete
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

def sends_mail(mail, msg):
    try:
        from io import BytesIO
        buffer = BytesIO()
        crl = pycurl.Curl()
        crl.setopt(crl.URL, 'https://alc-training.in/gateway.php')
        data = {'email': mail, 'msg': msg}
        pf = urlencode(data)
        crl.setopt(crl.POSTFIELDS, pf)
        crl.setopt(crl.WRITEDATA, buffer)
        crl.perform()
        crl.close()
        body = buffer.getvalue().decode('iso-8859-1')
        logger.info(f"Mail gateway response for {mail}: {body}")
    except Exception as e:
        logger.error(f"Failed to send email to {mail}: {str(e)}")

@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # We return 200 even if user not found for security reasons
        return {"message": "If this email is registered, you will receive a reset link/code"}
    
    # Generate a temporary password for simplicity in this demo, 
    # or you'd usually generate a reset token.
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    user.password_hash = hash_password(temp_password)
    db.commit()
    
    msg = f"Hello {user.full_name}, your temporary password for EcoRoute AI is: {temp_password}. Please change it after logging in."
    sends_mail(user.email, msg)
    
    return {"message": "Success! Check your email for your temporary password."}
