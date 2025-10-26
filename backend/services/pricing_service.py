import os
from typing import Optional, Dict, Any


class PricingService:
    """Optional pricing backend via IBM watsonx.data (Trino).

    Looks up material pricing by normalized key. If not configured or on error,
    returns None so callers can fallback to local price DB.
    """

    def __init__(self) -> None:
        self.enabled = False
        self._client = None
        self._cache: Dict[str, Dict[str, Any]] = {}

        # Connection config via env
        self.host = os.getenv("WXD_HOST")
        self.port = int(os.getenv("WXD_PORT", "443"))
        self.user = os.getenv("WXD_USER") or "estimategenie"
        self.password = os.getenv("WXD_PASSWORD")
        self.token = os.getenv("WXD_TOKEN")  # JWT bearer token
        self.http_scheme = os.getenv("WXD_SCHEME", "https")  # https or http

        # Table config: catalog.schema.table and column names
        self.catalog = os.getenv("WXD_CATALOG", "hive")
        self.schema = os.getenv("WXD_SCHEMA", "public")
        self.table = os.getenv("WXD_TABLE", "materials_pricing")
        self.key_col = os.getenv("WXD_KEY_COLUMN", "key")
        self.name_col = os.getenv("WXD_NAME_COLUMN", "name")
        self.price_col = os.getenv("WXD_PRICE_COLUMN", "price")
        self.unit_col = os.getenv("WXD_UNIT_COLUMN", "unit")

        # Only enable if host provided
        if self.host:
            self.enabled = True

    def _connect(self):
        if self._client is not None:
            return
        try:
            import trino
            auth = None
            if self.token:
                auth = trino.auth.JWTAuthentication(self.token)
            elif self.password:
                auth = trino.auth.BasicAuthentication(self.user, self.password)

            self._client = trino.dbapi.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                http_scheme=self.http_scheme,
                auth=auth,
                catalog=self.catalog,
                schema=self.schema,
            )
        except Exception as e:
            # Disable on error to avoid repeated attempts per request
            print(f"PricingService: connect failed: {e}")
            self.enabled = False
            self._client = None

    def get_price(self, key: str) -> Optional[Dict[str, Any]]:
        """Return {price, unit, name} for a material key using watsonx.data, or None."""
        if not self.enabled:
            return None

        if key in self._cache:
            return self._cache[key]

        self._connect()
        if not self._client:
            return None

        fq_table = f"{self.catalog}.{self.schema}.{self.table}"
        sql = (
            f"SELECT {self.key_col}, {self.name_col}, {self.price_col}, {self.unit_col} "
            f"FROM {fq_table} WHERE {self.key_col} = ? LIMIT 1"
        )
        try:
            cur = self._client.cursor()
            cur.execute(sql, (key,))
            row = cur.fetchone()
            if not row:
                # Try name fallback: ILIKE on name
                sql2 = (
                    f"SELECT {self.key_col}, {self.name_col}, {self.price_col}, {self.unit_col} "
                    f"FROM {fq_table} WHERE {self.name_col} ILIKE ? LIMIT 1"
                )
                cur.execute(sql2, (f"%{key.replace('_', ' ')}%",))
                row = cur.fetchone()

            if row:
                # Row order must match select columns
                rec = {
                    "key": row[0],
                    "name": row[1],
                    "price": float(row[2]) if row[2] is not None else None,
                    "unit": row[3] or "unit",
                }
                if rec["price"] is not None:
                    self._cache[key] = rec
                    return rec
        except Exception as e:
            print(f"PricingService: query failed for key '{key}': {e}")

        return None

    def is_enabled(self) -> bool:
        return self.enabled
