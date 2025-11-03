# Testing Guide - New Features

## Overview

This guide covers testing for the newly implemented features:

1. Two-step mobile quote flow with auth gating
2. Advanced quote options (quality, contingency, profit, region)
3. Video upload with first-frame extraction
4. Voice-to-text description input

---

## Prerequisites

### Backend Setup

1. Ensure backend is running:

   ```bash
   cd backend
   python app.py
   ```

   Should see: `Application startup complete`

2. Health check:

   ```bash
   curl.exe https://api.estimategenie.net/health
   ```

   Should return HTTP 200 with `"status": "healthy"`

### Frontend Access

- Production: <https://www.estimategenie.net/mobile-index.html>
- Local: Open `mobile-index.html` in browser (with API override if needed)

### Authentication

You'll need either:

- JWT token: Sign up/login and check `localStorage['auth_token']`
- API key: Check `localStorage['api_key']` after signup

---

## Test Suite

### 1. Auth Gating (Mobile Quote Flow)

**Test Case 1.1: No Auth - Blocked Generation**

1. Open mobile-index.html in incognito/private window (no saved auth)
2. Select an image file
3. Verify:
   - ✅ Preview appears with filename/size
   - ✅ "Generate Quote" button is **disabled**
   - ✅ Yellow auth hint appears: "Sign in to generate quotes"
   - ✅ Links to login.html and signup.html are present

**Test Case 1.2: With Auth - Enabled Generation**

1. Open login.html and sign in (or use existing session)
2. Navigate to mobile-index.html
3. Select an image file
4. Verify:
   - ✅ Preview appears
   - ✅ "Generate Quote" button is **enabled** (not grayed out)
   - ✅ No auth warning appears
   - ✅ Clicking "Generate Quote" starts processing

**Test Case 1.3: Auth Token Validation**

```javascript
// In browser console on mobile-index.html:
localStorage.setItem('auth_token', 'invalid_token');
// Reload page, select file
// Should still be blocked (backend validates token)
```

---

### 2. Advanced Quote Options

**Test Case 2.1: Baseline (Standard/Default)**

1. Login and navigate to mobile-index.html
2. Upload: `test-images/bathroom.jpg` (or any bathroom image)
3. Project Type: "Bathroom Renovation"
4. Description: "Standard bathroom tile work"
5. **Keep Advanced Options collapsed** (use defaults)
6. Click "Generate Quote"
7. Note results:
   - Total Cost: `$_____`
   - Materials: `$_____`
   - Labor: `$_____`
   - Profit: `$_____` (should be ~15% of subtotal)
   - Contingency: `$0` (default is 0%)

**Test Case 2.2: Premium Quality**

1. Same image/project
2. Expand "Advanced options"
3. Material Quality: **Premium**
4. Keep other options default
5. Generate Quote
6. Verify:
   - ✅ Materials cost is **~30% higher** than Test 2.1
   - ✅ Labor cost is **same** as Test 2.1
   - ✅ Total is higher due to increased materials

**Test Case 2.3: Luxury Quality**

1. Same setup, Material Quality: **Luxury**
2. Verify:
   - ✅ Materials cost is **~80% higher** than baseline
   - ✅ Labor unchanged
   - ✅ Significant total increase

**Test Case 2.4: Contingency Buffer**

1. Standard quality
2. Contingency: **10%**
3. Verify:
   - ✅ Contingency field shows ~10% of (materials + labor)
   - ✅ Total includes this buffer

**Test Case 2.5: Higher Profit Margin**

1. Standard quality, 0% contingency
2. Profit: **25%**
3. Verify:
   - ✅ Profit field shows ~25% of (materials + labor)
   - ✅ Total includes increased margin

**Test Case 2.6: Regional Adjustment - West Coast**

1. Standard quality, 15% profit, 0% contingency
2. Region: **West**
3. Verify:
   - ✅ Labor cost is **~35% higher** than baseline
   - ✅ Materials unchanged
   - ✅ Total reflects higher labor rate

**Test Case 2.7: Regional Adjustment - South**

1. Region: **South**
2. Verify:
   - ✅ Labor cost is **~15% lower** than baseline
   - ✅ More affordable quote

**Test Case 2.8: Combined Max Settings**

