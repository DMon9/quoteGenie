/**
 * CTA Button Handler for EstimateGenie
 * Handles "Get Started Free", "Start Free Trial", and "Watch Demo" buttons
 */

(function (window) {
    'use strict';

    // Demo video modal HTML (will be injected on first use)
    const demoModalHTML = `
    <div id="demo-modal" class="fixed inset-0 bg-black bg-opacity-75 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
        <div class="flex justify-between items-center p-4 border-b">
          <h3 class="text-xl font-bold text-gray-900">EstimateGenie Demo</h3>
          <button id="close-demo-modal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="p-6">
          <div class="aspect-video bg-gray-100 rounded-lg overflow-hidden mb-4">
            <iframe id="demo-video" width="100%" height="100%" 
              src="" 
              frameborder="0" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowfullscreen>
            </iframe>
          </div>
          <div class="text-center">
            <p class="text-gray-600 mb-4">See how EstimateGenie transforms project estimation with AI</p>
            <button onclick="window.CTAButtons.closeDemo(); window.location.href='signup.html'" 
              class="px-6 py-3 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 transition">
              Get Started Free
            </button>
          </div>
        </div>
      </div>
    </div>
  `;

    // Demo video URL (you can replace this with your actual demo video)
    const DEMO_VIDEO_URL = 'https://www.youtube.com/embed/M7lc1UVf-VE?autoplay=1'; // Replace with actual video

    // Initialize modal on first call
    let modalInjected = false;

    function injectModal() {
        if (modalInjected) return;

        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = demoModalHTML;
        document.body.appendChild(modalContainer.firstElementChild);

        // Close button handler
        document.getElementById('close-demo-modal').addEventListener('click', closeDemo);

        // Click outside to close
        document.getElementById('demo-modal').addEventListener('click', function (e) {
            if (e.target.id === 'demo-modal') {
                closeDemo();
            }
        });

        // ESC key to close
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                closeDemo();
            }
        });

        modalInjected = true;
    }

    function openDemo() {
        injectModal();
        const modal = document.getElementById('demo-modal');
        const video = document.getElementById('demo-video');

        // Set video URL
        video.src = DEMO_VIDEO_URL;

        // Show modal
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeDemo() {
        const modal = document.getElementById('demo-modal');
        const video = document.getElementById('demo-video');

        if (modal && video) {
            // Stop video
            video.src = '';

            // Hide modal
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }

    function redirectToSignup() {
        window.location.href = 'signup.html';
    }

    function redirectToLogin() {
        window.location.href = 'login.html';
    }

    function redirectToDashboard() {
        window.location.href = 'dashboard-new.html';
    }

    // Check if user is logged in
    function isLoggedIn() {
        return !!(localStorage.getItem('auth_token') || localStorage.getItem('api_key'));
    }

    // Auto-wire buttons on page load
    function autoWireButtons() {
        // Get Started / Start Free Trial buttons
        const signupButtons = document.querySelectorAll(
            'button:not([data-cta-wired]), a:not([data-cta-wired])'
        );

        signupButtons.forEach(button => {
            const text = button.textContent.trim();

            // Signup buttons
            if (text.includes('Get Started') ||
                text.includes('Start Free') ||
                text.includes('Try Free') ||
                text.includes('Sign Up')) {
                button.setAttribute('data-cta-wired', 'true');
                button.style.cursor = 'pointer';
                button.addEventListener('click', function (e) {
                    e.preventDefault();
                    if (isLoggedIn()) {
                        redirectToDashboard();
                    } else {
                        redirectToSignup();
                    }
                });
            }

            // Login buttons
            if (text.includes('Log In') || text.includes('Sign In')) {
                button.setAttribute('data-cta-wired', 'true');
                button.style.cursor = 'pointer';
                button.addEventListener('click', function (e) {
                    e.preventDefault();
                    if (isLoggedIn()) {
                        redirectToDashboard();
                    } else {
                        redirectToLogin();
                    }
                });
            }

            // Watch Demo buttons
            if (text.includes('Watch Demo')) {
                button.setAttribute('data-cta-wired', 'true');
                button.style.cursor = 'pointer';
                button.addEventListener('click', function (e) {
                    e.preventDefault();
                    openDemo();
                });
            }
        });
    }

    // Export public API
    window.CTAButtons = {
        openDemo: openDemo,
        closeDemo: closeDemo,
        redirectToSignup: redirectToSignup,
        redirectToLogin: redirectToLogin,
        redirectToDashboard: redirectToDashboard,
        isLoggedIn: isLoggedIn
    };

    // Auto-wire on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoWireButtons);
    } else {
        autoWireButtons();
    }

    console.log('[CTA Buttons] Initialized - buttons auto-wired');

})(window);
