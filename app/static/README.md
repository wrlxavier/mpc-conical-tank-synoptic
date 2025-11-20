# Frontend Documentation - Tank Simulation Synoptic

Complete documentation for the real-time tank simulation frontend interface.

## 🏛️ Architecture

The frontend is built with vanilla JavaScript using a modular architecture:

```
app/static/
├── index.html          # Main HTML structure
├── css/
│   ├── styles.css      # Responsive styling
│   └── svg-synoptic.css # SVG overlay styling
└── js/
    ├── api.js          # HTTP API communication module
    ├── websocket.js    # WebSocket real-time communication
    ├── ui.js           # DOM manipulation and data display
    ├── svg-synoptic.js # SVG synoptic overlay module
    └── app.js          # Main application coordinator (initializes SVGSynoptic)
```

## 📦 Modules

### 1. API Module (`api.js`)

Handles all HTTP requests to the FastAPI backend.

**Key Functions:**
- `initializeRealTime(config)` - POST to `/simulation/initialize`
- `getSimulationStatus()` - GET current status
- `healthCheck()` - Check backend health

### 2. WebSocket Module (`websocket.js`)

Manages WebSocket connection for real-time data streaming.

**Key Functions:**
- `connect(handlers)` - Establish WebSocket connection
- `disconnect()` - Close connection
- `sendSetpoint(tankId, variable, value)` - Send setpoint command
- `pause()` / `resume()` / `reset()` - Runtime controls
- `getConnectionStatus()` - Check connection state

**Example Usage:**
```javascript
// Connect to WebSocket
WebSocketManager.connect({
    onOpen: (event) => console.log('Connected'),
    onMessage: (data) => {
        if (data.type === 'state_update') {
            console.log('Current level:', data.data.variables.tank_c_level);
        }
    },
    onClose: (event) => console.log('Disconnected'),
    onError: (error) => console.error('Error:', error)
});

// Send setpoint change
WebSocketManager.sendSetpoint('tank_c', 'level', 2.0);
```

### 3. UI Module (`ui.js`)

Handles all DOM manipulation and data visualization.

**Key Functions:**
- `showStatus(elementId, message, type)` - Display status messages
- `updateDataCard(cardId, value, decimals)` - Update single data card
- `updateAllDataCards(variables)` - Update all cards from state object

**Example Usage:**
```javascript
// Update data display
UI.updateAllDataCards({
    tank_c_level: 1.52,
    tank_c_concentration: 182.5,
    tank_d_level: 1.48,
    // ...
});

// Show success message
UI.showStatus('realtime-status', 'Receiving live data...', 'success');
```

### 4. SVG Synoptic Module (`svg-synoptic.js`)

Handles SVG-based process visualization:

- Loads `tank_process.svg` into the synoptic board.
- Creates overlay elements as defined in `overlayConfig` (process variables and actuator controls).
- Updates overlays synchronously with `UI.updateAllDataCards()` and `SVGSynoptic.updateOverlays()`.
- Overlay positions and styles are managed in `svg-synoptic.css`.

**Initialization:**  
`app.js` calls `SVGSynoptic.initialize()` during startup. On success, the container `#synoptic-board` receives the class `loaded` (see `svg-synoptic.css` for placeholder hiding).

**Overlay Lifecycle:**  
- Overlays are created on SVG load.
- Updated via `updateOverlay` and `updateControlOverlay`.
- Reset via `SVGSynoptic.resetOverlays()` (called by `UI.resetDataCards()`).

**Control Scaling:**  
Actuator controls are displayed as percentages:  
$u_{\%} = 100 \times u$  
Scaling is performed in `updateControlOverlay`.

## 📊 Real-time Operation

**Workflow:**
1. `initializeRealTime()` (HTTP) sends payload built by `buildRealTimeConfig`.
2. `WebSocketManager.connect()` (see `websocket.js`) establishes connection and receives `state_update` messages.
3. Each update triggers `UI.updateAllDataCards()` and `SVGSynoptic.updateOverlays()` for synchronized display.

**Data Flow:**
```
Initialize → API.initializeRealTime() → Backend
                                            ↓
                                      Session Created
                                            ↓
WebSocket ←─────── state_update ←─────── Real-time Loop
    ↓                                       ↑
UI.updateAllDataCards() → SVGSynoptic.updateOverlays()
setpoint commands
```

