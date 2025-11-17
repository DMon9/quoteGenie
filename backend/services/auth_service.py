"""
Authentication service for user management and JWT tokens
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import os
import sqlite3
import re
from models.user import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def normalize_email(email: str) -> str:
    """Normalize email address by converting to lowercase and stripping whitespace"""
    return email.strip().lower()

def is_valid_email(email: str) -> bool:
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

class AuthService:
    def __init__(self, db_path="estimategenie.db"):
        self.db_path = db_path
        self.init_database()

    @staticmethod
    def _parse_created_at(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None

    def init_database(self):
        """Initialize users table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                plan TEXT DEFAULT 'free',
                api_key TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                stripe_customer_id TEXT,
                subscription_status TEXT DEFAULT 'inactive',
                subscription_id TEXT,
                quotes_used INTEGER DEFAULT 0,
                api_calls_used INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()

    def create_access_token(self, user_id: str, email: str) -> str:
        """Create JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_id,
            "email": email,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def register_user(self, email: str, name: str, password: str, plan: str = "free") -> Optional[User]:
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                conn.close()
                return None
            
            # Create user
            import uuid
            user_id = str(uuid.uuid4())
            password_hash = User.hash_password(password)
            user = User(
                id=user_id,
                email=email,
                name=name,
                password_hash=password_hash,
                plan=plan
            )
            
            # Insert into database
            cursor.execute("""
                INSERT INTO users (id, email, name, password_hash, plan, api_key, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user.id,
                user.email,
                user.name,
                user.password_hash,
                user.plan,
                user.api_key,
                user.created_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return user
        except Exception as e:
            print(f"Error registering user: {e}")
            return None

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            user = User(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                password_hash=row["password_hash"],
                plan=row["plan"],
                api_key=row["api_key"],
                created_at=self._parse_created_at(row["created_at"]),
                stripe_customer_id=row["stripe_customer_id"],
                subscription_status=row["subscription_status"],
                subscription_id=row["subscription_id"],
                quotes_used=row["quotes_used"],
                api_calls_used=row["api_calls_used"]
            )
            
            if not user.verify_password(password):
                return None
            
            return user
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            user = User(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                password_hash=row["password_hash"],
                plan=row["plan"],
                api_key=row["api_key"],
                created_at=self._parse_created_at(row["created_at"]),
                stripe_customer_id=row["stripe_customer_id"],
                subscription_status=row["subscription_status"],
                subscription_id=row["subscription_id"],
                quotes_used=row["quotes_used"],
                api_calls_used=row["api_calls_used"]
            )
            
            return user
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE api_key = ?", (api_key,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            user = User(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                password_hash=row["password_hash"],
                plan=row["plan"],
                api_key=row["api_key"],
                created_at=self._parse_created_at(row["created_at"]),
                stripe_customer_id=row["stripe_customer_id"],
                subscription_status=row["subscription_status"],
                subscription_id=row["subscription_id"],
                quotes_used=row["quotes_used"],
                api_calls_used=row["api_calls_used"]
            )
            
            return user
        except Exception as e:
            print(f"Error getting user by API key: {e}")
            return None

    def update_user_usage(self, user_id: str, quotes_used: Optional[int] = None, api_calls_used: Optional[int] = None):
        """Update user usage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if quotes_used is not None:
                cursor.execute("UPDATE users SET quotes_used = ? WHERE id = ?", (quotes_used, user_id))
            
            if api_calls_used is not None:
                cursor.execute("UPDATE users SET api_calls_used = ? WHERE id = ?", (api_calls_used, user_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating user usage: {e}")

    def update_subscription(self, user_id: str, plan: str, subscription_id: str, subscription_status: str):
        """Update user subscription info"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET plan = ?, subscription_id = ?, subscription_status = ?
                WHERE id = ?
            """, (plan, subscription_id, subscription_status, user_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating subscription: {e}")
