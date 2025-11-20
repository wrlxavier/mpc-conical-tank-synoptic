/**
 * UI Module for Tank Simulation Interface
 * Handles DOM manipulation, data display, and user interactions
 */

const UI = (() => {
    const CONTROL_KEY_REGEX = /(supply_valve|water_pump|brine_pump|outlet_valve)$/;
    /**
     * Show status message
     * @param {string} elementId - Status message element ID
     * @param {string} message - Message text
     * @param {string} type - Message type (success, error, info)
     */
    function showStatus(elementId, message, type = 'info') {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.textContent = message;
        element.className = `status-message ${type}`;
        element.style.display = 'block';
    }

    /**
     * Hide status message
     * @param {string} elementId - Status message element ID
     */
    function hideStatus(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        element.style.display = 'none';
    }

    /**
     * Update data card display
     * @param {string} cardId - Data card element ID
     * @param {number|string} value - Value to display
     * @param {number} decimals - Number of decimal places
     */
    function updateDataCard(cardId, value, decimals = 2) {
        const card = document.getElementById(cardId);
        if (!card) return;

        const valueElement = card.querySelector('.value');
        if (!valueElement) return;

        if (typeof value === 'number' && Number.isFinite(value)) {
            valueElement.textContent = value.toFixed(decimals);
        } else if (value === null || value === undefined || Number.isNaN(value)) {
            valueElement.textContent = '--';
        } else {
            valueElement.textContent = value;
        }
    }

    /**
     * Update all data cards from state object
     * @param {object} variables - Object with variable values
     */
    function updateAllDataCards(variables = {}, controls = null) {
        const { processVars, controlVars } = splitVariableMap(variables || {});
        const controlData = controls || (Object.keys(controlVars).length ? controlVars : null);

        if (processVars.tank_c_level !== undefined) {
            updateDataCard('data-tank-c-level', processVars.tank_c_level);
        }
        if (processVars.tank_c_concentration !== undefined) {
            updateDataCard('data-tank-c-conc', processVars.tank_c_concentration, 1);
        }
        if (processVars.tank_d_level !== undefined) {
            updateDataCard('data-tank-d-level', processVars.tank_d_level);
        }
        if (processVars.tank_d_concentration !== undefined) {
            updateDataCard('data-tank-d-conc', processVars.tank_d_concentration, 1);
        }
        if (processVars.tank_e_level !== undefined) {
            updateDataCard('data-tank-e-level', processVars.tank_e_level);
        }
        if (processVars.tank_e_concentration !== undefined) {
            updateDataCard('data-tank-e-conc', processVars.tank_e_concentration, 1);
        }

        updateControlCards(controlData || {});

        if (typeof SVGSynoptic !== 'undefined') {
            SVGSynoptic.updateOverlays(processVars, controlData || {});
        }
    }

    /**
     * Reset all data cards to default
     */
    function resetDataCards() {
        const cards = document.querySelectorAll('.data-card .value');
        cards.forEach(card => {
            card.textContent = '--';
        });

        // Reset SVG overlays if available
        if (typeof SVGSynoptic !== 'undefined') {
            SVGSynoptic.resetOverlays();
        }

        if (typeof ChartsManager !== 'undefined') {
            ChartsManager.reset();
        }
    }

    function updateControlCards(controlData = {}) {
        updateControlCard('data-tank-a-supply', controlData.tank_a_supply_valve);
        updateControlCard('data-tank-b-supply', controlData.tank_b_supply_valve);
        updateControlCard('data-tank-c-water', controlData.tank_c_water_pump);
        updateControlCard('data-tank-c-brine', controlData.tank_c_brine_pump);
        updateControlCard('data-tank-c-outlet', controlData.tank_c_outlet_valve);
        updateControlCard('data-tank-d-water', controlData.tank_d_water_pump);
        updateControlCard('data-tank-d-brine', controlData.tank_d_brine_pump);
        updateControlCard('data-tank-d-outlet', controlData.tank_d_outlet_valve);
        updateControlCard('data-tank-e-water', controlData.tank_e_water_pump);
        updateControlCard('data-tank-e-brine', controlData.tank_e_brine_pump);
        updateControlCard('data-tank-e-outlet', controlData.tank_e_outlet_valve);
    }

    function updateControlCard(cardId, value) {
        if (value === undefined || value === null) {
            updateDataCard(cardId, null);
            return;
        }
        updateDataCard(cardId, value * 100, 0);
    }

    function splitVariableMap(variables = {}) {
        const processVars = {};
        const controlVars = {};

        Object.entries(variables).forEach(([key, value]) => {
            if (CONTROL_KEY_REGEX.test(key)) {
                controlVars[key] = value;
            } else {
                processVars[key] = value;
            }
        });

        return { processVars, controlVars };
    }

    /**
     * Toggle button enabled/disabled state
     * @param {string} buttonId - Button element ID
     * @param {boolean} enabled - Enable or disable
     */
    function toggleButton(buttonId, enabled) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.disabled = !enabled;
        }
    }

    /**
     * Show/hide element
     * @param {string} elementId - Element ID
     * @param {boolean} show - Show or hide
     */
    function toggleElement(elementId, show) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = show ? 'block' : 'none';
        }
    }

    // Public API
    return {
        showStatus,
        hideStatus,
        updateDataCard,
        updateAllDataCards,
        resetDataCards,
        toggleButton,
        toggleElement
    };
})();
