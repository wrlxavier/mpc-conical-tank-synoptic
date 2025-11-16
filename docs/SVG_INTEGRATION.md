# SVG Synoptic Integration

This document describes the SVG synoptic visualization feature added to the tank simulation system.

## Overview

The SVG synoptic module enables dynamic visualization of the tank process by loading the `tank_process.svg` diagram and overlaying real-time data on top of it. This provides an intuitive, visual representation of the process state.

## Features

### 1. **Dynamic SVG Loading**
- Automatically loads the SVG diagram on page initialization
- Responsive scaling to fit the container
- Graceful fallback with placeholder if SVG fails to load

### 2. **Real-time Data Overlays**
- 18 overlay elements displaying:
  - 8 process variables (levels and concentrations)
  - 10 actuator controls (supply valves, pumps, outlet valves for each tank)
- Overlay configuration is defined in `overlayConfig`
- Overlays update automatically with process and control data
- Visual feedback with color changes when data is active

### 3. **Interactive Features**
- Hover effects on overlays for better visibility
- Highlight animation for specific tanks
- Smooth transitions between states

### 4. **Responsive Design**
- Adapts to different screen sizes
- Mobile-friendly layout adjustments

## Architecture

### Files Added

#### `app/static/js/svg-synoptic.js`
Core module responsible for:
- Loading and displaying the SVG diagram
- Creating overlay elements
- Updating overlay values with process data
- Managing overlay states (active, highlighted)

**Key Functions:**
- `initialize(svgContainerId, overlayContainerId)`: Initialize the module
- `updateOverlays(variables, controls)`: Update all overlays with process and control data
- `resetOverlays()`: Reset overlays to default state
- `highlightTank(tankId, highlight)`: Highlight specific tank overlays

#### `app/static/css/svg-synoptic.css`
Styles for:
- SVG container layout
- Overlay positioning and appearance
- Animations and transitions
- Responsive breakpoints

### Files Modified

#### `app/static/index.html`
- Added link to `svg-synoptic.css`
- Added script tag for `svg-synoptic.js` (loaded before other scripts)

#### `app/static/js/app.js`
- Added SVG initialization in `init()` function
- SVG loads asynchronously on page load
- Adds 'loaded' class to synoptic board when successful

#### `app/static/js/ui.js`
- Integrated SVG overlay updates in `updateAllDataCards()`
- Integrated SVG overlay reset in `resetDataCards()`
- Ensures data cards and SVG overlays update synchronously

## Usage

The integration is **fully automatic** - no manual intervention needed. When the page loads:

1. `SVGSynoptic.initialize` is called inside `app.js` during `init()`
2. SVG is fetched and displayed
3. Overlay elements are created and positioned
4. On successful load, `#synoptic-board` receives the `loaded` class (see `svg-synoptic.css` for placeholder hiding)
5. Data updates from batch or real-time simulations automatically refresh both:
   - Data cards in the panel
   - SVG overlays on the diagram

## Customization

### Adjusting Overlay Positions

Overlay positions are defined in `svg-synoptic.css`. To adjust:

```css
/* Example: Move Tank C Level overlay */
#overlay-tank-c-level {
    top: 35%;  /* Adjust vertical position */
    left: 8%;  /* Adjust horizontal position */
}
```

### Styling Overlays

Modify these classes in `svg-synoptic.css`:

- `.svg-overlay`: Base overlay appearance
- `.svg-overlay.active`: Style when data is present
- `.svg-overlay.highlighted`: Style for highlighted state
- `.overlay-label`, `.overlay-value`, `.overlay-unit`: Text elements

### Adding New Overlays

To add overlays for additional variables:

1. **In `svg-synoptic.js`**, add to `overlayConfig` array:
```javascript
{ id: 'overlay-new-variable', label: 'New Variable', unit: 'unit', tank: 'X' }
```

2. **Add positioning in `svg-synoptic.css`**:
```css
#overlay-new-variable {
    top: 20%;
    left: 15%;
}
```

3. **Update in `updateOverlays()` function**:
```javascript
updateOverlay('overlay-new-variable', variables.new_variable, 2);
```

## Technical Details

### Module Pattern
The SVG synoptic uses the **Revealing Module Pattern** for encapsulation:
- Private variables: `svgContainer`, `overlayContainer`, `svgElement`
- Public API: `initialize`, `updateOverlays`, `resetOverlays`, `highlightTank`

### Data Flow

```
Backend Data → API/WebSocket → UI.updateAllDataCards() → SVGSynoptic.updateOverlays()
                                         ↓
                                   Data Cards Updated
                                         ↓
                                  SVG Overlays Updated
```

### Overlay Lifecycle
- Overlays are created on SVG load
- Updated via `updateOverlay` and `updateControlOverlay` functions
- Reset to default state via `resetOverlays` (called by `UI.resetDataCards()`)

### Control Scaling
- Actuator control values are displayed as percentages:
  $u_{\%} = 100 \times u$
- Scaling is performed in `updateControlOverlay` before rendering

### Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires ES6 support
- Uses Fetch API for SVG loading
- CSS Grid and Flexbox for layouts

## Troubleshooting

### SVG Not Loading
- Check browser console for errors
- Verify `tank_process.svg` exists in `app/static/imgs/`
- Ensure correct file permissions
- Check network tab for 404 errors

### Overlays Not Updating
- If control overlays show `--`, check if `UI.updateAllDataCards()` is forwarding the `controls` object (see `splitVariableMap` in `app/static/js/ui.js`)
- If SVG does not appear, confirm `tank_process.svg` exists and has read permissions

### Positioning Issues
- Adjust CSS values in `svg-synoptic.css`
- Use browser DevTools to inspect overlay positions
- Remember: positions are relative to SVG container

## Future Enhancements

Potential improvements:

1. **Interactive SVG Elements**: Click on tanks to view detailed information
2. **Animated Flow Indicators**: Visualize flow rates with animated pipes
3. **Color-coded Alerts**: Change overlay colors based on alarm conditions
4. **Historical Overlays**: Show trends with sparklines in overlays
5. **Drag-and-Drop Positioning**: GUI tool for adjusting overlay positions

## Integration with Control System

The SVG synoptic seamlessly integrates with:

- **Batch Simulation Mode**: Updates with final simulation values
- **Real-time Mode**: Updates continuously via WebSocket
- **MPC Controller**: Future integration for displaying control actions

---

**Last Updated**: November 15, 2025  
**Version**: 1.0.0  
**Author**: AI Assistant (via Perplexity)
