# Multi-Model AI Deployment Guide

## What's New

Your backend now supports **multiple AI models** with automatic fallback:

1. **Google Gemini 2.0 Flash** - Fast, general-purpose (already configured ✅)
2. **OpenAI GPT-4o Vision** - Detailed analysis, complex reasoning  
3. **Anthropic Claude 3.5 Sonnet** - Precise measurements, technical analysis

### Features Added

- **Intelligent Fallback**: If one model fails, automatically tries the next
- **Model Selection API**: Users can choose their preferred AI model
- **Enhanced Analysis**: Better material lists, labor estimates, and cost breakdowns
- **Multiple Vision Models**: Get the best results from different AI providers

## Deployment Steps

### 1. Install New Dependencies on Fly.io

The backend now requires additional Python packages:

- `anthropic==0.40.0` - For Claude AI
- `openai==1.57.4` - For GPT-4 Vision

These are already in `requirements.txt` and will be installed during deployment.

### 2. Set API Keys (Optional)

To enable GPT-4 Vision and Claude, set their API keys:

```powershell
# For GPT-4 Vision (OpenAI)
fly secrets set OPENAI_API_KEY="your-openai-api-key-here" -a quotegenie-api

# For Claude (Anthropic)
fly secrets set ANTHROPIC_API_KEY="your-anthropic-api-key-here" -a quotegenie-api
```

**Note**: Without these keys, the system will use Gemini (already working) and fallback gracefully.

### 3. Deploy to Fly.io

```powershell
cd backend
fly deploy -a quotegenie-api
```

This will:

- Build a new Docker image with updated dependencies
- Deploy to Fly.io
- Restart the app with new features

### 4. Verify Deployment

```powershell
# Check health
Invoke-RestMethod -Uri "https://quotegenie-api.fly.dev/health"

# Check available models
Invoke-RestMethod -Uri "https://quotegenie-api.fly.dev/api/v1/models/available"

# Check model status
Invoke-RestMethod -Uri "https://quotegenie-api.fly.dev/api/v1/models/status"
```

### 5. Deploy Frontend to Cloudflare Pages

The frontend needs to be deployed to production. You have two options:

#### Option A: Git Integration (Recommended)

1. Push your code to GitHub:

   ```powershell
   git add .
   git commit -m "Add multi-model AI support and deployment ready"
   git push origin main
   ```

2. Connect to Cloudflare Pages:
   - Go to: <https://dash.cloudflare.com/> → Pages
   - Click "Create a project" → "Connect to Git"
   - Select your `quoteGenie` repository
   - Configure build settings:
     - **Build command**: (leave blank - static site)
     - **Build output directory**: `/`
     - **Root directory**: `/`
   - Click "Save and Deploy"

#### Option B: Direct Upload with Wrangler

```powershell
# Install Wrangler if not already installed
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy (from root directory)
wrangler pages deploy . --project-name=estimategenie
```

## API Changes

### New Endpoints

1. **GET /api/v1/models/available**
   - Returns list of available AI models
   - Response:

     ```json
     {
       "models": [
         {
           "id": "gemini",
           "name": "Google Gemini 2.0 Flash",
           "provider": "google",
           "capabilities": ["vision", "reasoning", "fast"],
           "best_for": "General purpose, fast responses"
         },
         {
           "id": "gpt4v",
           "name": "OpenAI GPT-4 Vision",
           "provider": "openai",
           "capabilities": ["vision", "reasoning", "detailed"],
           "best_for": "Detailed analysis, complex reasoning"
         },
         {
           "id": "claude",
           "name": "Anthropic Claude 3.5 Sonnet",
           "provider": "anthropic",
           "capabilities": ["vision", "reasoning", "precise"],
           "best_for": "Precise measurements, technical analysis"
         }
       ],
       "preferred": "auto"
     }
     ```

2. **GET /api/v1/models/status**
   - Returns detailed status of all AI services

### Updated Endpoints

**POST /v1/quotes** - Now accepts `model` parameter:

- `model=auto` (default) - Uses best available model with fallback
- `model=gemini` - Force use of Gemini
- `model=gpt4v` - Force use of GPT-4 Vision (if configured)
- `model=claude` - Force use of Claude (if configured)

## Environment Variables

Add these to Fly.io for full functionality:

```bash
# Required (already set)
GOOGLE_API_KEY=your-gemini-key
JWT_SECRET_KEY=your-jwt-secret

# Optional - for additional models
OPENAI_API_KEY=your-openai-key      # Enables GPT-4 Vision
ANTHROPIC_API_KEY=your-claude-key   # Enables Claude

# Optional - for payment features
STRIPE_SECRET_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# Model preferences
PREFERRED_MODEL=auto                 # Options: auto, gemini, gpt4v, claude
GEMINI_MODEL=gemini-2.0-flash-exp   # Specific Gemini model
GPT4V_MODEL=gpt-4o                   # Specific GPT model
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Specific Claude model
```

## Cost Considerations

Each AI model has different pricing:

- **Gemini 2.0 Flash**: ~$0.075 per 1M input tokens (cheapest)
- **GPT-4o Vision**: ~$2.50 per 1M input tokens
- **Claude 3.5 Sonnet**: ~$3.00 per 1M input tokens

**Recommendation**:

- Use Gemini for most requests (fast + cheap)
- Use GPT-4V or Claude for premium users or complex projects
- Set `PREFERRED_MODEL=gemini` to control costs

## Testing

After deployment, test with:

```powershell
# Test basic quote generation (uses default model)
$imageFile = "test-image.jpg"
$uri = "https://quotegenie-api.fly.dev/v1/quotes"
# ... (see TESTING_GUIDE.md for full examples)

# Test with specific model
# Add `model=gpt4v` to form data
```

## Troubleshooting

### "Model not available" error

- Check API keys are set: `fly secrets list -a quotegenie-api`
- Verify keys are valid (not placeholder values)
- Check model status endpoint

### Deployment fails

- Check flyctl is up to date: `fly version`
- Verify Dockerfile.fly exists
- Check fly.toml configuration

### Frontend not loading

- Clear browser cache
- Check Cloudflare Pages build logs
- Verify API URL in `assets/js/api-config.js`

## Next Steps

1. Deploy backend: `fly deploy -a quotegenie-api`
2. Set API keys (optional): `fly secrets set OPENAI_API_KEY=...`
3. Deploy frontend to Cloudflare Pages
4. Test end-to-end functionality
5. Monitor usage and costs in provider dashboards

---

For support or questions, check the logs:

```powershell
fly logs -a quotegenie-api
```
