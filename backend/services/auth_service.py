"""
Authentication service for user management and JWT tokens
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
import sqlite3
import sys
from models.user import User

# Security Configuration
# List of known weak/default keys that should trigger warnings
# These are exact string matches to avoid false positives
# Add common weak keys here to help detect insecure configurations
WEAK_KEYS = {
    "your-secret-key-change-in-production", 
    "secret", 
    "test", 
    "dev", 
    "development",
    "INSECURE_DEVELOPMENT_KEY_DO_NOT_USE_IN_PRODUCTION",
    "changeme",
    "change-me-to-a-secure-random-32-char-key"
}

# Minimum recommended key length for JWT secrets
MIN_KEY_LENGTH = 32

# Get JWT secret key from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Validate that JWT_SECRET_KEY is set and secure
if not SECRET_KEY:
    print("=" * 70, file=sys.stderr)
    print("SECURITY WARNING: JWT_SECRET_KEY environment variable is not set!", file=sys.stderr)
    print("Using an insecure default for development only.", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("For production, set a secure random key:", file=sys.stderr)
    print("  export JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    # Use a development-only fallback that is clearly insecure
    SECRET_KEY = "INSECURE_DEVELOPMENT_KEY_DO_NOT_USE_IN_PRODUCTION"

# Warn if using a weak or default secret key
# Check length first (most important) or exact match against known weak keys
is_weak_key = len(SECRET_KEY) < MIN_KEY_LENGTH or SECRET_KEY in WEAK_KEYS
if is_weak_key:
    print("=" * 70, file=sys.stderr)
    print("SECURITY WARNING: JWT_SECRET_KEY is weak or uses default value!", file=sys.stderr)
    print("This is a critical security vulnerability in production.", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("Generate a strong key with:", file=sys.stderr)
    print("  python -c 'import secrets; print(secrets.token_urlsafe(32))'", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

class AuthService:
    def __init__(self, db_path="estimategenie.db"):
        self.db_path = db_path
        self.init_database()

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
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        except jwt.JWTError:
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
                user.created_at
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
                created_at=datetime.fromisoformat(row["created_at"]),
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
                created_at=datetime.fromisoformat(row["created_at"]),
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
                created_at=datetime.fromisoformat(row["created_at"]),
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
