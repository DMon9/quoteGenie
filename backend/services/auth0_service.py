"""
Auth0 authentication service for user management
"""
from typing import Optional
import os
from jose import jwt, JWTError
from auth0.authentication import GetToken
from auth0.management import Auth0
import httpx

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", f"https://{AUTH0_DOMAIN}/api/v2/")
AUTH0_ALGORITHMS = ["RS256"]

class Auth0Service:
    """Service for Auth0 authentication and user management"""
    
    def __init__(self):
        self.domain = AUTH0_DOMAIN
        self.client_id = AUTH0_CLIENT_ID
        self.client_secret = AUTH0_CLIENT_SECRET
        self.audience = AUTH0_AUDIENCE
        self.algorithms = AUTH0_ALGORITHMS
        
        # Initialize Auth0 Management API client
        if self.domain and self.client_id and self.client_secret:
            try:
                get_token = GetToken(self.domain, self.client_id, client_secret=self.client_secret)
                token = get_token.client_credentials(f"https://{self.domain}/api/v2/")
                self.mgmt_api = Auth0(self.domain, token['access_token'])
            except Exception as e:
                print(f"Warning: Could not initialize Auth0 Management API: {e}")
                self.mgmt_api = None
        else:
            print("Warning: Auth0 credentials not configured")
            self.mgmt_api = None
    
    def is_configured(self) -> bool:
        """Check if Auth0 is properly configured"""
        return bool(self.domain and self.client_id and self.client_secret)
    
    async def get_jwks(self):
        """Get JSON Web Key Set from Auth0"""
        if not self.domain:
            return None
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://{self.domain}/.well-known/jwks.json")
            return response.json()
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verify Auth0 JWT token and return payload"""
        if not self.is_configured():
            return None
        
        try:
            # Get the signing key from Auth0
            jwks = await self.get_jwks()
            if not jwks:
                return None
            
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
            
            if not rsa_key:
                return None
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=f"https://{self.domain}/"
            )
            
            return payload
            
        except JWTError as e:
            print(f"JWT verification error: {e}")
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None
    
    def get_user_info(self, user_id: str) -> Optional[dict]:
        """Get user information from Auth0 by user ID"""
        if not self.mgmt_api:
            return None
        
        try:
            user = self.mgmt_api.users.get(user_id)
            return user
        except Exception as e:
            print(f"Error fetching user info: {e}")
            return None
    
    def create_user(self, email: str, password: str, name: str) -> Optional[dict]:
        """Create a new user in Auth0"""
        if not self.mgmt_api:
            return None
        
        try:
            user_data = {
                "email": email,
                "password": password,
                "name": name,
                "connection": "Username-Password-Authentication",
                "email_verified": False
            }
            user = self.mgmt_api.users.create(user_data)
            return user
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def update_user_metadata(self, user_id: str, metadata: dict) -> bool:
        """Update user metadata in Auth0"""
        if not self.mgmt_api:
            return False
        
        try:
            self.mgmt_api.users.update(user_id, {"user_metadata": metadata})
            return True
        except Exception as e:
            print(f"Error updating user metadata: {e}")
            return False
    
    def get_authorization_url(self, redirect_uri: str, state: str = "") -> str:
        """Generate Auth0 authorization URL for login"""
        if not self.domain or not self.client_id:
            return ""
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://{self.domain}/authorize?{query_string}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[dict]:
        """Exchange authorization code for access token"""
        if not self.is_configured():
            return None
        
        try:
            get_token = GetToken(self.domain, self.client_id, client_secret=self.client_secret)
            token = get_token.authorization_code(code, redirect_uri)
            return token
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return None
