/**
 * Centralized API Configuration for EstimateGenie
 * 
 * Features:
 * - Single source of truth for API endpoints
 * - URL parameter override: ?api=http://localhost:8000
 * - localStorage override: localStorage.setItem('API_BASE_URL', 'https://...')
 * - Environment detection (local vs production)
 */

(function (window) {
  'use strict';

  // Default production API endpoint
  const DEFAULT_API_BASE = 'https://quotegenie-api.fly.dev';

  // Detect if running locally
  const isLocalhost = window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.hostname === '';

  /**
   * Get API base URL with override support
   * Priority: URL param > localStorage > default
   */
  function getApiBase() {
    // 1. Check URL parameter (?api=...)
    const urlParams = new URLSearchParams(window.location.search);
    const urlOverride = urlParams.get('api');
    if (urlOverride) {
      console.log('[API Config] Using URL override:', urlOverride);
      return urlOverride;
    }

    // 2. Check localStorage
    const localOverride = localStorage.getItem('API_BASE_URL');
    if (localOverride) {
      console.log('[API Config] Using localStorage override:', localOverride);
      return localOverride;
    }

    // 3. Use production Fly.io backend (even on localhost for testing)
    console.log('[API Config] Using production Fly.io backend:', DEFAULT_API_BASE);
    return DEFAULT_API_BASE;
  }

  // Global API configuration object
  window.ApiConfig = {
    // Base URL (without trailing slash)
    baseUrl: getApiBase(),

    // Helper to build full endpoint URLs
    url: function (path) {
      const safePath = typeof path === 'string' ? path.trim() : '';
      if (!safePath) {
        return this.baseUrl;
      }
      const cleanPath = safePath.startsWith('/') ? safePath : '/' + safePath;
      return this.baseUrl + cleanPath;
    },

    // Common endpoints
    endpoints: {
      // Health & Docs
      health: '/health',
      docs: '/docs',

      // Auth
      register: '/api/v1/auth/register',
      login: '/api/v1/auth/login',
      me: '/api/v1/auth/me',
      usage: '/api/v1/auth/usage',
      updateProfile: '/api/v1/auth/update-profile',
      changePassword: '/api/v1/auth/change-password',
      regenerateKey: '/api/v1/auth/regenerate-key',
      deleteAccount: '/api/v1/auth/delete-account',

      // Payment
      createPortalSession: '/api/v1/payment/create-portal-session',
      stripeWebhook: '/api/v1/webhooks/stripe',

      // Quotes
      quotes: '/v1/quotes',
      quote: function (id) { return `/v1/quotes/${id}`; }
    },

    // Fetch wrapper with automatic auth header injection
    fetch: async function (endpoint, options = {}) {
      const endpointStr = typeof endpoint === 'string' ? endpoint : '';
      const isAbsolute = endpointStr.startsWith('http://') || endpointStr.startsWith('https://') || endpointStr.startsWith('//');
      const url = isAbsolute ? endpointStr : this.url(endpointStr);

      // Auto-inject auth token if available
      const token = localStorage.getItem('auth_token');
      const apiKey = localStorage.getItem('api_key');

      const headers = {
        'Content-Type': 'application/json',
        ...options.headers
      };

      if (token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${token}`;
      } else if (apiKey && !headers['X-API-Key']) {
        headers['X-API-Key'] = apiKey;
      }

      return fetch(url, {
        ...options,
        headers
      });
    },

    // Update base URL (persists to localStorage)
    setBaseUrl: function (newBaseUrl) {
      console.log('[API Config] Setting base URL to:', newBaseUrl);
      this.baseUrl = newBaseUrl;
      localStorage.setItem('API_BASE_URL', newBaseUrl);
    },

    // Reset to default (clears localStorage)
    reset: function () {
      console.log('[API Config] Resetting to default');
      localStorage.removeItem('API_BASE_URL');
      this.baseUrl = getApiBase();
    },

    // Check if API is reachable
    testConnection: async function () {
      try {
        const response = await fetch(this.url('/health'), {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        });
        const healthy = response.ok;
        console.log('[API Config] Health check:', healthy ? 'OK' : 'FAIL', response.status);
        return healthy;
      } catch (error) {
        console.error('[API Config] Connection test failed:', error.message);
        return false;
      }
    }
  };

  // Convenience: expose endpoints directly
  window.API = window.ApiConfig.endpoints;

  // Log configuration on load
  console.log('[API Config] Initialized with base URL:', window.ApiConfig.baseUrl);
  console.log('[API Config] Override via: ?api=URL or localStorage.setItem("API_BASE_URL", "URL")');

})(window);