1. Material Quality: **Luxury**
2. Contingency: **30%**
3. Profit: **50%**
4. Region: **West**
5. Verify:
   - ✅ Total is **significantly higher** than baseline (2-3x)
   - ✅ All breakdown fields are populated
   - ✅ Math adds up: Total = Materials + Labor + Profit + Contingency

**Expected Calculation:**

```
Base Materials: $350
Base Labor: $800
─────────────────
Adjusted Materials (1.8x): $630
Adjusted Labor (1.35x): $1,080
Subtotal: $1,710
Profit (50%): $855
Contingency (30%): $513
─────────────────
Total: $3,078
```

---

### 3. Video Upload & First-Frame Extraction

**Test Case 3.1: Video Upload**

1. Login to mobile-index.html
2. Click file upload
3. Select a video file (.mp4, .mov, .avi)
4. Verify:
   - ✅ File is accepted (no "Please upload an image" error)
   - ✅ Preview shows filename/size
   - ✅ No preview thumbnail (expected for video)
   - ✅ "Generate Quote" button is enabled

**Test Case 3.2: Video Processing**

1. Continue from Test 3.1
2. Click "Generate Quote"
3. Watch console (F12) for logs
4. Verify:
   - ✅ No errors during frame extraction
   - ✅ Progress animation runs
   - ✅ Quote generates successfully
   - ✅ Results appear (backend received JPEG frame)

**Test Case 3.3: Video Frame Quality**

1. Use a short construction/renovation video
2. Generate quote
3. Check if detected materials match video content
4. Verify frame extraction captured useful data

---

### 4. Voice-to-Text Description

**Test Case 4.1: Voice Input Availability**

1. Open mobile-index.html
2. Look for microphone icon near "Description" field
3. Verify:
   - ✅ Mic button is visible (if browser supports Web Speech API)
   - ✅ Mic button is hidden in unsupported browsers (Firefox, older Safari)

**Test Case 4.2: Voice Recording**

1. Click the microphone button
2. Verify:
   - ✅ Status changes to "Listening..."
   - ✅ Browser prompts for microphone permission (if first time)

**Test Case 4.3: Voice Transcription**

1. While listening, speak:
   > "Install new tile in master bathroom shower. Include waterproofing membrane and premium fixtures."
2. Stop speaking (or click mic again)
3. Verify:
   - ✅ Text appears in Description field
   - ✅ Transcription is accurate
   - ✅ Status clears after completion

**Test Case 4.4: Append Mode**

1. Type in Description: "Main floor bathroom"
2. Click mic and say: "with walk-in shower"
3. Verify:
   - ✅ New text is **appended** (not replaced)
   - ✅ Final text: "Main floor bathroom with walk-in shower"

---

### 5. Complete End-to-End Flow

**Test Case 5.1: Full Workflow - Standard**

1. **Start fresh**: Logout and clear localStorage
2. **Sign up**: Create new account at signup.html
3. **Verify redirect**: Should land on dashboard-new.html
4. **Navigate**: Click "Mobile" or go to mobile-index.html
5. **Upload**: Select bathroom image
6. **Describe**: Type or use voice: "Tile shower installation"
7. **Project**: Select "Bathroom Renovation"
8. **Options**: Expand and set:
   - Quality: Standard
   - Contingency: 5%
   - Profit: 15%
   - Region: Midwest
9. **Generate**: Click "Generate Quote"
10. **Wait**: Watch progress animation
11. **Review**: Check results:
    - ✅ Total cost displayed
    - ✅ 4-column breakdown (Materials, Labor, Profit, Contingency)
    - ✅ Timeline (days/hours)
    - ✅ Materials list (5 items preview)
12. **Actions**: Test buttons:
    - ✅ Download PDF (may not be implemented yet)
    - ✅ Share Quote (may not be implemented yet)
    - ✅ **New Quote**: Clears form and scrolls to top

**Test Case 5.2: Full Workflow - Premium**

1. Same flow, but set Quality: **Premium**, Contingency: **10%**, Region: **Northeast**
2. Verify quote reflects higher costs

**Test Case 5.3: Reset Flow**

1. After generating a quote, click "New Quote"
2. Verify:
   - ✅ Results section hidden
   - ✅ Preview cleared
   - ✅ Description field cleared
   - ✅ "Generate Quote" button disabled
   - ✅ Scrolled back to upload area

---

## Backend Unit Tests

