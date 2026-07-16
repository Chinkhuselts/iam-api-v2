import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from database import init_db, get_db_connection
import psycopg2
import os
app = FastAPI(title="IAM API V2")

# --- Security Setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Updated to 32+ characters to fix the PyJWT InsecureKeyLengthWarning!
SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Pydantic Models (Data Validation) ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Helper Functions & Middleware ---
def create_access_token(data: dict):
    """Generates a JWT valid for 30 minutes."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# This tells Swagger UI to add the "Authorize" lock icon
security = HTTPBearer() 

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Decodes the JWT and validates the user's session."""
    token = credentials.credentials
    try:
        # Attempt to decode the token using our secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload # Returns the dictionary: {"sub": "1", "role": "user", "exp": ...}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token signature")

# --- App Events & Public Routes ---
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "FastAPI and PostgreSQL are connected!"}

@app.post("/register", status_code=201)
def register_user(user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    
    insert_query = """
        INSERT INTO users (username, email, password_hash, role_id)
        VALUES (
            %s, 
            %s, 
            %s, 
            (SELECT id FROM roles WHERE name = 'user')
        )
        RETURNING id, username, email, created_at;
    """
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(insert_query, (user.username, user.email, hashed_password))
        new_user = cur.fetchone() 
        conn.commit()             
        return {"message": "User created successfully", "user": new_user}
        
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username or email already registered")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.post("/login")
def login_user(user: UserLogin):
    select_query = """
        SELECT u.id, u.password_hash, r.name as role_name 
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.email = %s;
    """
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(select_query, (user.email,))
        db_user = cur.fetchone()
        
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        if not pwd_context.verify(user.password, db_user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        access_token = create_access_token(
            data={"sub": str(db_user['id']), "role": db_user['role_name']}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    finally:
        cur.close()
        conn.close()

# --- Protected Routes (RBAC) ---
@app.get("/users/me")
def get_my_profile(user_data: dict = Depends(verify_token)):
    """A standard protected route. Any logged-in user can access this."""
    return {
        "message": "You have successfully bypassed the security guard!",
        "your_data": user_data
    }

@app.get("/admin/dashboard")
def get_admin_dashboard(user_data: dict = Depends(verify_token)):
    """A highly secure route. ONLY Admins are allowed."""
    if user_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: You do not have Admin privileges.")
    
    return {
        "message": "Welcome to the Admin Vault. Classified data goes here.",
        "admin_id": user_data.get("sub")
    }
