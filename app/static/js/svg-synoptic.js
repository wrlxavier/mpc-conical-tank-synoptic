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
            await loadSVG('../static/imgs/tank_process.svg');
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

        if (!svgContainer) return;

        const temp = document.createElement('div');
        temp.innerHTML = svgText.trim();
        const loadedSVG = temp.firstElementChild;

        if (loadedSVG) {
            loadedSVG.style.width = '100%';
            loadedSVG.style.height = 'auto';
            loadedSVG.style.display = 'block';

            const overlays = document.getElementById('data-overlays');
            svgContainer.innerHTML = '';
            svgContainer.appendChild(loadedSVG);
            if (overlays) {
                svgContainer.appendChild(overlays);
            }
        }
    }

    /**
     * Create overlay elements for dynamic data display
     */
    function createOverlays() {
        if (!overlayContainer) return;

        const overlayConfig = [
            { id: 'overlay-tank-a-level', label: 'Nível Tanque A', unit: 'm', tank: 'A' },
            { id: 'overlay-tank-b-level', label: 'Nível Tanque B', unit: 'm', tank: 'B' },
            { id: 'overlay-tank-c-level', label: 'Nível Tanque C', unit: 'm', tank: 'C' },
            { id: 'overlay-tank-c-conc', label: 'Concentração Tanque C', unit: 'kg/m³', tank: 'C' },
            { id: 'overlay-tank-d-level', label: 'Nível Tanque D', unit: 'm', tank: 'D' },
            { id: 'overlay-tank-d-conc', label: 'Concentração Tanque D', unit: 'kg/m³', tank: 'D' },
            { id: 'overlay-tank-e-level', label: 'Nível Tanque E', unit: 'm', tank: 'E' },
            { id: 'overlay-tank-e-conc', label: 'Concentração Tanque E', unit: 'kg/m³', tank: 'E' },
            { id: 'overlay-tank-a-supply', label: 'Suprimento Tanque A', unit: '%', tank: 'A' },
            { id: 'overlay-tank-b-supply', label: 'Suprimento Tanque B', unit: '%', tank: 'B' },
            { id: 'overlay-tank-c-water-pump', label: 'Bomba de Água C', unit: '%', tank: 'C' },
            { id: 'overlay-tank-c-brine-pump', label: 'Bomba de Salmoura C', unit: '%', tank: 'C' },
            { id: 'overlay-tank-c-outlet-valve', label: 'Válvula de Saída C', unit: '%', tank: 'C' },
            { id: 'overlay-tank-d-water-pump', label: 'Bomba de Água D', unit: '%', tank: 'D' },
            { id: 'overlay-tank-d-brine-pump', label: 'Bomba de Salmoura D', unit: '%', tank: 'D' },
            { id: 'overlay-tank-d-outlet-valve', label: 'Válvula de Saída D', unit: '%', tank: 'D' },
            { id: 'overlay-tank-e-water-pump', label: 'Bomba de Água E', unit: '%', tank: 'E' },
            { id: 'overlay-tank-e-brine-pump', label: 'Bomba de Salmoura E', unit: '%', tank: 'E' },
            { id: 'overlay-tank-e-outlet-valve', label: 'Válvula de Saída E', unit: '%', tank: 'E' }
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
    function updateOverlays(variables = {}, controls = {}) {
        updateOverlay('overlay-tank-a-level', variables.tank_a_level, 2);
        updateOverlay('overlay-tank-b-level', variables.tank_b_level, 2);
        updateOverlay('overlay-tank-c-level', variables.tank_c_level, 2);
        updateOverlay('overlay-tank-c-conc', variables.tank_c_concentration, 1);
        updateOverlay('overlay-tank-d-level', variables.tank_d_level, 2);
        updateOverlay('overlay-tank-d-conc', variables.tank_d_concentration, 1);
        updateOverlay('overlay-tank-e-level', variables.tank_e_level, 2);
        updateOverlay('overlay-tank-e-conc', variables.tank_e_concentration, 1);

        updateControlOverlay('overlay-tank-a-supply', controls.tank_a_supply_valve);
        updateControlOverlay('overlay-tank-b-supply', controls.tank_b_supply_valve);
        updateControlOverlay('overlay-tank-c-water-pump', controls.tank_c_water_pump);
        updateControlOverlay('overlay-tank-c-brine-pump', controls.tank_c_brine_pump);
        updateControlOverlay('overlay-tank-c-outlet-valve', controls.tank_c_outlet_valve);
        updateControlOverlay('overlay-tank-d-water-pump', controls.tank_d_water_pump);
        updateControlOverlay('overlay-tank-d-brine-pump', controls.tank_d_brine_pump);
        updateControlOverlay('overlay-tank-d-outlet-valve', controls.tank_d_outlet_valve);
        updateControlOverlay('overlay-tank-e-water-pump', controls.tank_e_water_pump);
        updateControlOverlay('overlay-tank-e-brine-pump', controls.tank_e_brine_pump);
        updateControlOverlay('overlay-tank-e-outlet-valve', controls.tank_e_outlet_valve);
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
        if (valueElement && value !== undefined && value !== null && !Number.isNaN(value)) {
            valueElement.textContent = typeof value === 'number' ? value.toFixed(decimals) : value;
            overlay.classList.add('active');
        } else if (valueElement) {
            valueElement.textContent = '--';
            overlay.classList.remove('active');
        }
    }

    function updateControlOverlay(overlayId, value, decimals = 0) {
        if (value === undefined || value === null) {
            updateOverlay(overlayId, undefined, decimals);
            return;
        }
        updateOverlay(overlayId, value * 100, decimals);
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
