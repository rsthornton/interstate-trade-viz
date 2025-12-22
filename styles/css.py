"""Custom CSS styles for the Interstate Trade visualization."""

CUSTOM_CSS = """
/* Full-height map container */
.map-container {
    position: relative;
    height: calc(100vh - 20px);
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
}

/* Mode toggle */
.mode-btn {
    flex: 1;
    font-size: 12px !important;
    padding: 6px 12px !important;
}

/* Interpretation card */
.interpretation-card {
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
    border-left: 3px solid #667eea;
}

.interpretation-title {
    font-size: 11px;
    font-weight: 600;
    color: #667eea;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.interpretation-text {
    font-size: 12px;
    color: rgba(255,255,255,0.8);
    line-height: 1.5;
    margin: 0;
}

.theme-light .interpretation-card {
    background: rgba(0,0,0,0.03);
    border-left-color: #5a67d8;
}

.theme-light .interpretation-text {
    color: #444;
}

/* Key insight highlight */
.insight-highlight {
    background: linear-gradient(135deg, rgba(102,126,234,0.15) 0%, rgba(118,75,162,0.15) 100%);
    border-radius: 8px;
    padding: 12px;
    margin-top: 12px;
}

.insight-label {
    font-size: 10px;
    font-weight: 600;
    color: #667eea;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.insight-value {
    font-size: 14px;
    font-weight: 600;
    color: white;
    margin-top: 4px;
}

.theme-light .insight-value {
    color: #333;
}

/* Expanded stats panel */
.stats-panel-expanded {
    position: absolute;
    bottom: 20px;
    left: 20px;
    z-index: 998;
    background: rgba(26, 26, 46, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 16px;
    min-width: 280px;
}

.stats-panel-title {
    font-size: 11px;
    font-weight: 600;
    color: rgba(255,255,255,0.7);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
}

.stats-grid {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}

.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 50px;
}

.stat-value {
    font-size: 16px;
    font-weight: 600;
    color: white;
}

.stat-label {
    font-size: 10px;
    color: rgba(255,255,255,0.7);
    text-transform: uppercase;
}

.theme-light .stats-panel-expanded {
    background: rgba(255, 255, 255, 0.95);
}

.theme-light .stats-panel-title {
    color: #666;
}

.theme-light .stat-value {
    color: #333;
}

.theme-light .stat-label {
    color: #666;
}

/* Floating control panel */
.floating-controls {
    position: absolute;
    top: 20px;
    left: 20px;
    z-index: 1000;
    background: rgba(26, 26, 46, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 16px;
    min-width: 200px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* Measure selector pills */
.measure-pills .btn {
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    margin: 2px;
    border: none;
    transition: all 0.2s ease;
}

.measure-pills .btn-outline-light {
    color: rgba(255,255,255,0.7);
    border: 1px solid rgba(255,255,255,0.2);
}

.measure-pills .btn-outline-light:hover {
    background: rgba(255,255,255,0.1);
    color: white;
}

.measure-pills .btn-light {
    background: white;
    color: #1a1a2e;
}

/* State drawer */
.state-drawer {
    position: absolute;
    top: 20px;
    right: 20px;
    bottom: 20px;
    width: 320px;
    z-index: 1000;
    background: rgba(26, 26, 46, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    box-shadow: 0 4px 30px rgba(0,0,0,0.4);
    overflow: hidden;
    transition: transform 0.3s ease, opacity 0.3s ease;
}

.state-drawer.hidden {
    transform: translateX(340px);
    opacity: 0;
    pointer-events: none;
}

.drawer-header {
    padding: 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.theme-light .drawer-header {
    border-bottom: 1px solid rgba(0,0,0,0.1) !important;
}

.drawer-body {
    padding: 20px;
    overflow-y: auto;
    max-height: calc(100% - 80px);
}

/* Bottom sheet for table */
.bottom-sheet {
    position: absolute;
    bottom: 0;
    left: 20px;
    right: 20px;
    z-index: 999;
    background: rgba(26, 26, 46, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 12px 12px 0 0;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.3);
    transition: transform 0.3s ease;
}

.bottom-sheet.collapsed {
    transform: translateY(calc(100% - 50px));
}

.sheet-handle {
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.sheet-handle:hover {
    background: rgba(255,255,255,0.05);
}

.handle-bar {
    width: 40px;
    height: 4px;
    background: rgba(255,255,255,0.3);
    border-radius: 2px;
}

/* Drawer styling */
.drawer-title {
    color: white;
}

.drawer-subtitle {
    color: rgba(255,255,255,0.5);
}

.close-btn {
    color: white !important;
    text-decoration: none !important;
}

.theme-light .drawer-title {
    color: #333 !important;
}

.theme-light .drawer-subtitle {
    color: #666 !important;
}

.theme-light .close-btn {
    color: #333 !important;
}

/* Stats badge */
.stats-badge {
    position: absolute;
    bottom: 20px;
    left: 20px;
    z-index: 998;
    background: rgba(26, 26, 46, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 11px;
    color: rgba(255,255,255,0.6);
}

.stats-badge-light {
    background: rgba(255, 255, 255, 0.9) !important;
    color: rgba(0,0,0,0.6) !important;
}

/* Light mode overrides */
.theme-light .text-white {
    color: #333 !important;
}

.theme-light .text-muted {
    color: #666 !important;
}

.theme-light .form-check-label {
    color: #333 !important;
}

.theme-light h5, .theme-light h6 {
    color: #333 !important;
}

.theme-light [class*="btn-outline"] {
    color: #333 !important;
    border-color: #ccc !important;
}

.theme-light [class*="btn-outline"]:hover {
    background-color: rgba(0,0,0,0.05) !important;
}

.theme-light .form-switch .form-check-input {
    background-color: #ccc;
}

.theme-light .form-switch .form-check-input:checked {
    background-color: #0d6efd;
}

.theme-light label {
    color: #666 !important;
}

.theme-light small {
    color: #666 !important;
}

.theme-light .handle-bar {
    background: rgba(0,0,0,0.3) !important;
}

.theme-light .sheet-handle span {
    color: #666 !important;
}

/* Slider styling for light mode */
.theme-light .rc-slider-track {
    background-color: #0d6efd !important;
}

.theme-light .rc-slider-rail {
    background-color: #ddd !important;
}

.theme-light .rc-slider-dot {
    border-color: #ccc !important;
}

.theme-light .rc-slider-mark-text {
    color: #666 !important;
}

/* Typography */
.text-gradient {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 12px;
    text-align: center;
}

.metric-value {
    font-size: 20px;
    font-weight: 600;
    color: white;
}

.metric-label {
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Partner list */
.partner-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 13px;
}

.partner-item:last-child {
    border-bottom: none;
}

/* Rank indicator */
.rank-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    font-size: 12px;
    font-weight: 600;
}

.rank-badge.top-10 {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
}

.rank-badge.top-20 {
    background: rgba(255,193,7,0.2);
    color: #ffc107;
}

.rank-badge.other {
    background: rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.6);
}

/* Info icons for centrality measures */
.info-icon {
    font-size: 12px;
    color: rgba(255,255,255,0.4);
    cursor: pointer;
    transition: color 0.2s ease;
    vertical-align: middle;
}

.info-icon:hover {
    color: rgba(255,255,255,0.8);
}

.theme-light .info-icon {
    color: rgba(0,0,0,0.3);
}

.theme-light .info-icon:hover {
    color: rgba(0,0,0,0.7);
}

/* Popover styling */
.popover {
    max-width: 280px;
}

.popover-header {
    font-size: 13px;
    font-weight: 600;
}

.popover-body {
    font-size: 12px;
    line-height: 1.5;
}
"""
