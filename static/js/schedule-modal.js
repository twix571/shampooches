/**
 * Schedule Modal Application (Simplified)
 * Handles add/delete/save time slots functionality only.
 * Groomer and time slot loading is handled by HTMX.
 */
(function() {
    'use strict';

    class ScheduleModal {
        constructor(containerElement) {
            this.container = containerElement;
            this.container._scheduleModal = this; // Store reference for HTMX handlers
            this.state = {
                existingSlots: [],
                pendingDeleteSlotId: null
            };

            this.elements = {};
            this.init();
        }

        init() {
            // Get context data from data attributes
            const contextDate = this.container.getAttribute('data-context-date') || '';
            const contextDayName = this.container.getAttribute('data-context-day-name') || '';

            if (contextDate) {
                try {
                    this.dateObj = this.parseDate(contextDate);
                    if (!this.dateObj || isNaN(this.dateObj.getTime())) {
                        console.error('ScheduleModal: Invalid date object created from contextDate:', contextDate);
                        this.dateObj = null;
                    }
                } catch (error) {
                    console.error('ScheduleModal: Error parsing date:', contextDate, error);
                    this.dateObj = null;
                }
            }

            if (this.dateObj) {
                this.dayName = contextDayName || this.dateObj.toLocaleDateString('en-US', { weekday: 'long' });

                // Update formatted date
                const formattedDateEl = document.getElementById('formatted-date');
                if (formattedDateEl) {
                    formattedDateEl.textContent = `${this.dayName}, ${this.dateObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`;
                }
            }

            this.cacheElements();
            this.setupEventListeners();
        }

        parseDate(dateStr) {
            if (!dateStr) return null;

            // Clean the date string - replace any unicode escape sequences with actual characters
            const cleanDateStr = dateStr.replace(/\\u002D/g, '-');

            // Simple ISO format parsing (YYYY-MM-DD)
            const parts = cleanDateStr.split('-');
            if (parts.length === 3) {
                const [year, month, day] = parts.map(Number);
                const date = new Date(year, month - 1, day);
                if (!isNaN(date.getTime())) {
                    return date;
                }
            }

            return null;
        }

        cacheElements() {
            this.elements.existingSlotsContainer = this.container.querySelector('#existing-slots');
            this.elements.newStartTime = this.container.querySelector('input[name="new_start_time"]');
            this.elements.newEndTime = this.container.querySelector('input[name="new_end_time"]');
            this.elements.groomerSelect = this.container.querySelector('#groomer-select');
        }

        setupEventListeners() {
            // Event delegation for dynamic elements
            this.container.addEventListener('click', (event) => {
                const target = event.target;

                // Add time slot button
                if (target.closest('[data-action="add-time-slot"]')) {
                    this.addTimeSlot();
                }

                // Quick add buttons
                const quickAddBtn = target.closest('[data-quick-add]');
                if (quickAddBtn) {
                    const startTime = quickAddBtn.getAttribute('data-quick-add');
                    const endTime = quickAddBtn.getAttribute('data-quick-add-end');
                    this.quickAddTimeSlot(startTime, endTime);
                }

                // Save button
                if (target.closest('[data-action="save-time-slots"]')) {
                    this.saveTimeSlots();
                }

                // Delete slot button
                const deleteBtn = target.closest('[data-action="delete-slot"]');
                if (deleteBtn) {
                    const slotId = parseInt(deleteBtn.getAttribute('data-slot-id'));
                    this.deleteSlot(slotId);
                }
            });
        }

        parseExistingSlotsFromHTML() {
            if (!this.elements.existingSlotsContainer) {
                console.warn('[ScheduleModal] No existing slots container found');
                return;
            }

            const deleteButtons = this.elements.existingSlotsContainer.querySelectorAll('[data-action="delete-slot"]');
            const slots = [];

            deleteButtons.forEach(button => {
                const slotId = parseInt(button.getAttribute('data-slot-id'));
                const flexContainer = button.closest('.flex');

                if (!flexContainer) return;

                // Find the span containing the time format (with " - ")
                const timeSpan = Array.from(flexContainer.querySelectorAll('span')).find(span => {
                    return span.textContent.includes(' - ') && (span.textContent.includes('AM') || span.textContent.includes('PM'));
                });

                if (!timeSpan) return;

                const timeText = timeSpan.textContent.trim();
                const [start, end] = timeText.split(' - ').map(t => t.trim());

                slots.push({
                    id: slotId,
                    start: this.time24(start),
                    end: this.time24(end)
                });
            });

            this.state.existingSlots = slots;
        }

        time24(time12) {
            const [time, period] = time12.split(' ');
            let [hours, minutes] = time.split(':');
            hours = parseInt(hours);
            if (period === 'PM' && hours !== 12) hours += 12;
            if (period === 'AM' && hours === 12) hours = 0;
            return `${hours.toString().padStart(2, '0')}:${minutes}`;
        }

        formatTime(time24) {
            const [hours, minutes] = time24.split(':');
            const hour = parseInt(hours);
            const ampm = hour >= 12 ? 'PM' : 'AM';
            const hour12 = hour % 12 || 12;
            return `${hour12}:${minutes} ${ampm}`;
        }

        deleteSlot(slotId) {
            // Ensure existing slots are parsed from HTML before any operation
            if (this.state.existingSlots.length === 0) {
                this.parseExistingSlotsFromHTML();
            }

            // If this slot is already pending deletion, confirm and delete
            if (this.state.pendingDeleteSlotId === slotId) {
                this.state.pendingDeleteSlotId = null;
                this.state.existingSlots = this.state.existingSlots.filter(slot => slot.id !== slotId);
                this.renderExistingSlots();
                showNotification('Time slot deleted', 'success');
                return;
            }

            // Mark this slot as pending deletion
            this.state.pendingDeleteSlotId = slotId;
            this.renderExistingSlots();
            showNotification('Click delete again to confirm', 'info');

            // Auto-cancel after 3 seconds if not confirmed
            setTimeout(() => {
                if (this.state.pendingDeleteSlotId === slotId) {
                    this.state.pendingDeleteSlotId = null;
                    const hasLocalOnlySlots = this.state.existingSlots.some(slot => slot.isNew || isNaN(slot.id));
                    if (!hasLocalOnlySlots) {
                        this.parseExistingSlotsFromHTML();
                    }
                    this.renderExistingSlots();
                }
            }, 3000);
        }

        renderExistingSlots() {
            if (!this.elements.existingSlotsContainer) return;

            if (this.state.existingSlots.length === 0) {
                this.elements.existingSlotsContainer.innerHTML = '<p class="text-gray-400 text-sm">No existing time slots for this day</p>';
                return;
            }

            let html = '';
            this.state.existingSlots.forEach(slot => {
                const isPendingDelete = this.state.pendingDeleteSlotId === slot.id;
                const containerClass = isPendingDelete
                    ? 'bg-red-50 rounded-md px-3 py-2 border-2 border-red-300 shadow-md'
                    : 'bg-gray-50 rounded-md px-3 py-2 border border-gray-200';
                const timeClass = isPendingDelete ? 'text-red-700 font-semibold' : 'text-sm text-gray-700';
                const buttonText = isPendingDelete ? 'Confirm Delete' : 'Delete';
                const buttonClass = isPendingDelete
                    ? 'text-red-600 font-bold px-3 py-1 rounded text-xs border-2 border-red-400 bg-red-50 transition-all'
                    : 'text-red-500 hover:text-red-700 text-xs';

                html += `
                    <div class="flex items-center justify-between ${containerClass} transition-all duration-200">
                        <span class="${timeClass}">${this.formatTime(slot.start)} - ${this.formatTime(slot.end)}</span>
                        <button data-action="delete-slot" data-slot-id="${slot.id}" class="${buttonClass}">${buttonText}</button>
                    </div>
                `;
            });

            this.elements.existingSlotsContainer.innerHTML = html;
        }

        addTimeSlot() {
            const startTime = this.elements.newStartTime ? this.elements.newStartTime.value : '';
            const endTime = this.elements.newEndTime ? this.elements.newEndTime.value : '';

            if (!startTime || !endTime) {
                showNotification('Please enter both start and end times', 'error');
                return;
            }

            if (startTime >= endTime) {
                showNotification('End time must be after start time', 'error');
                return;
            }

            // Check for duplicate start times
            const slotExists = this.state.existingSlots.some(slot => slot.start === startTime);
            if (slotExists) {
                showNotification('A time slot with this start time already exists', 'error');
                return;
            }

            // Add to existing slots
            this.state.existingSlots.push({
                id: Date.now(), // Temporary ID for UI
                start: startTime,
                end: endTime,
                isNew: true
            });

            this.renderExistingSlots();

            // Clear inputs
            if (this.elements.newStartTime) this.elements.newStartTime.value = '';
            if (this.elements.newEndTime) this.elements.newEndTime.value = '';
        }

        quickAddTimeSlot(startTime, endTime) {
            // Check for duplicate start times
            const slotExists = this.state.existingSlots.some(slot => slot.start === startTime);
            if (slotExists) {
                showNotification('A time slot with this start time already exists', 'error');
                return;
            }

            // Add to existing slots
            this.state.existingSlots.push({
                id: Date.now(),
                start: startTime,
                end: endTime,
                isNew: true
            });

            this.renderExistingSlots();
        }

        async saveTimeSlots() {
            const selectedGroomerId = this.elements.groomerSelect ? this.elements.groomerSelect.value : '';

            if (!this.dateObj || isNaN(this.dateObj.getTime())) {
                showNotification('No valid date selected', 'error');
                return;
            }

            // Show confirmation dialog for all groomers
            if (!selectedGroomerId) {
                if (typeof window.showConfirmModal === 'function') {
                    const confirmed = await window.showConfirmModal('Apply to All Groomers', 'This will apply time slots to ALL groomers. Continue?');
                    if (!confirmed) return;
                } else if (typeof confirm === 'function') {
                    if (!confirm('This will apply time slots to ALL groomers. Continue?')) {
                        return;
                    }
                }
            }

            this._performSave(selectedGroomerId);
        }

        async _performSave(groomerId) {
            // Parse existing slots from HTML if state is empty
            if (this.state.existingSlots.length === 0 && this.elements.existingSlotsContainer) {
                this.parseExistingSlotsFromHTML();
            }

            // Prepare the data for the API
            const timeSlotsData = this.state.existingSlots.map(slot => ({
                start: slot.start,
                end: slot.end
            }));

            // Check for duplicate start times (backend validation should handle this)
            const startTimes = timeSlotsData.map(slot => slot.start);
            const uniqueStartTimes = new Set(startTimes);
            if (startTimes.length !== uniqueStartTimes.size) {
                showNotification('Duplicate time slots detected. Each start time can only appear once.', 'error');
                return;
            }

            const dateStr = this.dateObj.toISOString().split('T')[0];
            const payload = {
                groomer_id: groomerId || 'all',
                date: dateStr,
                time_slots: timeSlotsData
            };

            try {
                const response = await fetch('/api/v1/admin/time-slots/set-day/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });

                let data;
                try {
                    data = await response.json();
                } catch (e) {
                    data = { message: 'Invalid response from server' };
                }

                if (response.ok) {
                    const message = !groomerId
                        ? 'Time slots saved for all groomers!'
                        : 'Time slots saved successfully!';
                    showNotification(message, 'success');
                    closeModal();
                    setTimeout(() => {
                        if (window.openModal) {
                            window.openModal('/appointments/');
                        } else if (window.loadModalContent) {
                            window.loadModalContent('/appointments/');
                        }
                    }, 150);
                } else {
                    const errorMessage = data.message || data.errors || 'Error saving time slots';
                    console.error('Server error:', data);
                    showNotification(String(errorMessage), 'error');
                }
            } catch (error) {
                console.error('Error saving time slots:', error);
                showNotification('Network error saving time slots', 'error');
            }
        }

        getCsrfToken() {
            const token = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
            if (token) return token;

            const cookieValue = `; ${document.cookie}`;
            const parts = cookieValue.split(`; csrftoken=`);
            if (parts.length === 2) return parts.pop().split(';').shift();

            return '';
        }
    }

    function initScheduleModal() {
        const container = document.querySelector('.schedule-modal-container');
        if (container) {
            new ScheduleModal(container);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initScheduleModal);
    } else {
        initScheduleModal();
    }

    window.ScheduleModal = ScheduleModal;

    // Listen for HTMX content swaps to refresh state
    document.body.addEventListener('htmx:afterSwap', function(event) {
        if (event.target && (event.target.id === 'existing-slots' || event.target.querySelector('#existing-slots'))) {
            const modalContainer = document.querySelector('.schedule-modal-container');
            if (modalContainer && modalContainer._scheduleModal) {
                modalContainer._scheduleModal.state.existingSlots = [];
                modalContainer._scheduleModal.state.pendingDeleteSlotId = null;
            }
        }
    });
})();
