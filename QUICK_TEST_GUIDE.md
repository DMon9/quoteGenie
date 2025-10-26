# Quick Site Functionality Test Guide

## ✅ Pre-Flight Check (30 seconds)

### 1. Backend Health
Open in browser or curl:
```
http://localhost:8001/health
```

**Expected:** Green JSON with all services `true`

### 2. Pricing Status
```
http://localhost:8001/v1/pricing/status
```

**Expected:**
```json
{
  "external_files": ["/app/pricing/materials_pricing_400.json"],
  "external_keys_count": 134,
  "total_materials_count": 143,
  "watsonx_enabled": true
}
```

### 3. Sample Price Lookup
```
http://localhost:8001/v1/pricing/lookup?key=lumber_2x4
```

**Expected:**
```json
{
  "key": "lumber_2x4",
  "source": "external-list",
  "price": 6.49,
  "unit": "piece"
}
```

---

## 🎨 Frontend Test (2 minutes)

### Open Test Page
```
http://localhost:8080/test-upload-v2.html
```

### Check Backend Indicators
Top of page should show:
- ✅ Backend: healthy
- ✅ LLM: Ready
- ✅ Vision: Ready

### Upload Test

1. **Select an image:**
   - Use any construction/renovation photo
   - Or screenshot of building materials
   - Or even a random photo (will estimate generically)

2. **Choose project type:**
   - Bathroom (good for tile/concrete/plumbing)
   - Kitchen (cabinets/countertops)
   - General (catch-all)

3. **Add description (optional):**
   ```
   "Small bathroom renovation with new tile floor and walls"
   ```

4. **Click "Generate AI Estimate"**
   - Wait 30-60 seconds
   - Watch for progress indicator

### Expected Results

**Success indicators:**
- ✅ Status turns green
- ✅ Quote ID displayed
- ✅ Total cost shows realistic amount
- ✅ Materials list populated
- ✅ Labor hours calculated
- ✅ Timeline shows days
- ✅ Work steps listed

**Sample output:**
```
Quote ID: quote_abc123
Total Cost: $5,234.50
  Materials: $3,850.00
  Labor: $900.00
  Markup: $484.50
Timeline: 2-4 days
Materials: 8 items
```

---

## 🔥 Hot-Reload Test (1 minute)

### Test Price Change Detection

1. **Get current price:**
   ```bash
   curl "http://localhost:8001/v1/pricing/lookup?key=lumber_2x4"
   # Returns: "price": 6.49
   ```

2. **Edit price list:**
   - Open `backend/pricing/materials_pricing_400.json`
   - Find first entry with lumber
   - Change `Final_Price_USD` from 6.49 to 7.99
   - **Save file**

3. **Wait or force reload:**
   ```bash
   # Option A: Wait 10 seconds for auto-reload
   sleep 10

   # Option B: Force immediate reload
   curl -X POST http://localhost:8001/v1/pricing/reload
   ```

4. **Verify change:**
   ```bash
   curl "http://localhost:8001/v1/pricing/lookup?key=lumber_2x4"
   # Should return: "price": 7.99
   ```

5. **Restore original:**
   - Change back to 6.49
   - Save and reload

---

## 🧪 Quick Smoke Tests

### Test 1: Minimal Quote
```bash
docker exec backend-api-1 python /app/smoke_test_quote.py
```

**Expected:** HTTP 200 with materials/labor/cost breakdown

### Test 2: E2E Realistic Quote
```bash
docker exec backend-api-1 python /app/test_e2e_quote.py
```

**Expected:** Full construction scene analysis with detailed output

### Test 3: Hot-Reload Verification
```bash
docker exec backend-api-1 python /app/test_hot_reload.py
```

**Expected:** Shows current pricing config and reload capability

---

## 📊 Dashboard Checks

### API Docs (Interactive)
```
http://localhost:8001/docs
```

Browse all endpoints, try test requests

### Root Endpoint
```
http://localhost:8001/
```

**Expected:**
```json
{
  "service": "EstimateGenie API",
  "status": "running",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

## ❌ Common Issues & Fixes

### Backend shows "Offline"
```bash
# Check container
docker ps | grep backend-api

# View logs
docker logs backend-api-1 --tail 50

# Restart if needed
docker compose -f backend/docker-compose.yml -f backend/docker-compose.override.yml restart
```

### Upload fails with CORS error
- Check browser console (F12)
- Verify ALLOW_ORIGINS in docker-compose.yml includes localhost:8080
- Hard refresh page (Ctrl+Shift+R)

### Pricing shows $0 or wrong amounts
```bash
# Check status
curl http://localhost:8001/v1/pricing/status

# Force reload
curl -X POST http://localhost:8001/v1/pricing/reload

# Check specific item
curl "http://localhost:8001/v1/pricing/lookup?key=concrete"
```

### LLM returns empty materials
- Check GOOGLE_API_KEY is set
- View container logs for Gemini errors
- Try with different image (more obvious construction content)

---

## ✅ Success Criteria

**All systems operational when:**
- [ ] Health endpoint returns all `true`
- [ ] Pricing status shows 134+ external keys
- [ ] Sample lookup returns external-list source
- [ ] Frontend shows 3 green badges
- [ ] Upload completes in < 60 seconds
- [ ] Quote has realistic materials/costs
- [ ] Hot-reload applies within 10 seconds
- [ ] Smoke tests pass

---

## 🎯 Quick Validation (10 seconds)

Run this one-liner:
```bash
curl -s http://localhost:8001/health | grep -q "healthy" && \
curl -s http://localhost:8001/v1/pricing/status | grep -q "external_keys_count" && \
echo "✅ ALL SYSTEMS GO" || echo "❌ CHECK LOGS"
```

**Expected:** `✅ ALL SYSTEMS GO`

---

## 📝 Notes

- Default reload interval: 10 seconds
- Max image size: ~10MB (configurable)
- Quote processing: 30-60 seconds typical
- Database: SQLite (local file)
- Price list format: JSON list with Material/Final_Price_USD/Unit_Type

**Last Updated:** 2025-10-26  
**Status:** All features operational and tested
