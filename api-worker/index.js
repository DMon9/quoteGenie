/**
 * Cloudflare Worker - EstimateGenie API Proxy
 * 
 * Routes API requests from the static frontend to the backend service.
 * Update BACKEND_URL after deploying backend to Render/Railway/Fly.io
 */

// Backend URL - update this after deploying backend
const BACKEND_URL = 'https://quotegenie-api.fly.dev'; // Local Docker backend (corrected port)
const ORCHESTRATOR_URL = 'https://quotegenie-api.fly.dev'; // Same backend for now

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }
    
    // Route requests
    if (url.pathname.startsWith('/api/orchestrate')) {
      return proxyToBackend(request, ORCHESTRATOR_URL, url.pathname.replace('/api', ''));
    }
    
    if (url.pathname.startsWith('/api/v1')) {
      return proxyToBackend(request, BACKEND_URL, url.pathname.replace('/api', ''));
    }
    
    if (url.pathname === '/api/health') {
      return healthCheck();
    }
    
    // For non-API requests, return 404 instead of intercepting
    return new Response('API endpoint not found', {
      status: 404,
      headers: { 'Content-Type': 'text/plain', ...corsHeaders }
    });
  }
};

async function proxyToBackend(request, backendUrl, path) {
  try {
    const url = new URL(path, backendUrl);
    
    // Copy search params
    const originalUrl = new URL(request.url);
    originalUrl.searchParams.forEach((value, key) => {
      url.searchParams.append(key, value);
    });
    
    // Forward request to backend
    const modifiedRequest = new Request(url.toString(), {
      method: request.method,
      headers: request.headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
    });
    
    const response = await fetch(modifiedRequest);
    
    // Add CORS headers to response
    const modifiedResponse = new Response(response.body, response);
    Object.entries(corsHeaders).forEach(([key, value]) => {
      modifiedResponse.headers.set(key, value);
    });
    
    return modifiedResponse;
    
  } catch (error) {
    return new Response(JSON.stringify({
      error: 'Backend proxy error',
      message: error.message,
      backend: backendUrl
    }), {
      status: 502,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
}

async function healthCheck() {
  const checks = {};
  
  // Check backend
  try {
    const response = await fetch(`${BACKEND_URL}/health`, { 
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    checks.backend = response.ok ? 'healthy' : 'unhealthy';
  } catch (e) {
    checks.backend = 'unreachable';
  }
  
  // Check orchestrator
  try {
    const response = await fetch(`${ORCHESTRATOR_URL}/`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    checks.orchestrator = response.ok ? 'healthy' : 'unhealthy';
  } catch (e) {
    checks.orchestrator = 'unreachable';
  }
  
  const allHealthy = Object.values(checks).every(v => v === 'healthy');
  
  return new Response(JSON.stringify({
    status: allHealthy ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    services: checks,
    urls: {
      backend: BACKEND_URL,
      orchestrator: ORCHESTRATOR_URL
    }
  }), {
    status: allHealthy ? 200 : 503,
    headers: { 'Content-Type': 'application/json', ...corsHeaders }
  });
}
