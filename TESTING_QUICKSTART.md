# Quick Testing Instructions

## 🚨 Issue: Local Backend Not Staying Up

The local backend is starting but immediately shutting down. This is likely due to:

1. Missing environment variables
2. Database connection issues
3. Import errors

## ✅ Solution: Test with Production API

Instead of local backend, use the production API at **<https://api.estimategenie.net>**

### Quick Start

1. **Open Test Dashboard**
   - Open: `http://localhost:8080/test-dashboard.html`
   - Or directly open: `test-dashboard.html` in your browser

2. **Check System Status**
   - Should show: `API Endpoint: https://api.estimategenie.net`
   - Click "Refresh Status"
   - Should show: `✅ Healthy` for API Health

3. **Test Authentication**
   - If not logged in, click "Login" button
   - Sign in with your credentials
   - Return to test dashboard

4. **Use the Calculator**
   - In "Advanced Options Calculator" section
   - Adjust sliders and see live calculations
   - This tests the pricing logic without making API calls

5. **Test Real Quote Generation**
   - Click "Mobile Quote" link
   - Upload an image
   - Set advanced options
   - Generate quote

---

## 🔧 To Fix Local Backend (Optional)

If you want to run backend locally for testing:

### Step 1: Check Environment Variables

```powershell
# Set required env vars
$env:GOOGLE_API_KEY="your_key_here"
$env:LLM_PROVIDER="google"
$env:GEMINI_MODEL="gemini-1.5-flash"
```

### Step 2: Start Backend

```powershell
cd c:\Users\user\quoteGenie\backend
python app.py
```

### Step 3: Configure Frontend to Use Local

```javascript
// In browser console on test-dashboard.html:
localStorage.setItem('API_BASE_URL', 'http://localhost:8000');
// Then refresh page
```

---

## 🎯 Recommended Testing Path

### Path A: Production API (Easiest - No Setup)

1. Use test-dashboard.html with production API
2. Test all features end-to-end
3. Use calculator for quick validation

### Path B: Local Backend (Advanced)

1. Fix backend environment
2. Start backend locally
3. Override API URL in browser
4. Test with local server

---

## 📋 What You Can Test Right Now

### Without Backend (Calculator Only)

✅ Advanced options math
✅ Quality multipliers (1.0x, 1.3x, 1.8x)
✅ Regional adjustments (0.85x - 1.35x)
✅ Profit/contingency calculations

### With Production API

✅ Auth gating
✅ Real quote generation
✅ Advanced options effect on real quotes
✅ Video upload
✅ Voice input
✅ Full mobile flow

---

## 🚀 Start Testing Now

1. **Open browser**: `http://localhost:8080/test-dashboard.html`
2. **Check status**: API should show "✅ Healthy"
3. **Test calculator**: Play with sliders in Test 2
4. **Test real flow**: Click "Mobile Quote" and generate

The test dashboard works perfectly with the production API - you don't need local backend running! 🎉