## 🔧 Customization

### Adding New Data Cards

1. **Update HTML** (`index.html`):
```html
<div class="data-card" id="data-new-variable">
    <h3>New Variable</h3>
    <div class="value">--</div>
    <div class="unit">unit</div>
</div>
```

2. **Update UI Module** (`ui.js`):
```javascript
function updateAllDataCards(variables) {
    // ... existing cards ...
    if (variables.new_variable !== undefined) {
        updateDataCard('data-new-variable', variables.new_variable);
    }
}
```

### Adding New Overlays

1. **In `svg-synoptic.js`**, add to `overlayConfig` array:
```javascript
{ id: 'overlay-tank-c-water-pump', label: 'Tank C Water Pump', unit: '%', tank: 'C' }
```
2. **Add positioning in `svg-synoptic.css`**:
```css
#overlay-tank-c-water-pump {
    top: 40%;
    left: 12%;
}
```
3. **Update in `SVGSynoptic.updateOverlays()`**:
```javascript
updateControlOverlay('overlay-tank-c-water-pump', controls.tank_c_water_pump);
```
*Note: Control values are multiplied by 100 before display.*

### Styling Customization

All styles are in `css/styles.css`. Key classes:

- `.control-panel` / `.control-group` - Form layout
- `.data-card` - Real-time data display cards
- `.status-message` - Status/error messages
- `.btn-primary`, `.btn-secondary`, etc. - Action buttons

## 📡 WebSocket Protocol

### Messages from Client to Server

```javascript
// Setpoint change
{
    type: 'setpoint',
    data: {
        tank_id: 'tank_c',
        variable: 'level',
        value: 2.0,
        timestamp: 1700000000.123
    }
}

// Control commands
{ type: 'pause' }
{ type: 'resume' }
{ type: 'reset' }
```

### Messages from Server to Client

```javascript
// Initial state
{
    type: 'initial_state',
    data: {
        variables: { /* current values */ },
        setpoints: { /* current setpoints */ },
        controls: { /* control signals */ }
    }
}

// State update (periodic)
{
    type: 'state_update',
    data: {
        timestamp: 1700000000.123,
        variables: {
            tank_c_level: 1.52,
            tank_c_concentration: 180.5,
            // ...
        },
        setpoints: { /* ... */ },
        controls: { /* ... */ }
    }
}
```

## 🐞 Error Handling

The frontend implements comprehensive error handling:

1. **API Errors**: Caught in `api.js` and displayed via `UI.showStatus()`
2. **WebSocket Errors**: Handled in `websocket.js` with auto-reconnection (up to 5 attempts)
3. **Form Validation**: Input types and min/max constraints in HTML
4. **Network Errors**: Displayed to user with actionable messages

## 🚀 Testing

### Manual Testing Checklist

**Real-time Mode:**
- [ ] Initialize with equilibrium point
- [ ] Connect WebSocket successfully
- [ ] Verify real-time data updates
- [ ] Send setpoint command
- [ ] Test pause/resume/reset
- [ ] Disconnect and reconnect

**SVG Synoptic:**
- [ ] Check that `#synoptic-board` receives the `loaded` class after `SVGSynoptic.initialize()`
- [ ] Confirm overlays update with process and control data
- [ ] Ensure `SVGSynoptic.resetOverlays()` is called when `UI.resetDataCards()` executes

### Browser Console

All modules log to console for debugging:
```javascript
// Enable verbose logging
const API_DEBUG = true;
const WS_DEBUG = true;
```

## 📝 Next Steps

1. **SVG Integration**: Load actual plant diagram into `#synoptic-board`
2. **Data Overlays**: Create positioned divs in `#data-overlays` to display values on SVG
3. **Charting**: Add time-series charts using Chart.js or similar library
4. **Historical Streaming Data**: Persist key metrics from the real-time feed
5. **Export Function**: Add CSV/JSON export for sampled real-time data

## 📚 Resources

- [Fetch API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [WebSocket API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [FastAPI WebSocket Guide](https://fastapi.tiangolo.com/advanced/websockets/)

---

**Built for UFMG Control Engineering - Tank Process Simulation Project**
