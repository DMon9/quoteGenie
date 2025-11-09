(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', () => {
        try {
            const path = window.location.pathname.split('/').pop() || 'index.html';
            const isActive = (href) => {
                if (!href) return false;
                const target = href.split('/').pop();
                if (!target) return false;
                // Treat index.html and root as same
                if ((path === '' || path === 'index.html') && (target === '' || target === 'index.html')) return true;
                return path === target;
            };

            const desktopLinks = document.querySelectorAll('nav a[href]');
            desktopLinks.forEach(a => {
                if (isActive(a.getAttribute('href'))) {
                    a.classList.remove('text-gray-500', 'hover:text-gray-700');
                    a.classList.add('text-purple-600', 'font-medium');
                    a.setAttribute('aria-current', 'page');
                }
            });

            // Also try to highlight any mobile menu links
            const mobileLinks = document.querySelectorAll('#mobile-menu a[href]');
            mobileLinks.forEach(a => {
                if (isActive(a.getAttribute('href'))) {
                    a.classList.add('bg-purple-50', 'text-purple-600', 'font-medium');
                    a.setAttribute('aria-current', 'page');
                }
            });
        } catch (e) {
            console.warn('[nav] failed to set active link', e);
        }
    });
})();
