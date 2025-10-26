# Pricing Hot-Reload Feature

## Overview

The backend now supports **automatic hot-reload** of external pricing lists. Price changes are detected and applied without restarting the API container.

## Configuration

Set pricing file(s) via environment variables in `docker-compose.yml`:

```yaml
environment:
  - PRICE_LIST_FILE=./pricing/materials_pricing_400.json
  # OR for multiple files:
  - PRICE_LIST_FILES=./pricing/list1.json,./pricing/list2.csv
  - PRICE_LIST_RELOAD_SEC=10  # Check interval (default: 10 seconds)
```

## Supported File Formats

### JSON List (your current format)
```json
[
  {
    "Material": "2x4x8 Lumber",
    "Final_Price_USD": 6.49,
    "Unit_Type": "piece",
    "Category": "Framing"
  }
]
```

### JSON Dictionary
```json
{
  "lumber_2x4": {
    "price": 6.49,
    "unit": "piece",
    "description": "2x4x8 lumber"
  }
}
```

### CSV
```csv
key,price,unit,description
lumber_2x4,6.49,piece,2x4x8 lumber
tile,3.50,sqft,Ceramic tile
```

## API Endpoints

### Check Pricing Status
```bash
GET http://localhost:8001/v1/pricing/status
```

Returns:
```json
{
  "external_files": ["/app/pricing/materials_pricing_400.json"],
  "external_keys_count": 134,
  "total_materials_count": 143,
  "reload_interval_sec": 10.0,
  "last_check_timestamp": 1761436920.915401,
  "watsonx_enabled": true
}
```

### Lookup a Price
```bash
GET http://localhost:8001/v1/pricing/lookup?key=2x4x8%20Lumber
```

Returns:
```json
{
  "key": "lumber_2x4",
  "source": "external-list",
  "price": 6.49,
  "unit": "piece"
}
```

Source values:
- `external` - from IBM watsonx.data (Trino) if configured
- `external-list` - from your pricing file
- `local` - from built-in materials DB
- `none` - not found

### Force Reload
```bash
POST http://localhost:8001/v1/pricing/reload
```

Returns:
```json
{
  "files": ["/app/pricing/materials_pricing_400.json"],
  "keys_loaded": 134,
  "last_check": 1761436920.915401,
  "interval_sec": 10.0
}
```

## How It Works

1. **On startup**: Backend loads price lists from configured files
2. **During operation**: Every `PRICE_LIST_RELOAD_SEC` seconds (default 10), the estimator checks file modification times
3. **On change**: If any file has a newer mtime, all external lists are reloaded automatically
4. **Pricing hierarchy**: 
   - IBM watsonx.data (if enabled via WXD_* env vars)
   - External price lists (your JSON/CSV files)
   - Built-in materials DB (fallback)

## Testing Hot-Reload

Run the included test script:
```bash
docker exec backend-api-1 python /app/test_hot_reload.py
```

Or test manually:
1. Edit `backend/pricing/materials_pricing_400.json`
2. Change a price value
3. Save the file
4. Wait 10 seconds (or POST to `/v1/pricing/reload`)
5. Query `/v1/pricing/lookup?key=lumber_2x4` to see the new price

## Current Status

✅ **Active**: 134 materials loaded from external list  
✅ **Auto-reload**: Enabled with 10s check interval  
✅ **Pricing sources**: External lists + built-in DB + optional watsonx.data  
✅ **Endpoints**: status, lookup, reload  
✅ **Schema support**: Case-insensitive JSON/CSV with flexible field names  

## Logs

Check container logs to see reload activity:
```bash
docker logs backend-api-1 --tail 50
```

Look for:
```
Price list loaded from /app/pricing/materials_pricing_400.json: 400 entries (e.g., lumber_2x4, ...)
```

## Notes

- File paths can be relative (to `/app` inside container) or absolute
- Multiple files are merged (last wins on duplicate keys)
- Material names are normalized (e.g., "2x4x8 Lumber" → `lumber_2x4`)
- Hot-reload is throttled by `PRICE_LIST_RELOAD_SEC` to avoid excessive file I/O
- Manual reload via POST endpoint bypasses throttle
