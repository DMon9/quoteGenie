"""
Authentication service for user management and JWT tokens
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import os
import re
import sqlite3
from models.user import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def normalize_email(email: str) -> str:
    """Normalize email for consistent storage and comparison."""
    return (email or "").strip().lower()


def is_valid_email(email: str) -> bool:
    """Validate email format using a simplified RFC 5322 regex."""
    if not email or len(email) < 5:
        return False
    return EMAIL_REGEX.match(email) is not None


def is_strong_password(password: str) -> bool:
    """
    Validate password strength.
    Requirements:
    - At least 8 characters
    - Contains at least one letter
    - Contains at least one number
    """
    if not password or len(password) < 8:
        return False
    
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_letter and has_digit


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
        email = normalize_email(email)
        if not is_valid_email(email):
            raise ValueError("Invalid email format")
        if not is_strong_password(password):
            raise ValueError("Password must be at least 8 characters and contain both letters and numbers")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
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
            
            email = normalize_email(email)
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
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

    def update_user_stripe_customer(self, user_id: str, stripe_customer_id: str):
        """Update user's Stripe customer ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET stripe_customer_id = ?
                WHERE id = ?
            """, (stripe_customer_id, user_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating Stripe customer ID: {e}")

    def create_password_reset_token(self, email: str) -> Optional[str]:
        """Create a password reset token for user"""
        try:
            email = normalize_email(email)
            # Check if user exists
            user = self.get_user_by_email(email)
            if not user:
                return None
            
            # Create reset token (valid for 1 hour)
            expire = datetime.now(timezone.utc) + timedelta(hours=1)
            reset_token_payload = {
                "sub": user.id,
                "email": email,
                "type": "password_reset",
                "exp": expire
            }
            reset_token = jwt.encode(reset_token_payload, SECRET_KEY, algorithm=ALGORITHM)
            return reset_token
        except Exception as e:
            print(f"Error creating password reset token: {e}")
            return None

    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        try:
            # Verify token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check if it's a password reset token
            if payload.get("type") != "password_reset":
                return False
            
            user_id = payload.get("sub")
            if not user_id:
                return False
            
            # Update password
            new_hash = User.hash_password(new_password)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
            conn.commit()
            conn.close()
            
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False
        except Exception as e:
            print(f"Error resetting password: {e}")
            return False

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            email = normalize_email(email)
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
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
            print(f"Error getting user by email: {e}")
            return None

