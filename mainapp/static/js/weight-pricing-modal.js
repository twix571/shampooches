document.addEventListener('DOMContentLoaded', function() {
    window.weightPricingModalApp = function(breedId, breedName, defaultWeightRangeAmount, defaultWeightPriceAmount, defaultStartWeight) {
        const state = {
            breedId: breedId,
            breedName: breedName,
            weightRangeAmount: defaultWeightRangeAmount || '10',
            weightPriceAmount: defaultWeightPriceAmount || '15',
            startWeight: defaultStartWeight || '15',
            previewDogWeight: defaultStartWeight || '15',
            surcharge: 0,
            hasUnsavedChanges: false,
            autoSaveTimer: null,
            isAutoSaving: false
        };

        function updateDOM() {
            // Update display elements
            const elements = {
                weightRangeAmount: document.getElementById('weight_range_amount_display'),
                weightPriceAmount: document.getElementById('weight_price_amount_display'),
                startWeight: document.getElementById('start_weight_display')
            };

            if (elements.weightRangeAmount) elements.weightRangeAmount.textContent = state.weightRangeAmount;
            if (elements.weightPriceAmount) elements.weightPriceAmount.textContent = '$' + state.weightPriceAmount;
            if (elements.startWeight) elements.startWeight.textContent = state.startWeight;

            // Update input values
            const inputs = {
                weightRangeAmount: document.querySelector('input[name="weight_range_amount"]'),
                weightPriceAmount: document.querySelector('input[name="weight_price_amount"]'),
                startWeight: document.querySelector('input[name="start_weight"]'),
                previewDogWeight: document.querySelector('input[placeholder="Enter weight"]')
            };

            if (inputs.weightRangeAmount) inputs.weightRangeAmount.value = state.weightRangeAmount;
            if (inputs.weightPriceAmount) inputs.weightPriceAmount.value = state.weightPriceAmount;
            if (inputs.startWeight) inputs.startWeight.value = state.startWeight;
            if (inputs.previewDogWeight) inputs.previewDogWeight.value = state.previewDogWeight;

            // Update surcharge display
            const surchargeInput = document.querySelector('input[readonly][placeholder="$"]');
            if (surchargeInput) {
                surchargeInput.value = '$' + state.surcharge.toFixed(2);
            }

            updatePreview();
        }

        function updatePreview() {
            const weightRangeAmount = parseFloat(state.weightRangeAmount) || 10;
            const weightPriceAmount = parseFloat(state.weightPriceAmount) || 15;
            const startWeight = parseFloat(state.startWeight) || 15;
            const dogWeight = parseFloat(state.previewDogWeight) || startWeight;

            let surcharge = 0;

            if (dogWeight > startWeight) {
                const excessWeight = dogWeight - startWeight;
                const numIncrements = Math.floor(excessWeight / weightRangeAmount);
                surcharge = numIncrements * weightPriceAmount;
            }

            state.surcharge = surcharge;
            updateDOM();
        }

        function debounceAutoSave() {
            state.hasUnsavedChanges = true;

            if (state.isAutoSaving) return;

            if (state.autoSaveTimer) {
                clearTimeout(state.autoSaveTimer);
            }

            state.autoSaveTimer = setTimeout(() => {
                autoSaveWeightPricing();
                state.autoSaveTimer = null;
            }, 1000);
        }

        function autoSaveWeightPricing() {
            if (state.isAutoSaving) return;
            state.isAutoSaving = true;

            const data = {
                breed_id: state.breedId,
                weight_range_amount: state.weightRangeAmount,
                weight_price_amount: state.weightPriceAmount,
                start_weight: state.startWeight
            };

            fetch('/admin/update-breed-weight-pricing/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (!result.success) {
                    console.error('Auto-save failed:', result.error);
                } else {
                    state.hasUnsavedChanges = false;
                }
            })
            .catch(error => {
                console.error('Auto-save error:', error.message);
            })
            .finally(() => {
                state.isAutoSaving = false;
            });
        }

        async function handleBack() {
            // Cancel any pending auto-save
            if (state.autoSaveTimer) {
                clearTimeout(state.autoSaveTimer);
                state.autoSaveTimer = null;
            }

            // Wait for any in-progress auto-save to complete
            while (state.isAutoSaving) {
                await new Promise(resolve => setTimeout(resolve, 50));
            }

            // Perform an immediate save and wait for it
            await saveWeightPricingImmediate();

            // Now close the modal
            closeModal();
        }

        async function saveWeightPricingImmediate() {
            const data = {
                breed_id: state.breedId,
                weight_range_amount: state.weightRangeAmount,
                weight_price_amount: state.weightPriceAmount,
                start_weight: state.startWeight
            };

            try {
                const response = await fetch('/admin/update-breed-weight-pricing/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                return result.success;
            } catch (error) {
                console.error('Save error:', error.message);
                return false;
            }
        }

        // Event handlers
        const weightRangeInput = document.querySelector('input[name="weight_range_amount"]');
        const weightPriceInput = document.querySelector('input[name="weight_price_amount"]');
        const startWeightInput = document.querySelector('input[name="start_weight"]');
        const previewWeightInput = document.querySelector('input[placeholder="Enter weight"]');
        const backButton = document.querySelector('button:not(.close-modal)');

        if (weightRangeInput) {
            weightRangeInput.addEventListener('change', function() {
                state.weightRangeAmount = this.value;
                updatePreview();
                debounceAutoSave();
            });
            weightRangeInput.addEventListener('input', function() {
                state.weightRangeAmount = this.value.replace('.', '');
                this.value = state.weightRangeAmount;
                state.hasUnsavedChanges = true;
            });
            weightRangeInput.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                    state.hasUnsavedChanges = true;
                }
            });
        }

        if (weightPriceInput) {
            weightPriceInput.addEventListener('change', function() {
                state.weightPriceAmount = this.value;
                updatePreview();
                debounceAutoSave();
            });
            weightPriceInput.addEventListener('input', function() {
                state.weightPriceAmount = this.value.replace('.', '');
                this.value = state.weightPriceAmount;
                state.hasUnsavedChanges = true;
            });
            weightPriceInput.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                    state.hasUnsavedChanges = true;
                }
            });
        }

        if (startWeightInput) {
            startWeightInput.addEventListener('change', function() {
                state.startWeight = this.value;
                updatePreview();
                debounceAutoSave();
            });
            startWeightInput.addEventListener('input', function() {
                state.startWeight = this.value.replace('.', '');
                this.value = state.startWeight;
                state.hasUnsavedChanges = true;
            });
            startWeightInput.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                    state.hasUnsavedChanges = true;
                }
            });
        }

        if (previewWeightInput) {
            previewWeightInput.addEventListener('change', function() {
                state.previewDogWeight = this.value;
                updatePreview();
            });
            previewWeightInput.addEventListener('input', function() {
                state.previewDogWeight = this.value.replace('.', '');
                this.value = state.previewDogWeight;
            });
        }

        if (backButton && !backButton.classList.contains('hidden')) {
            backButton.addEventListener('click', handleBack);
        }

        // Initialize
        updatePreview();

        // Expose functions globally if needed
        return {
            state,
            updatePreview,
            handleBack
        };
    };
});
