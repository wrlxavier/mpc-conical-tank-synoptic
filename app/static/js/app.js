/**
 * Main Application Module
 * Initializes and coordinates all modules for the tank simulation interface
 */

(function () {
    'use strict';

    // Application state
    let realtimeSessionId = null;
    let isPaused = false;

    /**
     * Initialize application
     */
    async function init() {
        console.log('Initializing Tank Simulation Application');

        // Initialize SVG Synoptic
        const svgInitialized = await SVGSynoptic.initialize('synoptic-board', 'data-overlays');

        if (svgInitialized) {
            document.getElementById('synoptic-board').classList.add('loaded');
            console.log('SVG Synoptic initialized successfully');
        } else {
            console.warn('SVG Synoptic initialization failed');
        }

        // Set up real-time simulation
        setupRealTimeSimulation();
        // Initialize trend charts
        if (typeof ChartsManager !== 'undefined') {
            ChartsManager.initialize();
        }

        // Perform health check
        performHealthCheck();
    }

    /**
     * Set up real-time simulation controls
     */
    function setupRealTimeSimulation() {
        // Initialize button
        document.getElementById('initialize-realtime')?.addEventListener('click', async () => {
            await initializeRealTime();
        });

        // Connect button
        document.getElementById('connect-websocket')?.addEventListener('click', () => {
            connectWebSocket();
        });

        // Runtime controls
        document.getElementById('rt-pause')?.addEventListener('click', () => {
            WebSocketManager.pause();
            isPaused = true;
            UI.toggleButton('rt-pause', false);
            UI.toggleButton('rt-resume', true);
        });

        document.getElementById('rt-resume')?.addEventListener('click', () => {
            WebSocketManager.resume();
            isPaused = false;
            UI.toggleButton('rt-pause', true);
            UI.toggleButton('rt-resume', false);
        });

        document.getElementById('rt-reset')?.addEventListener('click', () => {
            WebSocketManager.reset();
            UI.showStatus('realtime-status', 'System reset to equilibrium', 'info');
        });

        document.getElementById('rt-disconnect')?.addEventListener('click', () => {
            disconnectWebSocket();
        });

        // Setpoint control
        document.getElementById('rt-send-setpoint')?.addEventListener('click', () => {
            sendSetpointCommand();
        });
    }

    /**
     * Initialize real-time simulation
     */
    async function initializeRealTime() {
        try {
            UI.showStatus('realtime-status', 'Initializing real-time simulation...', 'info');
            UI.toggleButton('initialize-realtime', false);

            const config = buildRealTimeConfig();
            console.log('Real-time config:', config);

            const response = await API.initializeRealTime(config);
            realtimeSessionId = response.session_id;

            UI.showStatus('realtime-status', `Initialized. Session: ${realtimeSessionId}`, 'success');
            UI.toggleButton('connect-websocket', true);

        } catch (error) {
            console.error('Real-time initialization error:', error);
            UI.showStatus('realtime-status', `Error: ${error.message}`, 'error');
            UI.toggleButton('initialize-realtime', true);
        }
    }

    /**
     * Build real-time configuration from form inputs
     * @returns {object} Real-time configuration
     */
    function buildRealTimeConfig() {
        return {
            equilibrium_point: {
                levels: {
                    tank_a: parseFloat(document.getElementById('rt-eq-a-level').value),
                    tank_b: parseFloat(document.getElementById('rt-eq-b-level').value),
                    tank_c: parseFloat(document.getElementById('rt-eq-c-level').value),
                    tank_d: parseFloat(document.getElementById('rt-eq-d-level').value),
                    tank_e: parseFloat(document.getElementById('rt-eq-e-level').value)
                },
                concentrations: {
                    tank_c: parseFloat(document.getElementById('rt-eq-c-conc').value),
                    tank_d: parseFloat(document.getElementById('rt-eq-d-conc').value),
                    tank_e: parseFloat(document.getElementById('rt-eq-e-conc').value)
                },
                controls: {
                    tank_a_supply_valve: 0.5,
                    tank_b_supply_valve: 0.5,
                    tank_c_water_pump: 0.6,
                    tank_c_brine_pump: 0.6,
                    tank_c_outlet_valve: 0.5,
                    tank_d_water_pump: 0.6,
                    tank_d_brine_pump: 0.6,
                    tank_d_outlet_valve: 0.5,
                    tank_e_water_pump: 0.6,
                    tank_e_brine_pump: 0.6,
                    tank_e_outlet_valve: 0.5
                }
            },
            sampling_interval: parseFloat(document.getElementById('rt-sampling').value),
            enable_noise: document.getElementById('rt-enable-noise').checked,
            noise_level: 0.01
        };
    }

    /**
     * Connect to WebSocket
     */
    function connectWebSocket() {
        UI.showStatus('realtime-status', 'Connecting to WebSocket...', 'info');
        UI.toggleButton('connect-websocket', false);

        WebSocketManager.connect({
            onOpen: handleWebSocketOpen,
            onMessage: handleWebSocketMessage,
            onClose: handleWebSocketClose,
            onError: handleWebSocketError
        });
    }

    /**
     * Disconnect from WebSocket
     */
    function disconnectWebSocket() {
        WebSocketManager.disconnect();
        UI.toggleElement('rt-runtime-controls', false);
        UI.toggleElement('rt-setpoint-controls', false);
        UI.toggleButton('initialize-realtime', true);
        UI.toggleButton('connect-websocket', false);
        UI.resetDataCards();
    }

    /**
     * Handle WebSocket open event
     */
    function handleWebSocketOpen(event) {
        console.log('WebSocket opened:', event);
        UI.showStatus('realtime-status', 'Connected! Receiving real-time data...', 'success');
        UI.toggleElement('rt-runtime-controls', true);
        UI.toggleElement('rt-setpoint-controls', true);
        UI.toggleButton('rt-pause', true);
    }

    /**
     * Handle WebSocket message event
     * @param {object} data - Message data
     */
    function handleWebSocketMessage(data) {
        if (data.type !== 'initial_state' && data.type !== 'state_update') {
            return;
        }

        const payload = data.data || {};
        const { variables = {}, controls = {}, timestamp } = payload;

        if (typeof ChartsManager !== 'undefined') {
            ChartsManager.ingestRealtimeSample(timestamp, variables, controls);
        }

        UI.updateAllDataCards(variables, controls);
    }

    /**
     * Handle WebSocket close event
     */
    function handleWebSocketClose(event) {
        console.log('WebSocket closed:', event);
        UI.showStatus('realtime-status', 'Disconnected from server', 'info');
        UI.toggleElement('rt-runtime-controls', false);
        UI.toggleElement('rt-setpoint-controls', false);
        UI.toggleButton('connect-websocket', true);
        if (typeof ChartsManager !== 'undefined') {
            ChartsManager.reset();
        }
    }

    /**
     * Handle WebSocket error event
     */
    function handleWebSocketError(event) {
        console.error('WebSocket error:', event);
        UI.showStatus('realtime-status', 'WebSocket connection error', 'error');
    }

    /**
     * Send setpoint command
     */
    function sendSetpointCommand() {
        try {
            const tankId = document.getElementById('rt-sp-tank').value;
            const variable = document.getElementById('rt-sp-variable').value;
            const value = parseFloat(document.getElementById('rt-sp-value').value);

            if (isNaN(value)) {
                UI.showStatus('realtime-status', 'Invalid setpoint value', 'error');
                return;
            }

            WebSocketManager.sendSetpoint(tankId, variable, value);
            UI.showStatus('realtime-status', `Setpoint sent: ${tankId} ${variable} = ${value}`, 'success');

        } catch (error) {
            console.error('Error sending setpoint:', error);
            UI.showStatus('realtime-status', `Error: ${error.message}`, 'error');
        }
    }

    /**
     * Perform health check on backend
     */
    async function performHealthCheck() {
        try {
            const health = await API.healthCheck();
            console.log('Backend health check:', health);
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }

    // Initialize application when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
