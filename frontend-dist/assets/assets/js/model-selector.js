/**
 * AI Model Selector Component
 * Allows users to select which AI model to use for quote generation
 */

class ModelSelector {
    constructor() {
        this.availableModels = [];
        this.selectedModel = 'auto';
        this.container = null;
    }

    /**
     * Initialize the model selector
     * @param {string} containerId - ID of the container element
     */
    async init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Model selector container not found: ${containerId}`);
            return;
        }

        // Fetch available models from API
        await this.fetchAvailableModels();

        // Render the selector
        this.render();
    }

    /**
     * Fetch available AI models from the backend
     */
    async fetchAvailableModels() {
        try {
            const response = await fetch(window.ApiConfig.url('/api/v1/models/available'));
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.availableModels = data.models || [];
            this.selectedModel = data.preferred || 'auto';

            console.log('[Model Selector] Available models:', this.availableModels);
        } catch (error) {
            console.error('[Model Selector] Failed to fetch models:', error);
            // Use default auto mode if fetch fails
            this.availableModels = [{
                id: 'auto',
                name: 'Automatic (Best Available)',
                provider: 'system',
                capabilities: ['vision', 'reasoning'],
                best_for: 'Automatically selects the best available model'
            }];
        }
    }

    /**
     * Render the model selector UI
     */
    render() {
        if (!this.container) return;

        const html = `
            <div class="model-selector-wrapper">
                <label class="model-selector-label">
                    <i class="fas fa-brain"></i> AI Model
                </label>
                <select id="model-selector-dropdown" class="model-selector-dropdown">
                    <option value="auto">Automatic (Recommended)</option>
                    ${this.availableModels.map(model => `
                        <option value="${model.id}" ${model.id === this.selectedModel ? 'selected' : ''}>
                            ${model.name}
                        </option>
                    `).join('')}
                </select>
                <div class="model-selector-info" id="model-info">
                    <small class="text-muted"></small>
                </div>
            </div>
        `;

        this.container.innerHTML = html;

        // Add event listener
        const dropdown = document.getElementById('model-selector-dropdown');
        if (dropdown) {
            dropdown.addEventListener('change', (e) => this.onModelChange(e.target.value));
            // Show initial info
            this.updateModelInfo(this.selectedModel);
        }
    }

    /**
     * Handle model selection change
     * @param {string} modelId - Selected model ID
     */
    onModelChange(modelId) {
        this.selectedModel = modelId;
        this.updateModelInfo(modelId);
        console.log('[Model Selector] Model changed to:', modelId);

        // Dispatch custom event for other components to listen
        const event = new CustomEvent('modelChanged', {
            detail: { model: modelId }
        });
        document.dispatchEvent(event);
    }

    /**
     * Update the info text based on selected model
     * @param {string} modelId - Model ID
     */
    updateModelInfo(modelId) {
        const infoElement = document.getElementById('model-info');
        if (!infoElement) return;

        if (modelId === 'auto') {
            infoElement.innerHTML = '<small class="text-muted">Automatically selects the best available AI model</small>';
            return;
        }

        const model = this.availableModels.find(m => m.id === modelId);
        if (model) {
            const icon = this.getModelIcon(model.provider);
            infoElement.innerHTML = `
                <small class="text-muted">
                    ${icon} ${model.best_for}
                </small>
            `;
        }
    }

    /**
     * Get icon for model provider
     * @param {string} provider - Provider name
     * @returns {string} HTML icon
     */
    getModelIcon(provider) {
        const icons = {
            'google': '<i class="fab fa-google"></i>',
            'openai': '<i class="fas fa-robot"></i>',
            'anthropic': '<i class="fas fa-brain"></i>'
        };
        return icons[provider] || '<i class="fas fa-microchip"></i>';
    }

    /**
     * Get the currently selected model
     * @returns {string} Selected model ID
     */
    getSelectedModel() {
        return this.selectedModel;
    }

    /**
     * Set the selected model programmatically
     * @param {string} modelId - Model ID to select
     */
    setSelectedModel(modelId) {
        this.selectedModel = modelId;
        const dropdown = document.getElementById('model-selector-dropdown');
        if (dropdown) {
            dropdown.value = modelId;
            this.updateModelInfo(modelId);
        }
    }
}

// Export as global
window.ModelSelector = ModelSelector;

// Add CSS styles
const style = document.createElement('style');
style.textContent = `
    .model-selector-wrapper {
        margin-bottom: 1rem;
    }

    .model-selector-label {
        display: block;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #374151;
    }

    .model-selector-label i {
        margin-right: 0.5rem;
        color: #6366f1;
    }

    .model-selector-dropdown {
        width: 100%;
        padding: 0.75rem 1rem;
        border: 2px solid #e5e7eb;
        border-radius: 0.5rem;
        font-size: 1rem;
        background-color: white;
        cursor: pointer;
        transition: all 0.2s;
    }

    .model-selector-dropdown:hover {
        border-color: #6366f1;
    }

    .model-selector-dropdown:focus {
        outline: none;
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }

    .model-selector-info {
        margin-top: 0.5rem;
        min-height: 1.5rem;
    }

    .model-selector-info small {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .model-selector-info i {
        font-size: 0.875rem;
    }
`;
document.head.appendChild(style);
