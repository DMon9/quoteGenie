# API Testing Script for EstimateGenie
# Tests authentication, payments, and quote generation

$BASE_URL = "http://localhost:8000"  # Change to https://quotegenie-api.fly.dev for production

Write-Host "EstimateGenie API Test Suite" -ForegroundColor Cyan
Write-Host "============================`n" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "[1/8] Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get
    Write-Host "✓ Health check passed" -ForegroundColor Green
    Write-Host "  Status: $($health.status)" -ForegroundColor Gray
}
catch {
    Write-Host "✗ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Register User
Write-Host "`n[2/8] Registering new user..." -ForegroundColor Yellow
$registerBody = @{
    email    = "test-$(Get-Random)@example.com"
    name     = "Test User"
    password = "TestPassword123!"
    plan     = "free"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/register" `
        -Method Post `
        -ContentType "application/json" `
        -Body $registerBody
    
    $token = $registerResponse.access_token
    $testEmail = ($registerBody | ConvertFrom-Json).email
    
    Write-Host "✓ User registered successfully" -ForegroundColor Green
    Write-Host "  Email: $testEmail" -ForegroundColor Gray
    Write-Host "  Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
}
catch {
    Write-Host "✗ Registration failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: Login
Write-Host "`n[3/8] Testing login..." -ForegroundColor Yellow
$loginBody = @{
    email    = $testEmail
    password = "TestPassword123!"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/login" `
        -Method Post `
        -ContentType "application/json" `
        -Body $loginBody
    
    Write-Host "✓ Login successful" -ForegroundColor Green
    Write-Host "  User: $($loginResponse.user.name)" -ForegroundColor Gray
    Write-Host "  Plan: $($loginResponse.user.plan)" -ForegroundColor Gray
}
catch {
    Write-Host "✗ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 4: Get User Profile
Write-Host "`n[4/8] Getting user profile..." -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    $profile = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/me" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✓ Profile retrieved" -ForegroundColor Green
    Write-Host "  Name: $($profile.name)" -ForegroundColor Gray
    Write-Host "  Email: $($profile.email)" -ForegroundColor Gray
    Write-Host "  Plan: $($profile.plan)" -ForegroundColor Gray
    Write-Host "  API Key: $($profile.api_key)" -ForegroundColor Gray
}
catch {
    Write-Host "✗ Profile retrieval failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 5: Get Usage Stats
Write-Host "`n[5/8] Checking usage statistics..." -ForegroundColor Yellow
try {
    $usage = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/usage" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✓ Usage stats retrieved" -ForegroundColor Green
    Write-Host "  Quotes used: $($usage.quotes_used) / $($usage.limits.quotes_per_month)" -ForegroundColor Gray
    Write-Host "  API calls: $($usage.api_calls_used) / $($usage.limits.api_calls_per_day)" -ForegroundColor Gray
    Write-Host "  Can generate quote: $($usage.can_generate_quote)" -ForegroundColor Gray
}
catch {
    Write-Host "✗ Usage stats failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Regenerate API Key
Write-Host "`n[6/8] Regenerating API key..." -ForegroundColor Yellow
try {
    $newKey = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/regenerate-key" `
        -Method Post `
        -Headers $headers
    
    Write-Host "✓ API key regenerated" -ForegroundColor Green
    Write-Host "  New API Key: $($newKey.api_key)" -ForegroundColor Gray
}
catch {
    Write-Host "✗ API key regeneration failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 7: Update Profile
Write-Host "`n[7/8] Updating profile..." -ForegroundColor Yellow
$updateBody = @{
    name = "Updated Test User"
} | ConvertTo-Json

try {
    $updateResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/update-profile" `
        -Method Put `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $updateBody
    
    Write-Host "✓ Profile updated" -ForegroundColor Green
    Write-Host "  Message: $($updateResponse.message)" -ForegroundColor Gray
}
catch {
    Write-Host "✗ Profile update failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 8: Quote Generation (if test image exists)
Write-Host "`n[8/8] Testing quote generation..." -ForegroundColor Yellow
$testImagePath = "test-image.jpg"

if (Test-Path $testImagePath) {
    try {
        # PowerShell multipart form-data is complex, using curl if available
        if (Get-Command curl -ErrorAction SilentlyContinue) {
            $curlOutput = curl -X POST "$BASE_URL/v1/quotes" `
                -H "Authorization: Bearer $token" `
                -F "file=@$testImagePath" `
                -F "project_type=bathroom" `
                -F "description=Test renovation" `
                -s
            
            $quoteResponse = $curlOutput | ConvertFrom-Json
            
            Write-Host "✓ Quote generated successfully" -ForegroundColor Green
            Write-Host "  Quote ID: $($quoteResponse.id)" -ForegroundColor Gray
            Write-Host "  Total Cost: `$$($quoteResponse.total_cost)" -ForegroundColor Gray
            Write-Host "  Timeline: $($quoteResponse.timeline)" -ForegroundColor Gray
            Write-Host "  Confidence: $($quoteResponse.confidence_score)%" -ForegroundColor Gray
        }
        else {
            Write-Host "⚠ curl not available, skipping quote test" -ForegroundColor Yellow
            Write-Host "  Install curl to test quote generation" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "✗ Quote generation failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "  This is expected if LLM/Vision services aren't configured" -ForegroundColor Gray
    }
}
else {
    Write-Host "⚠ Test image not found, skipping quote generation" -ForegroundColor Yellow
    Write-Host "  Create '$testImagePath' to test quote functionality" -ForegroundColor Gray
}

# Summary
Write-Host "`n=============================" -ForegroundColor Cyan
Write-Host "Test Suite Complete!" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Cyan
Write-Host "`nTest Account Created:" -ForegroundColor Yellow
Write-Host "  Email: $testEmail" -ForegroundColor White
Write-Host "  Password: TestPassword123!" -ForegroundColor White
Write-Host "  JWT Token: $($token.Substring(0, 30))..." -ForegroundColor White
Write-Host "`nYou can now:" -ForegroundColor Yellow
Write-Host "  - Login at: http://localhost:8000/login.html" -ForegroundColor White
Write-Host "  - View dashboard at: http://localhost:8000/dashboard.html" -ForegroundColor White
Write-Host "  - Use API key: $($newKey.api_key)" -ForegroundColor White
Write-Host "`n"

# Optional: Clean up test user
Write-Host "Delete test user? (y/n): " -ForegroundColor Yellow -NoNewline
$cleanup = Read-Host

if ($cleanup -eq "y") {
    try {
        $deleteResponse = Invoke-RestMethod -Uri "$BASE_URL/api/v1/auth/delete-account" `
            -Method Delete `
            -Headers $headers
        
        Write-Host "✓ Test user deleted" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Cleanup failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}