### Run Estimation Tests

```powershell
cd backend
python test_advanced_options.py
```

**Expected Output:**

```
============================================================
Testing Advanced Options
============================================================

1. BASELINE (Standard quality, 15% profit, midwest)
   Total: $1,155.00
   Materials: $410.00
   Labor: $880.00
   Profit: $132.00
   Contingency: $0.00

2. PREMIUM QUALITY (1.3x material multiplier)
   Total: $1,278.00
   Materials: $533.00 (was $410.00)
   Material increase: $123.00 (~30% expected)
   ...

9. OPTIONS TRACKING
   Options applied: {
       "quality": "luxury",
       "contingency_pct": 20.0,
       "profit_pct": 30.0,
       "region": "west"
   }

============================================================
All tests completed!
============================================================
```

---

## API Testing (curl)

### Test 1: Baseline Quote

```bash
curl.exe -X POST https://api.estimategenie.net/v1/quotes ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  -F "file=@test-images/bathroom.jpg" ^
  -F "project_type=bathroom" ^
  -F "description=Standard tile work"
```

### Test 2: Advanced Options Quote

```bash
curl.exe -X POST https://api.estimategenie.net/v1/quotes ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  -F "file=@test-images/bathroom.jpg" ^
  -F "project_type=bathroom" ^
  -F "description=Premium tile work" ^
  -F "options={\"quality\":\"premium\",\"contingency_pct\":10,\"profit_pct\":20,\"region\":\"west\"}"
```

**Expected Response:**

```json
{
  "id": "quote_abc123def456",
  "status": "completed",
  "total_cost": {
    "currency": "USD",
    "amount": 1850.50,
    "breakdown": {
      "materials": 533.00,
      "labor": 1188.00,
      "profit": 344.20,
      "contingency": 172.10
    }
  },
  "options_applied": {
    "quality": "premium",
    "contingency_pct": 10.0,
    "profit_pct": 20.0,
    "region": "west"
  },
  "materials": [...],
  "labor": [...],
  "timeline": {...}
}
```

---

## Browser Console Testing

### Check Auth State

```javascript
// Open console (F12) on mobile-index.html
console.log('Token:', localStorage.getItem('auth_token'));
console.log('API Key:', localStorage.getItem('api_key'));

// Test ApiConfig
console.log('API Base:', ApiConfig.baseUrl);
console.log('Quotes URL:', ApiConfig.url(API.quotes));

// Test connection
ApiConfig.testConnection().then(ok => console.log('API reachable:', ok));
```

### Test Options Submission

```javascript
// Manually trigger a quote with specific options
const testQuote = {
  quality: 'luxury',
  contingency_pct: 20,
  profit_pct: 30,
  region: 'west'
};
console.log('Options JSON:', JSON.stringify(testQuote));
```

---

## Known Limitations & Future Work

### Not Yet Implemented

- ❌ PDF Download (button present but not functional)
- ❌ Share Quote (button present but not functional)
- ❌ Navigation/tab stability across pages
- ❌ Video thumbnail preview (shows filename only)

### Browser Compatibility

- Voice input: Chrome/Edge only (Web Speech API)
- Video upload: All modern browsers
- Auth flow: All browsers

### Performance

- Large videos (>100MB) may take longer to extract frame
- Voice recognition requires internet connection
- First quote generation may be slower (cold start)

---

## Bug Reporting Template

If you find issues during testing, report using this format:

**Feature**: [e.g., Video Upload]
**Browser**: [Chrome 119, Edge 120, etc.]
**Steps to Reproduce**:

1. ...
2. ...

**Expected**: ...
**Actual**: ...
**Console Errors**: [paste any errors from F12 console]
**Screenshots**: [if applicable]

---

## Success Criteria

✅ All auth gating tests pass
✅ Advanced options affect calculations correctly
✅ Video uploads convert to images successfully
✅ Voice input appends to description
✅ Reset flow clears state properly
✅ Backend unit tests pass
✅ API returns `options_applied` in response
✅ Mobile UI displays 4-column breakdown

---

## Next Steps After Testing

1. Fix any bugs discovered
2. Implement PDF download feature
3. Add share quote functionality
4. Stabilize navigation across pages
5. Add video thumbnail preview
6. Optimize performance for large files
7. Add more comprehensive error handling
