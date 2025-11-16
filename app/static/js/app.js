/**
 * Main Application Module
 * Initializes and coordinates all modules for the tank simulation interface
 */

(function () {
    'use strict';

    // Application state
    let currentMode = 'batch';
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

        // Set up mode switching
        setupModeSwitch();

        // Set up batch simulation
        setupBatchSimulation();

        // Set up real-time simulation
        setupRealTimeSimulation();

        // Perform health check
        performHealthCheck();
    }

    /**
     * Set up mode switching functionality
     */
    function setupModeSwitch() {
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.getAttribute('data-mode');
                switchToMode(mode);
            });
        });
    }

    /**
     * Switch to specified mode
     * @param {string} mode - 'batch' or 'realtime'
     */
    function switchToMode(mode) {
        if (currentMode === mode) return;

        // Disconnect WebSocket if switching from real-time
        if (currentMode === 'realtime' && WebSocketManager.getConnectionStatus()) {
            WebSocketManager.disconnect();
        }

        currentMode = mode;
        UI.switchMode(mode);
        console.log(`Switched to ${mode} mode`);
    }

    /**
     * Set up batch simulation controls
     */
    function setupBatchSimulation() {
        // Add step input button
        document.getElementById('add-step-input')?.addEventListener('click', () => {
            UI.addStepInputRow('step-inputs-container');
        });

        // Run simulation button
        document.getElementById('run-batch-simulation')?.addEventListener('click', async () => {
            await runBatchSimulation();
        });
    }

    /**
     * Run batch simulation
     */
    async function runBatchSimulation() {
        try {
            UI.showStatus('batch-status', 'Preparing simulation...', 'info');
            UI.toggleButton('run-batch-simulation', false);

            // Collect simulation parameters
            const params = buildBatchSimulationParams();
            console.log('Batch simulation parameters:', params);

            // Run simulation
            UI.showStatus('batch-status', 'Running simulation...', 'info');
            const response = await API.runBatchSimulation(params);

            // Display results
            UI.displayBatchResults(response);

        } catch (error) {
            console.error('Batch simulation error:', error);
            UI.showStatus('batch-status', `Error: ${error.message}`, 'error');
        } finally {
            UI.toggleButton('run-batch-simulation', true);
        }
    }

    /**
     * Build batch simulation parameters from form inputs
     * @returns {object} Simulation parameters
     */
    function buildBatchSimulationParams() {
        return {
            initial_conditions: {
                tank_a: { level: 1.5, concentration: null },
                tank_b: { level: 1.5, concentration: null },
                tank_c: {
                    level: parseFloat(document.getElementById('batch-ic-c-level').value),
                    concentration: parseFloat(document.getElementById('batch-ic-c-conc').value)
                },
                tank_d: {
                    level: parseFloat(document.getElementById('batch-ic-d-level').value),
                    concentration: parseFloat(document.getElementById('batch-ic-d-conc').value)
                },
                tank_e: {
                    level: parseFloat(document.getElementById('batch-ic-e-level').value),
                    concentration: parseFloat(document.getElementById('batch-ic-e-conc').value)
                }
            },
            control_inputs: {
                tank_a_control: { supply_valve: 0.5 },
                tank_b_control: { supply_valve: 0.5 },
                tank_c_control: { water_pump: 0.6, brine_pump: 0.6, outlet_valve: 0.5 },
                tank_d_control: { water_pump: 0.6, brine_pump: 0.6, outlet_valve: 0.5 },
                tank_e_control: { water_pump: 0.6, brine_pump: 0.6, outlet_valve: 0.5 }
            },
            simulation_config: {
                simulation_id: `batch_${Date.now()}`,
                time_step: parseFloat(document.getElementById('batch-timestep').value),
                duration: parseFloat(document.getElementById('batch-duration').value),
                solver: document.getElementById('batch-solver').value,
                save_interval: parseFloat(document.getElementById('batch-saveinterval').value)
            },
            step_inputs: UI.getStepInputs('step-inputs-container')
        };
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
        if (data.type === 'initial_state') {
            console.log('Received initial state:', data.data);
            const { variables = {}, controls = {} } = data.data || {};
            UI.updateAllDataCards(variables, controls);
        } else if (data.type === 'state_update') {
            // Update data display in real-time
            const { variables = {}, controls = {} } = data.data || {};
            UI.updateAllDataCards(variables, controls);
        }
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
