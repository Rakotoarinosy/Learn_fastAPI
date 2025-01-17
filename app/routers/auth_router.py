from jose import jwt
from datetime import datetime, timedelta
import bcrypt
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from app.db import get_conn
from psycopg.rows import class_row
from psycopg2.extras import DictCursor
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/auth")

class SignUpReq(BaseModel):
    email: EmailStr
    username: str
    password: str

class SignInReq(BaseModel):
    email: EmailStr
    password: str
    
class UserDB(BaseModel):
    user_id: int
    email: str
    username: str | None
    password: str | None
    
    
@router.post("/signup")
def signup(sign_up_req: SignUpReq):
    hashed = bcrypt.hashpw(sign_up_req.password.encode("utf-8"), bcrypt.gensalt())
    with get_conn() as conn:
        with conn.cursor() as cursor:
            record = cursor.execute(
                "select * from users where email = %s or username = %s",
                [sign_up_req.email, sign_up_req.username],
            )
            record = cursor.fetchone()
             
            if record:
                raise HTTPException(status_code=400, detail="user aleready exists")
            
            cursor.execute(
                "insert into users (email, username, password) values (%s,%s,%s)", [sign_up_req.email, sign_up_req.username, hashed.decode("utf-8")]
            )
    return {"message": "sign up succcess"}

@router.post("/signin")
def signin(sign_in_req: SignInReq, response: Response):
    # Check for missing fields
    if not sign_in_req.email or not sign_in_req.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    with get_conn() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Fetch the user by email
            cursor.execute(
                "SELECT * FROM users WHERE email ILIKE %s", [sign_in_req.email]
            )
            record = cursor.fetchone()
            
            if not record:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if the password is correct
            if not record['password']:
                raise HTTPException(status_code=500, detail="Invalid password record")

            # Verify the provided password matches the stored hash
            is_password_correct = bcrypt.checkpw(
                sign_in_req.password.encode("utf-8"), record['password'].encode("utf-8")
            )
            
            if not is_password_correct:
                raise HTTPException(status_code=401, detail="Incorrect credentials")
            expire = datetime.utcnow() + timedelta(minutes=15)
            paylod = {"sub": str(record['user_id']), "exp": expire}
            token = jwt.encode(paylod, settings.jwt_secret, algorithm="HS256")
            response.set_cookie(key="jwt",value=token)
    return {"message": "Sign in success"}