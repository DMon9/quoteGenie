# API Configuration Guide

## Overview

`assets/js/api-config.js` provides a centralized way to manage API endpoints across all frontend pages.

## Features

1. **Single Source of Truth**: One place to define the API base URL
2. **Environment Detection**: Automatically uses localhost when testing locally
3. **Easy Overrides**: Switch APIs via URL parameter or localStorage
4. **Auto-Auth**: Automatically injects JWT/API key headers
5. **Built-in Health Check**: Test API connectivity with one call

---

## Basic Usage

### 1. Include in your HTML

```html
<script src="/assets/js/api-config.js"></script>
```

### 2. Use in your code

**Old way (hardcoded):**
```javascript
const response = await fetch("https://api.estimategenie.net/api/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password })
});
```

**New way (dynamic):**
```javascript
const response = await ApiConfig.fetch(API.login, {
  method: "POST",
  body: JSON.stringify({ email, password })
});
```

or

```javascript
const response = await fetch(ApiConfig.url(API.login), {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password })
});
```

---

## Available Endpoints

Access via `API` or `ApiConfig.endpoints`:

```javascript
API.health              // /health
API.docs                // /docs
API.register            // /api/v1/auth/register
API.login               // /api/v1/auth/login
API.me                  // /api/v1/auth/me
API.usage               // /api/v1/auth/usage
API.updateProfile       // /api/v1/auth/update-profile
API.changePassword      // /api/v1/auth/change-password
API.regenerateKey       // /api/v1/auth/regenerate-key
API.deleteAccount       // /api/v1/auth/delete-account
API.createPortalSession // /api/v1/payment/create-portal-session
API.quotes              // /v1/quotes
API.quote(id)           // /v1/quotes/{id}
```

---

## Override Methods

### Method 1: URL Parameter (Temporary)

Test against a different API without changing code:

```
https://www.estimategenie.net/login.html?api=http://localhost:8000
https://www.estimategenie.net/dashboard.html?api=https://staging-api.estimategenie.net
```

Useful for:
- Local development
- Testing staging environments
- Debugging production issues

### Method 2: localStorage (Persistent)

Set once in browser console, persists across page reloads:

```javascript
// Switch to localhost
localStorage.setItem('API_BASE_URL', 'http://localhost:8000');

// Switch to staging
localStorage.setItem('API_BASE_URL', 'https://staging-api.estimategenie.net');

// Reset to default
localStorage.removeItem('API_BASE_URL');
// or
ApiConfig.reset();
```

### Method 3: Programmatic

```javascript
ApiConfig.setBaseUrl('https://new-api.example.com');
```

---

## Auto-Authentication

The `ApiConfig.fetch()` wrapper automatically adds auth headers if tokens are present in localStorage:

```javascript
// Tokens stored after login
localStorage.setItem('auth_token', 'jwt-token-here');
localStorage.setItem('api_key', 'api-key-here');

// This request will auto-include Authorization: Bearer <token>
const user = await ApiConfig.fetch(API.me).then(r => r.json());
```

Manual auth header injection still works:
```javascript
const response = await ApiConfig.fetch(API.quotes, {
  method: "POST",
  headers: {
    "Authorization": "Bearer custom-token",  // Override
    "X-API-Key": "custom-key"
  },
  body: JSON.stringify(quoteData)
});
```

---

## Health Check

Test API connectivity:

```javascript
const isHealthy = await ApiConfig.testConnection();
if (!isHealthy) {
  alert("Cannot connect to API. Please check your connection.");
}
```

In browser console:
```javascript
await ApiConfig.testConnection();
// [API Config] Health check: OK 200
```

---

## Migration Guide

### Before (scattered endpoints)

```javascript
// login.html
fetch("https://api.estimategenie.net/api/v1/auth/login", {...})

// dashboard.html
fetch("https://api.estimategenie.net/api/v1/auth/me", {...})
fetch("https://api.estimategenie.net/api/v1/auth/regenerate-key", {...})

// signup.html
fetch("https://api.estimategenie.net/api/v1/auth/register", {...})
```

### After (centralized)

```html
<!-- Include once in <head> -->
<script src="/assets/js/api-config.js"></script>
```

```javascript
// login.html
ApiConfig.fetch(API.login, { method: "POST", body: JSON.stringify(credentials) })

// dashboard.html
ApiConfig.fetch(API.me)
ApiConfig.fetch(API.regenerateKey, { method: "POST" })

// signup.html
ApiConfig.fetch(API.register, { method: "POST", body: JSON.stringify(userData) })
```

---

## Environment Detection

| Environment | API Base URL | Notes |
|-------------|--------------|-------|
| `localhost` | `http://localhost:8000` | Auto-detected |
| Production | `https://api.estimategenie.net` | Default |
| Override | User-specified | Via URL param or localStorage |

---

## Browser Console Helpers

```javascript
// Check current config
console.log(ApiConfig.baseUrl);

// Test connectivity
await ApiConfig.testConnection();

// Switch to local backend
ApiConfig.setBaseUrl('http://localhost:8000');

// Switch to production
ApiConfig.reset();

// List all endpoints
console.table(API);
```

---

## Benefits

1. **Zero-touch endpoint changes**: Update one file, all pages follow
2. **Easier testing**: Switch APIs with a query parameter
3. **Cleaner code**: No hardcoded URLs scattered across files
4. **Auto-auth**: Don't repeat Bearer token logic everywhere
5. **Type safety ready**: Easy to convert to TypeScript later

---

## Next Steps

1. Include `api-config.js` in all HTML pages
2. Replace hardcoded `fetch("https://...")` with `ApiConfig.fetch(API.endpoint)`
3. Test with `?api=http://localhost:8000` during development
4. Optionally add a settings UI to let users switch API environments

---

## Example: Login Page

```html
<!DOCTYPE html>
<html>
<head>
  <script src="/assets/js/api-config.js"></script>
</head>
<body>
  <form id="loginForm">
    <input type="email" id="email" required>
    <input type="password" id="password" required>
    <button type="submit">Login</button>
  </form>

  <script>
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;

      try {
        const response = await ApiConfig.fetch(API.login, {
          method: 'POST',
          body: JSON.stringify({ email, password })
        });

        if (response.ok) {
          const data = await response.json();
          localStorage.setItem('auth_token', data.token);
          window.location.href = '/dashboard.html';
        } else {
          alert('Login failed');
        }
      } catch (error) {
        console.error('Login error:', error);
        alert('Cannot connect to API');
      }
    });
  </script>
</body>
</html>
```

---

## Troubleshooting

**Issue**: "ApiConfig is not defined"
- **Fix**: Ensure `<script src="/assets/js/api-config.js"></script>` loads before other scripts

**Issue**: CORS errors
- **Fix**: Verify backend ALLOW_ORIGINS includes the frontend domain

**Issue**: Health check fails
- **Fix**: Check network tab in DevTools; ensure API is deployed and reachable

**Issue**: Auth headers not added
- **Fix**: Ensure `auth_token` or `api_key` are in localStorage after login

---

## Production Checklist

- [x] `api-config.js` included in all pages
- [x] Default API set to `https://api.estimategenie.net`
- [x] Backend CORS allows `https://www.estimategenie.net`, `https://estimategenie.net`, `https://api.estimategenie.net`
- [x] Stripe webhook uses `https://api.estimategenie.net/api/v1/webhooks/stripe`
- [x] Cloudflare DNS has CNAME: `api` → `quotegenie-api.fly.dev` (proxied)
