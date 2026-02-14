/**
 * Modal System - Shared modal and notification functions
 * Handles modal opening, closing, and toast notifications
 */

(function() {
    'use strict';

    // Global modal and toast functions
    function showNotification(message, type = 'success') {
        const toast = document.getElementById('toast-notification');
        const toastMessage = document.getElementById('toast-message');

        toastMessage.textContent = message;
        toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white z-[1000] ${type === 'success' ? 'bg-green-500' : 'bg-red-500'}`;

        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 10);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(0.5rem)';
        }, 3000);
    }

    function showWarningModal(title, message) {
        const overlay = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-inner-content');

        overlay.classList.remove('hidden');

        content.innerHTML = `
            <div class="p-8">
                <div class="flex items-center justify-center mb-6">
                    <div class="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center">
                        <svg class="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                        </svg>
                    </div>
                </div>
                <h2 class="text-2xl font-semibold text-gray-800 text-center mb-4">${title}</h2>
                <p class="text-gray-600 text-center mb-6">${message}</p>
                <div class="flex justify-center">
                    <button onclick="closeModal()" class="px-6 py-3 bg-gold-500 text-white rounded-lg hover:bg-gold-700 transition">
                        OK
                    </button>
                </div>
            </div>
        `;

        document.body.style.overflow = 'hidden';
    }

    function showConfirmModal(title, message) {
        return new Promise((resolve) => {
            const overlay = document.getElementById('modal-overlay');
            const content = document.getElementById('modal-inner-content');

            overlay.classList.remove('hidden');

            content.innerHTML = `
                <div class="p-8">
                    <div class="flex items-center justify-center mb-6">
                        <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                            <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                    </div>
                    <h2 class="text-2xl font-semibold text-gray-800 text-center mb-4">${title}</h2>
                    <p class="text-gray-600 text-center mb-6">${message}</p>
                    <div class="flex justify-center gap-3">
                        <button onclick="closeModal(); window._confirmResolve(false)" class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition">
                            Cancel
                        </button>
                        <button onclick="closeModal(); window._confirmResolve(true)" class="px-6 py-3 bg-gold-500 text-white rounded-lg hover:bg-gold-700 transition">
                            Confirm
                        </button>
                    </div>
                </div>
            `;

            window._confirmResolve = resolve;
            document.body.style.overflow = 'hidden';
        });
    }

    function openModal(url, isStatic = false, modalName = null) {
        const overlay = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-inner-content');

        overlay.classList.remove('hidden');

        if (isStatic && modalName) {
            const staticContent = getStaticModalContent(modalName);
            if (staticContent) {
                content.innerHTML = staticContent;
                return;
            }
        }

        content.innerHTML = '<div class="p-8 flex items-center justify-center"><div class="text-gray-500">Loading...</div></div>';

        fetch(url, {
            credentials: 'include',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            content.innerHTML = html;
            processModalScripts(content);
        })
        .catch(error => {
            content.innerHTML = '<div class="p-8"><p class="text-gray-600">Unable to load content. Please try again later.</p></div>';
        });

        document.body.style.overflow = 'hidden';
    }

    // Load content into an already-open modal
    window.loadModalContent = function(url) {
        const content = document.getElementById('modal-inner-content');

        content.innerHTML = '<div class="p-8 flex items-center justify-center"><div class="text-gray-500">Loading...</div></div>';

        fetch(url, {
            credentials: 'include',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            content.innerHTML = html;
            processModalScripts(content);
        })
        .catch(error => {
            content.innerHTML = '<div class="p-8"><p class="text-gray-600">Unable to load content. Please try again later.</p></div>';
        });
    };

    function closeModal(options = {}) {
        const overlay = document.getElementById('modal-overlay');
        const content = document.getElementById('modal-inner-content');

        // Check if we need to trigger page refresh or update
        if (options.refreshPage || window.refreshOnModalClose) {
            location.reload();
            return;
        }

        // Trigger custom event for page updates
        const event = new CustomEvent('modalClosed', {
            detail: {
                success: options.success || false,
                modalType: options.modalType || null,
                data: options.data || null
            }
        });
        document.dispatchEvent(event);

        overlay.classList.add('hidden');
        content.innerHTML = '';
        document.body.style.overflow = 'auto';

        window.refreshOnModalClose = false;
        window._confirmResolve = null;
    }

    function closeModalOverlay(event) {
        if (event.target.id === 'modal-overlay') {
            closeModal();
        }
    }

    function getStaticModalContent(modalName) {
        const businessName = document.body.dataset.businessName || 'Shampooches';
        const businessAddress = document.body.dataset.businessAddress || '';
        const businessPhone = document.body.dataset.businessPhone || '';
        const businessEmail = document.body.dataset.businessEmail || '';

        const staticContent = {
            about: `
                <div class="p-8">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-semibold text-gray-800">About ${businessName}</h2>
                        <button onclick="closeModal()" class="px-3 py-1 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="prose text-gray-600">
                        <p class="mb-4">${businessName} provides exceptional grooming services for dogs. Our certified groomers are passionate about making every dog look and feel their best.</p>
                        <p class="mb-4">We use premium, eco-friendly products and follow the highest standards of hygiene and safety. Your pets deserve the best care.</p>
                    </div>
                </div>
            `,
            contact: `
                <div class="p-8">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-semibold text-gray-800">Contact Us</h2>
                        <button onclick="closeModal()" class="px-3 py-1 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="space-y-4 text-gray-600">
                        ${businessAddress ? `
                        <div class="flex items-center">
                            <svg class="w-5 h-5 text-gold-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                            <span>${businessAddress}</span>
                        </div>
                        ` : ''}
                        ${businessPhone ? `
                        <div class="flex items-center">
                            <svg class="w-5 h-5 text-gold-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                            </svg>
                            <span>${businessPhone}</span>
                        </div>
                        ` : ''}
                        ${businessEmail ? `
                        <div class="flex items-center">
                            <svg class="w-5 h-5 text-gold-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                            <span>${businessEmail}</span>
                        </div>
                        ` : ''}
                        ${!businessPhone && !businessEmail && !businessAddress ? '<p class="text-gray-500 italic">Contact information not yet configured. Please contact the administrator.</p>' : ''}
                    </div>
                </div>
            `
        };

        return staticContent[modalName] || null;
    }

    function processModalScripts(container) {
        const scripts = container.querySelectorAll('script');
        const promises = [];

        scripts.forEach(oldScript => {
            const scriptSrc = oldScript.src;

            if (scriptSrc) {
                const promise = new Promise((resolve) => {
                    const newScript = document.createElement('script');
                    newScript.src = scriptSrc;
                    newScript.async = false;

                    newScript.onload = () => {
                        resolve();
                    };

                    newScript.onerror = () => {
                        console.error('[ModalUtils] Failed to load script:', scriptSrc);
                        resolve();
                    };

                    document.head.appendChild(newScript);
                });

                promises.push(promise);
                oldScript.remove();
            } else {
                // Inline script handling
                const scriptType = oldScript.getAttribute('type');
                const scriptId = oldScript.getAttribute('id');

                // Determine if this is executable JavaScript
                const jsTypes = ['text/javascript', 'module', 'application/javascript'];
                const isExecuteable = (!scriptId && (!scriptType || jsTypes.includes(scriptType)));

                if (!isExecuteable) {
                    // Non-executable (e.g., JSON data, templates) - keep in DOM for potential use
                    return; // Don't execute or remove
                }

                // Execute the inline script
                const scriptContent = oldScript.textContent || '';
                if (!scriptContent.trim()) {
                    oldScript.remove();
                    return;
                }

                try {
                    const newScript = document.createElement('script');
                    newScript.textContent = scriptContent;
                    newScript.type = scriptType || 'text/javascript';
                    newScript.async = false;
                    document.body.appendChild(newScript);
                    newScript.remove();
                } catch (error) {
                    console.error('[ModalUtils] Error executing inline script:', error);
                } finally {
                    oldScript.remove();
                }
            }
        });

        return Promise.all(promises).then(() => {
            if (typeof htmx !== 'undefined' && htmx.process) {
                htmx.process(container);
            }
        });
    }

    function getCsrfToken() {
        const token = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
        if (token) return token;

        const cookieValue = `; ${document.cookie}`;
        const parts = cookieValue.split(`; csrftoken=`);
        if (parts.length === 2) return parts.pop().split(';').shift();

        return '';
    }

    // Event delegation for modal buttons
    document.addEventListener('click', (e) => {
        const button = e.target.closest('[data-modal-url]');
        if (button) {
            e.preventDefault();
            const url = button.getAttribute('data-modal-url');
            const isStatic = button.getAttribute('data-modal-static') === 'true';
            const modalName = button.getAttribute('data-modal-name');

            openModal(url, isStatic, modalName);
        }
    });

    // Keyboard event handling
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });

    // Make functions globally available
    window.showNotification = showNotification;
    window.showWarningModal = showWarningModal;
    window.showConfirmModal = showConfirmModal;
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.closeModalOverlay = closeModalOverlay;
    window.getCSRFToken = getCsrfToken;

})();
