/**
 * SVG Synoptic Module
 * Manages SVG loading and dynamic data overlays for tank process visualization
 */

const SVGSynoptic = (() => {
    let svgContainer = null;
    let overlayContainer = null;
    let svgElement = null;

    /**
     * Initialize the SVG synoptic display
     * @param {string} svgContainerId - ID of container for SVG
     * @param {string} overlayContainerId - ID of container for overlays
     */
    async function initialize(svgContainerId, overlayContainerId) {
        svgContainer = document.getElementById(svgContainerId);
        overlayContainer = document.getElementById(overlayContainerId);

        if (!svgContainer) {
            console.error('SVG container not found');
            return false;
        }

        try {
            await loadSVG('/static/imgs/tank_process.svg');
            createOverlays();
            return true;
        } catch (error) {
            console.error('Error initializing SVG synoptic:', error);
            return false;
        }
    }

    /**
     * Load SVG file into container
     * @param {string} svgPath - Path to SVG file
     */
    async function loadSVG(svgPath) {
        const response = await fetch(svgPath);
        const svgText = await response.text();
        
        svgContainer.innerHTML = svgText;
        svgElement = svgContainer.querySelector('svg');
        
        if (svgElement) {
            svgElement.style.width = '100%';
            svgElement.style.height = 'auto';
            svgElement.style.display = 'block';
        }
    }

    /**
     * Create overlay elements for dynamic data display
     */
    function createOverlays() {
        if (!overlayContainer) return;

        const overlayConfig = [
            { id: 'overlay-tank-a-level', label: 'Tank A Level', unit: 'm', tank: 'A' },
            { id: 'overlay-tank-b-level', label: 'Tank B Level', unit: 'm', tank: 'B' },
            { id: 'overlay-tank-c-level', label: 'Tank C Level', unit: 'm', tank: 'C' },
            { id: 'overlay-tank-c-conc', label: 'Tank C Conc.', unit: 'kg/m³', tank: 'C' },
            { id: 'overlay-tank-d-level', label: 'Tank D Level', unit: 'm', tank: 'D' },
            { id: 'overlay-tank-d-conc', label: 'Tank D Conc.', unit: 'kg/m³', tank: 'D' },
            { id: 'overlay-tank-e-level', label: 'Tank E Level', unit: 'm', tank: 'E' },
            { id: 'overlay-tank-e-conc', label: 'Tank E Conc.', unit: 'kg/m³', tank: 'E' }
        ];

        overlayContainer.innerHTML = '';

        overlayConfig.forEach(config => {
            const overlay = document.createElement('div');
            overlay.id = config.id;
            overlay.className = `svg-overlay svg-overlay-tank-${config.tank.toLowerCase()}`;
            overlay.innerHTML = `
                <div class="overlay-label">${config.label}</div>
                <div class="overlay-value">--</div>
                <div class="overlay-unit">${config.unit}</div>
            `;
            overlayContainer.appendChild(overlay);
        });
    }

    /**
     * Update overlay values with process data
     * @param {object} variables - Process variables object
     */
    function updateOverlays(variables) {
        updateOverlay('overlay-tank-a-level', variables.tank_a_level, 2);
        updateOverlay('overlay-tank-b-level', variables.tank_b_level, 2);
        updateOverlay('overlay-tank-c-level', variables.tank_c_level, 2);
        updateOverlay('overlay-tank-c-conc', variables.tank_c_concentration, 1);
        updateOverlay('overlay-tank-d-level', variables.tank_d_level, 2);
        updateOverlay('overlay-tank-d-conc', variables.tank_d_concentration, 1);
        updateOverlay('overlay-tank-e-level', variables.tank_e_level, 2);
        updateOverlay('overlay-tank-e-conc', variables.tank_e_concentration, 1);
    }

    /**
     * Update individual overlay element
     * @param {string} overlayId - Overlay element ID
     * @param {number} value - Value to display
     * @param {number} decimals - Number of decimal places
     */
    function updateOverlay(overlayId, value, decimals = 2) {
        const overlay = document.getElementById(overlayId);
        if (!overlay) return;

        const valueElement = overlay.querySelector('.overlay-value');
        if (valueElement && value !== undefined && value !== null) {
            valueElement.textContent = typeof value === 'number' ? value.toFixed(decimals) : value;
            overlay.classList.add('active');
        } else if (valueElement) {
            valueElement.textContent = '--';
            overlay.classList.remove('active');
        }
    }

    /**
     * Reset all overlays to default state
     */
    function resetOverlays() {
        const overlays = overlayContainer?.querySelectorAll('.svg-overlay');
        overlays?.forEach(overlay => {
            const valueElement = overlay.querySelector('.overlay-value');
            if (valueElement) {
                valueElement.textContent = '--';
            }
            overlay.classList.remove('active');
        });
    }

    /**
     * Highlight specific tank overlay
     * @param {string} tankId - Tank identifier (tank_a, tank_b, etc.)
     * @param {boolean} highlight - Enable or disable highlight
     */
    function highlightTank(tankId, highlight) {
        const tankClass = tankId.replace('_', '-');
        const overlays = document.querySelectorAll(`.svg-overlay-${tankClass}`);
        
        overlays.forEach(overlay => {
            if (highlight) {
                overlay.classList.add('highlighted');
            } else {
                overlay.classList.remove('highlighted');
            }
        });
    }

    // Public API
    return {
        initialize,
        updateOverlays,
        resetOverlays,
        highlightTank
    };
})();
