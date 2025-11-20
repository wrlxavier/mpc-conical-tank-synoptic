/**
 * API Module for Tank Simulation System
 * Handles HTTP requests to the FastAPI backend
 */

const API = (() => {
    const BASE_URL = window.location.origin;

    /**
     * Generic fetch wrapper with error handling
     * @param {string} endpoint - API endpoint
     * @param {object} options - Fetch options
     * @returns {Promise<object>} Response data
     */
    async function request(endpoint, options = {}) {
        try {
            const response = await fetch(`${BASE_URL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Initialize real-time simulation
     * @param {object} config - Real-time configuration
     * @returns {Promise<object>} Initialization response with session ID
     */
    async function initializeRealTime(config) {
        console.log('Initializing real-time simulation:', config);
        return await request('/simulation/initialize', {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    /**
     * Get current simulation status
     * @returns {Promise<object>} Current status
     */
    async function getSimulationStatus() {
        return await request('/simulation/status');
    }

    /**
     * Health check
     * @returns {Promise<object>} Health status
     */
    async function healthCheck() {
        return await request('/health');
    }

    // Public API
    return {
        initializeRealTime,
        getSimulationStatus,
        healthCheck
    };
})();
