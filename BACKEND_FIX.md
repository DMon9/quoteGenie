## ✅ FIXED: Backend Configuration

### What Was Wrong

Your frontend was trying to connect to `http://localhost:8000`, but your backend is actually deployed on **Fly.io** at `https://quotegenie-api.fly.dev`.

### What I Fixed

1. **Updated `assets/js/api-config.js`**
   - Changed default API base URL from `https://api.estimategenie.net` to `https://quotegenie-api.fly.dev`
   - Removed localhost detection logic that was forcing local backend
   - Now always uses Fly.io backend by default

2. **Created `LOCAL_DEV.md`**
   - Clear guide that backend is on Fly.io
   - Shows how to run just the frontend locally
   - Explains how to override for local backend testing if needed

### ✅ Ready to Test

**The signup should work now!**

1. Make sure frontend is running:

   ```powershell
   python -m http.server 8080
   ```

2. Open: <http://localhost:8080/signup.html>

3. Fill in the form and click "Create Account"

4. **It will connect to your Fly.io backend automatically**

### Backend Status

✅ **Fly.io backend is LIVE and healthy:**

- URL: <https://quotegenie-api.fly.dev>
- Health: <https://quotegenie-api.fly.dev/health>
- Status: All services running (vision, llm, database)

### How It Works Now

```
Browser (localhost:8080)
    ↓
Frontend JavaScript (api-config.js)
    ↓
HTTPS Request to Fly.io
    ↓
Backend API (quotegenie-api.fly.dev)
    ↓
Database on Fly.io
```

### For Local Development

If you need to test backend changes:

1. Override in browser console:

   ```javascript
   localStorage.setItem('API_BASE_URL', 'http://localhost:8000')
   ```

2. Start local backend:

   ```powershell
   cd backend
   ..\.venv-3\Scripts\Activate.ps1
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

3. Reset to Fly.io:

   ```javascript
   localStorage.removeItem('API_BASE_URL')
   ```

See `LOCAL_DEV.md` for complete guide.
