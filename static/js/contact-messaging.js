/**
 * Contact Messaging JavaScript Module
 *
 * Handles the messaging interface for customers to communicate with staff.
 * Features:
 * - Thread selection and message loading
 * - Sending messages
 * - Real-time polling for active viewers and typers
 * - New thread creation
 */

(function() {
    'use strict';

    // Capture reference to existing showNotification (from modal.js) before we overwrite it
    const originalShowNotification = window.showNotification;

    let currentThreadId = null;
    let pollingInterval = null;
    let messagePollingInterval = null;
    let typingTimeout = null;
    let csrfToken = null;

    // Detect if we're in staff context (staff contact page)
    function isStaffContext() {
        return window.location.pathname === '/contact/staff/';
    }

    // Get CSRF token
    function getCSRFToken() {
        if (!csrfToken) {
            csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        }
        return csrfToken;
    }

    // Helper function to safely fetch and parse JSON
    async function fetchJSON(url, options = {}) {
        const response = await fetch(url, {
            ...options,
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                ...(options.headers || {}),
            },
        });

        // Check if response is JSON before parsing
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error(`Server error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    // ========================

    // ========================
    // Modal Functions
    // ========================

    function openNewThreadModal() {
        const modal = document.getElementById('new-thread-modal');
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeNewThreadModal() {
        const modal = document.getElementById('new-thread-modal');
        modal.classList.add('hidden');
        document.body.style.overflow = '';
        document.getElementById('new-thread-form').reset();
    }

    // ========================
    // Thread Functions
    // ========================

    function selectThread(threadId) {
        currentThreadId = threadId;

        // Update UI
        document.getElementById('empty-state').classList.add('hidden');
        document.getElementById('thread-header').classList.remove('hidden');
        document.getElementById('messages-list').classList.remove('hidden');
        document.getElementById('message-input-area').classList.remove('hidden');

        // Clear message list
        const messagesList = document.getElementById('messages-list');
        messagesList.innerHTML = '<div class="text-center text-gray-500 py-8">Loading messages...</div>';

        // Load messages
        loadMessages(threadId);

        // Start polling for status
        startStatusPolling(threadId);
    }

    async function loadMessages(threadId) {
        try {
            // Use the correct endpoint based on user context
            const endpoint = isStaffContext()
                ? `/api/contact/staff/threads/${threadId}/messages/`
                : `/api/contact/threads/${threadId}/messages/`;

            const data = await fetchJSON(endpoint, {
                method: 'GET',
            });

            if (data.success) {
                renderMessages(data.data.messages, data.data.subject);
            } else {
                showNotification('error', data.message || 'Failed to load messages');
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            showNotification('error', 'Failed to load messages');
        }
    }

    function renderMessages(messages, subject) {
        const messagesList = document.getElementById('messages-list');
        const threadSubject = document.getElementById('thread-subject');

        threadSubject.textContent = subject;
        messagesList.innerHTML = '';

        if (messages.length === 0) {
            messagesList.innerHTML = '<p class="text-center text-gray-500 py-8">No messages yet. Be the first to say hello!</p>';
            return;
        }

        messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            const currentUsername = document.querySelector('meta[name="current-username"]')?.content;
            const isOwnMessage = msg.sender === currentUsername;

            msgDiv.className = `flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`;

            msgDiv.innerHTML = `
                <div class="max-w-[80%] ${isOwnMessage ? 'bg-gold-500 text-white' : 'bg-gray-100 text-gray-800'} px-4 py-2 rounded-lg">
                    <p class="text-sm font-medium mb-1 ${isOwnMessage ? 'text-gold-100' : 'text-gold-700'}">
                        ${msg.sender} ${isOwnMessage ? '(You)' : ''}
                    </p>
                    <p class="whitespace-pre-wrap break-words">${escapeHtml(msg.content)}</p>
                    <p class="text-xs ${isOwnMessage ? 'text-gold-200' : 'text-gray-500'} mt-1">
                        ${formatMessageTime(msg.created_at)}
                    </p>
                </div>
            `;

            messagesList.appendChild(msgDiv);
        });

        // Scroll to bottom
        messagesList.scrollTop = messagesList.scrollHeight;
    }

    // ========================
    // Message Functions
    // ========================

    async function sendMessage(event) {
        event.preventDefault();

        const form = event.target;
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();

        if (!message || !currentThreadId) return;

        // Disable form
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';

        try {
            const data = await fetchJSON(`/api/contact/threads/${currentThreadId}/send/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `message=${encodeURIComponent(message)}`,
            });

            if (data.success) {
                messageInput.value = '';
                // Reload messages
                await loadMessages(currentThreadId);
                stopTyping();
            } else {
                showNotification('error', data.message || 'Failed to send message');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            showNotification('error', 'Failed to send message');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send';
        }
    }

    // ========================
    // New Thread Functions
    // ========================

    async function createThread(event) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);

        // Disable submit button
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';

        try {
            const data = await fetchJSON('/api/contact/threads/create/', {
                method: 'POST',
                body: formData,
            });

            if (data.success) {
                closeNewThreadModal();
                // Reload page to show new thread
                window.location.reload();
            } else {
                showNotification('error', data.message || 'Failed to create conversation');
            }
        } catch (error) {
            console.error('Error creating thread:', error);
            showNotification('error', 'Failed to create conversation');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Start Conversation';
        }
    }

    // ========================
    // Polling Functions
    // ========================

    // Debugging helper
    function debugLog(category, message, data = null) {
        const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
        const prefix = `[${timestamp}] [Messaging Polling]`;
        console.log(`${prefix} [${category}]`, message);
        if (data !== null) {
            console.log(`${prefix} Data:`, data);
        }
    }

    function startStatusPolling(threadId) {
        debugLog('polling', 'Starting status polling for thread', { threadId });

        // Update currentThreadId for use by stopPolling
        currentThreadId = threadId;

        // Clear existing intervals
        stopPolling();

        // Poll for status (viewers and typers) every 3 seconds
        debugLog('polling', 'Setting up status interval (3s) and message interval (5s)');
        pollingInterval = setInterval(() => {
            checkThreadStatus(threadId);
        }, 3000);

        // Poll for new messages every 5 seconds
        messagePollingInterval = setInterval(() => {
            loadMessages(threadId);
        }, 5000);

        debugLog('polling', 'Polling intervals established', {
            statusInterval: 3000,
            messageInterval: 5000
        });
    }

    function stopPolling() {
        debugLog('polling', 'Stopping polling');
        if (pollingInterval) {
            debugLog('polling', 'Clearing status polling interval');
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
        if (messagePollingInterval) {
            debugLog('polling', 'Clearing message polling interval');
            clearInterval(messagePollingInterval);
            messagePollingInterval = null;
        }

        // Update view status
        if (currentThreadId) {
            debugLog('polling', 'Updating thread view status before stopping', { threadId: currentThreadId });
            updateThreadView(currentThreadId);
        }

        // Stop typing
        if (currentThreadId) {
            debugLog('polling', 'Stopping typing indicator', { threadId: currentThreadId });
            stopTyping();
        }

        debugLog('polling', 'Polling stopped successfully');
    }

    async function checkThreadStatus(threadId) {
        try {
            const data = await fetchJSON(`/api/contact/threads/${threadId}/status/`, {
                method: 'GET',
            });

            if (data.success) {
                updateViewers(data.data.active_viewers);
                updateTypers(data.data.active_typers);
                updateThreadView(threadId);
            }
        } catch (error) {
            console.error('Error checking thread status:', error);
        }
    }

    async function updateThreadView(threadId) {
        try {
            await fetchJSON(`/api/contact/threads/${threadId}/update-view/`, {
                method: 'GET',
            });
        } catch (error) {
            console.error('Error updating thread view:', error);
        }
    }

    function updateViewers(viewers) {
        const viewersEl = document.getElementById('active-viewers');

        if (!viewersEl) return;

        if (viewers.length === 0) {
            viewersEl.textContent = '';
        } else {
            const viewerNames = viewers.map(v => v.username).join(', ');
            viewersEl.innerHTML = `<span class="text-green-600 font-medium">● Viewers:</span> ${viewerNames}`;
        }
    }

    function updateTypers(typers) {
        const typingIndicator = document.getElementById('typing-indicator');

        if (!typingIndicator) return;

        if (typers.length === 0) {
            typingIndicator.classList.add('hidden');
        } else {
            const typerNames = typers.map(t => t.username).join(', ');
            typingIndicator.textContent = `${typerNames} ${typers.length === 1 ? 'is' : 'are'} typing...`;
            typingIndicator.classList.remove('hidden');
        }
    }

    // ========================
    // Typing Functions
    // ========================

    function handleTyping() {
        if (!currentThreadId) return;

        // Send typing indicator
        setTypingIndicator(currentThreadId, true);

        // Clear existing timeout
        if (typingTimeout) {
            clearTimeout(typingTimeout);
        }

        // Clear typing indicator after 3 seconds of no typing
        typingTimeout = setTimeout(() => {
            stopTyping();
        }, 3000);
    }

    async function setTypingIndicator(threadId, isTyping) {
        try {
            await fetchJSON(`/api/contact/threads/${threadId}/typing/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `is_typing=${isTyping}`,
            });
        } catch (error) {
            console.error('Error setting typing indicator:', error);
        }
    }

    function stopTyping() {
        if (currentThreadId) {
            setTypingIndicator(currentThreadId, false);
        }
    }

    // ========================
    // Utility Functions
    // ========================

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatMessageTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diff = now - date;

        // Less than 1 minute
        if (diff < 60000) {
            return 'Just now';
        }

        // Less than 1 hour
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes} min ago`;
        }

        // Less than 1 day
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours} hr ago`;
        }

        // More than 1 day
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
        });
    }

    function showNotification(type, message) {
        // Use the existing showNotification function from modal.js if available
        // modal.js expects (message, type), so we need to swap parameters
        if (typeof originalShowNotification === 'function') {
            originalShowNotification(message, type);
        } else {
            alert(message);
        }
    }

    // ========================
    // Event Listeners
    // ========================

    document.addEventListener('DOMContentLoaded', function() {
        // New thread form
        const newThreadForm = document.getElementById('new-thread-form');
        if (newThreadForm) {
            newThreadForm.addEventListener('submit', createThread);
        }

        // Message form
        const messageForm = document.getElementById('message-form');
        if (messageForm) {
            messageForm.addEventListener('submit', sendMessage);

            // Typing indicator
            const messageInput = document.getElementById('message-input');
            if (messageInput) {
                messageInput.addEventListener('input', handleTyping);
            }
        }

        // Close modal on outside click
        const newThreadModal = document.getElementById('new-thread-modal');
        if (newThreadModal) {
            newThreadModal.addEventListener('click', function(event) {
                if (event.target === newThreadModal) {
                    closeNewThreadModal();
                }
            });
        }

        // Stop polling when page is hidden
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopPolling();
            } else if (currentThreadId) {
                startStatusPolling(currentThreadId);
                loadMessages(currentThreadId);
            }
        });

        // Stop polling on page unload
        window.addEventListener('beforeunload', function() {
            stopPolling();
        });
    });

    // Make functions globally accessible
    window.contactMessaging = {
        openNewThreadModal: openNewThreadModal,
        closeNewThreadModal: closeNewThreadModal,
        selectThread: selectThread,
    };

    // Also expose functions directly for onclick handlers in templates
    window.openNewThreadModal = openNewThreadModal;
    window.closeNewThreadModal = closeNewThreadModal;
    window.selectThread = selectThread;
    window.getCSRFToken = getCSRFToken;
    // Expose utility functions for use in inline scripts
    window.formatMessageTime = formatMessageTime;
    window.escapeHtml = escapeHtml;
    // Expose polling functions for staff contact page
    window.startStatusPolling = startStatusPolling;
    window.stopPolling = stopPolling;
    window.updateThreadView = updateThreadView;
    window.stopTyping = stopTyping;

})();
