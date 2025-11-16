/**
 * WebSocket Module for Real-time Tank Simulation
 * Manages WebSocket connection and message handling
 */

const WebSocketManager = (() => {
    let ws = null;
    let isConnected = false;
    let reconnectAttempts = 0;
    let maxReconnectAttempts = 5;
    let reconnectDelay = 2000; // ms
    let callbacks = {
        onOpen: null,
        onMessage: null,
        onClose: null,
        onError: null
    };

    /**
     * Get WebSocket URL based on current location
     * @returns {string} WebSocket URL
     */
    function getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws/realtime`;
    }

    /**
     * Connect to WebSocket server
     * @param {object} handlers - Event handlers
     */
    function connect(handlers = {}) {
        if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
            console.warn('WebSocket already connected or connecting');
            return;
        }

        // Store callbacks
        callbacks = { ...callbacks, ...handlers };

        const url = getWebSocketURL();
        console.log('Connecting to WebSocket:', url);

        ws = new WebSocket(url);

        ws.onopen = (event) => {
            console.log('WebSocket connected');
            isConnected = true;
            reconnectAttempts = 0;
            if (callbacks.onOpen) callbacks.onOpen(event);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data.type);
                if (callbacks.onMessage) callbacks.onMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            if (callbacks.onError) callbacks.onError(event);
        };

        ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            isConnected = false;
            ws = null;
            
            if (callbacks.onClose) callbacks.onClose(event);

            // Attempt reconnection if not a normal closure
            if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                console.log(`Reconnection attempt ${reconnectAttempts}/${maxReconnectAttempts} in ${reconnectDelay}ms`);
                setTimeout(() => connect(callbacks), reconnectDelay);
            }
        };
    }

    /**
     * Disconnect from WebSocket server
     */
    function disconnect() {
        if (ws) {
            console.log('Disconnecting WebSocket');
            reconnectAttempts = maxReconnectAttempts; // Prevent auto-reconnect
            ws.close(1000, 'User disconnect');
            ws = null;
            isConnected = false;
        }
    }

    /**
     * Send data through WebSocket
     * @param {object} data - Data to send
     */
    function send(data) {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            throw new Error('WebSocket not connected');
        }

        console.log('Sending WebSocket message:', data.type);
        ws.send(JSON.stringify(data));
    }

    /**
     * Send setpoint command
     * @param {string} tankId - Tank identifier
     * @param {string} variable - Variable name
     * @param {number} value - New setpoint value
     */
    function sendSetpoint(tankId, variable, value) {
        send({
            type: 'setpoint',
            data: {
                tank_id: tankId,
                variable: variable,
                value: parseFloat(value),
                timestamp: Date.now() / 1000
            }
        });
    }

    /**
     * Send pause command
     */
    function pause() {
        send({ type: 'pause' });
    }

    /**
     * Send resume command
     */
    function resume() {
        send({ type: 'resume' });
    }

    /**
     * Send reset command
     */
    function reset() {
        send({ type: 'reset' });
    }

    /**
     * Check if WebSocket is connected
     * @returns {boolean}
     */
    function getConnectionStatus() {
        return isConnected;
    }

    // Public API
    return {
        connect,
        disconnect,
        send,
        sendSetpoint,
        pause,
        resume,
        reset,
        getConnectionStatus
    };
})();
