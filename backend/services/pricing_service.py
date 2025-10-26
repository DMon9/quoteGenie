import os
from typing import Optional, Dict, Any


class PricingService:
    """Disabled pricing service - no external pricing backend configured.
    
    Always returns None to fallback to local/external price lists.
    """

    def __init__(self) -> None:
        self.enabled = False
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Check if watsonx is configured
        if os.getenv("WXD_HOST") and os.getenv("WXD_TOKEN"):
            print("PricingService: watsonx.data configuration detected but disabled")
        else:
            print("PricingService: no external pricing backend configured")
    def get_price(self, key: str) -> Optional[Dict[str, Any]]:
        """Return None - no external pricing backend configured."""
        return None

    def is_enabled(self) -> bool:
        """Always returns False - external pricing disabled."""
        return False
