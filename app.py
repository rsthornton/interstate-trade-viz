"""
Interstate Trade Network Visualization - Reimagined UI/UX

Design principles:
1. The map IS the interface - everything else serves it
2. Progressive disclosure - show complexity on demand
3. State selection is the primary interaction
4. Controls feel like part of the map, not a separate panel
5. Information appears contextually

Author: Shingai Thornton
"""

from dash import Dash, html, dcc, callback, Output, Input, State, no_update, dash_table, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import pickle
from pathlib import Path


# =============================================================================
# DATA LOADING
# =============================================================================

def load_centralities(data_dir="data"):
    file_path = Path(data_dir) / "centralities_51x51.csv"
    df = pd.read_csv(file_path)
    df = df.rename(columns={'label': 'state'})
    return df


def load_network(data_dir="data"):
    file_path = Path(data_dir) / "network_graph.gpickle"
    with open(file_path, 'rb') as f:
        G = pickle.load(f)
    return G


def load_state_coords(data_dir="data"):
    file_path = Path(data_dir) / "state_coords.csv"
    return pd.read_csv(file_path)


def load_gdp(data_dir="data"):
    file_path = Path(data_dir) / "state_gdp_2017.csv"
    df = pd.read_csv(file_path)
    df['gdp_billions'] = df['gdp_2017_q4_millions'] / 1000
    df['gdp_rank'] = df['gdp_billions'].rank(ascending=False, method='min').astype(int)
    return df


def load_filtration_data(data_dir="data"):
    file_path = Path(data_dir) / "filtration_results_51x51.csv"
    df = pd.read_csv(file_path)
    df = df.rename(columns={'label': 'state'})
    
    filtration_data = {}
    for threshold_label in df['threshold_label'].unique():
        threshold_df = df[df['threshold_label'] == threshold_label].copy()
        threshold_df['rank_betweenness'] = threshold_df['betweenness'].rank(ascending=False, method='min')
        threshold_df['rank_eigenvector'] = threshold_df['eigenvector'].rank(ascending=False, method='min')
        threshold_df['rank_out_degree'] = threshold_df['out_degree'].rank(ascending=False, method='min')
        filtration_data[threshold_label] = threshold_df.reset_index(drop=True)
    
    return filtration_data


def get_top_edges(network, coords, centralities, top_n=50):
    id_to_label = dict(zip(centralities['state_id'], centralities['state']))
    coords_renamed = coords.rename(columns={'state_abbr': 'state'})
    coord_lookup = {row['state']: {'lat': row['lat'], 'lon': row['lon']} 
                    for _, row in coords_renamed.iterrows()}
    
    edges_with_weight = [
        (source, target, data['weight'])
        for source, target, data in network.edges(data=True)
    ]
    edges_sorted = sorted(edges_with_weight, key=lambda x: x[2], reverse=True)
    
    top_edges = []
    for source_id, target_id, weight in edges_sorted[:top_n]:
        source_label = id_to_label.get(source_id)
        target_label = id_to_label.get(target_id)
        
        if not source_label or not target_label:
            continue
        if source_label not in coord_lookup or target_label not in coord_lookup:
            continue
        
        top_edges.append({
            'source': source_label,
            'target': target_label,
            'weight': weight,
            'source_lat': coord_lookup[source_label]['lat'],
            'source_lon': coord_lookup[source_label]['lon'],
            'target_lat': coord_lookup[target_label]['lat'],
            'target_lon': coord_lookup[target_label]['lon']
        })
    
    return top_edges


# =============================================================================
# VISUALIZATION
# =============================================================================

def create_network_map(centralities, coordinates, centrality_measure='eigenvector',
                       selected_state=None, show_edges=False, edge_data=None, dark_mode=True):
    """Create the network map with refined styling."""
    
    coords = coordinates.rename(columns={'state_abbr': 'state'})
    df = centralities.merge(coords[['state', 'lat', 'lon']], on='state', how='inner')
    
    # Sizing
    min_size, max_size = 12, 55
    size_values = df[centrality_measure]
    sizes = min_size + (size_values / size_values.max()) * (max_size - min_size)
    
    color_values = df[centrality_measure]
    
    # Build hover text
    has_state_name = 'state_name' in df.columns
    has_gdp = 'gdp_billions' in df.columns
    
    hover_text = []
    for _, row in df.iterrows():
        display_name = row['state_name'] if has_state_name else row['state']
        text = f"<b>{display_name}</b><br>"
        if has_gdp and pd.notna(row['gdp_billions']):
            text += f"GDP: ${row['gdp_billions']:.1f}B (#{int(row['gdp_rank'])})<br>"
        text += f"<br><b>{centrality_measure.replace('_', ' ').title()}</b>: {row[centrality_measure]:.4f} (#{int(row[f'rank_{centrality_measure}'])})"
        hover_text.append(text)
    
    # Selection highlighting
    if selected_state:
        selected_mask = df['state'] == selected_state
        marker_sizes = [s * 1.4 if sel else s for s, sel in zip(sizes, selected_mask)]
        marker_opacities = [1.0 if sel else 0.5 for sel in selected_mask]
    else:
        marker_sizes = list(sizes)
        marker_opacities = 0.85
    
    # Color scheme based on mode
    if dark_mode:
        colorscale = 'Viridis'
        map_style = 'carto-darkmatter'
        paper_bg = '#1a1a2e'
        font_color = '#ffffff'
    else:
        colorscale = 'Viridis'
        map_style = 'carto-positron'
        paper_bg = '#ffffff'
        font_color = '#333333'
    
    fig = go.Figure()
    
    # Add edges first (behind nodes)
    if show_edges and edge_data:
        max_weight = max(e['weight'] for e in edge_data) if edge_data else 1
        for edge in edge_data:
            scaled_width = 0.5 + (edge['weight'] / max_weight) * 3
            
            # Highlight edges connected to selected state
            if selected_state and (edge['source'] == selected_state or edge['target'] == selected_state):
                edge_color = 'rgba(255, 193, 7, 0.7)'  # Gold for selected
                scaled_width *= 1.5
            else:
                edge_color = 'rgba(100, 149, 237, 0.3)' if dark_mode else 'rgba(70, 130, 180, 0.4)'
            
            fig.add_trace(go.Scattermapbox(
                lat=[edge['source_lat'], edge['target_lat']],
                lon=[edge['source_lon'], edge['target_lon']],
                mode='lines',
                line=dict(width=scaled_width, color=edge_color),
                hoverinfo='skip',
                showlegend=False
            ))
    
    # Add nodes
    fig.add_trace(go.Scattermapbox(
        lat=df['lat'],
        lon=df['lon'],
        mode='markers',
        marker=dict(
            size=marker_sizes,
            color=color_values,
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title=dict(
                    text=centrality_measure.replace('_', ' ').title(),
                    side='right',
                    font=dict(color=font_color, size=11)
                ),
                thickness=12,
                len=0.4,
                y=0.5,
                tickfont=dict(color=font_color, size=10),
                bgcolor='rgba(0,0,0,0.3)' if dark_mode else 'rgba(255,255,255,0.8)',
                borderwidth=0
            ),
            opacity=marker_opacities
        ),
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        customdata=df['state'].tolist(),
        name=''
    ))
    
    fig.update_layout(
        mapbox=dict(
            style=map_style,
            center=dict(lat=39.5, lon=-98.0),
            zoom=3.3
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=paper_bg,
        plot_bgcolor=paper_bg,
        showlegend=False,
        uirevision='constant'  # Prevents map from resetting on updates
    )
    
    return fig


# =============================================================================
# LOAD DATA
# =============================================================================

print("Loading data...")
centralities_base = load_centralities()
coords = load_state_coords()
network = load_network()
filtration_data = load_filtration_data()
gdp = load_gdp()

# Merge GDP and state_name into centralities
centralities_base = centralities_base.merge(
    gdp[['state_abbrev', 'gdp_billions', 'gdp_rank']],
    left_on='state', right_on='state_abbrev', how='left'
).drop(columns=['state_abbrev'])

centralities_base = centralities_base.merge(
    coords[['state_abbr', 'state_name']],
    left_on='state', right_on='state_abbr', how='left'
).drop(columns=['state_abbr'])

# Network stats
density = nx.density(network)
num_edges = network.number_of_edges()
num_nodes = len(centralities_base)
clustering_coef = nx.average_clustering(network, weight='weight')
reciprocity = nx.reciprocity(network)

print("Data loaded.")


# =============================================================================
# CUSTOM CSS
# =============================================================================

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
    color: rgba(255,255,255,0.5);
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
    color: rgba(255,255,255,0.5);
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
"""


# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
    ],
    title="Interstate Trade Network",
    suppress_callback_exceptions=True
)

# Inject custom CSS via index_string
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
''' + CUSTOM_CSS + '''
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

server = app.server


# =============================================================================
# LAYOUT
# =============================================================================

app.layout = html.Div([
    # Inject custom CSS via a hidden div with dangerouslySetInnerHTML workaround
    # Or better: we'll use inline styles and the app.index_string approach
    
    # Stores
    dcc.Store(id='selected-state', data=None),
    dcc.Store(id='show-edges-store', data=False),
    dcc.Store(id='table-expanded', data=False),
    dcc.Store(id='selected-measure', data='eigenvector'),
    dcc.Store(id='app-mode', data='explore'),  # 'explore' or 'analyze'
    
    # Main container
    html.Div(id='main-container', className='theme-light', children=[
        # Map
        dcc.Graph(
            id='network-map',
            config={
                'displayModeBar': False,
                'scrollZoom': True
            },
            style={'height': '100%', 'width': '100%'}
        ),
        
        # Floating controls (top-left)
        html.Div(id='floating-controls', children=[
            # Mode toggle
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button("🔍 Explore", id="btn-explore", color="light", size="sm", 
                              outline=False, className="mode-btn"),
                    dbc.Button("📊 Analyze", id="btn-analyze", color="light", size="sm",
                              outline=True, className="mode-btn"),
                ], size="sm", className="w-100 mb-3")
            ]),
            
            # Title
            html.Div([
                html.H5("U.S. Interstate Trade", className="mb-0 text-white", 
                       style={'fontWeight': '600', 'fontSize': '16px'}),
                html.Small("Network Analysis", className="text-muted")
            ], className="mb-3"),
            
            # Measure selector
            html.Div([
                html.Label("Centrality Measure", className="text-muted small mb-2 d-block"),
                html.Div([
                    dbc.Button("Eigenvector", id="btn-eigen", color="light", size="sm", 
                              className="me-1", n_clicks=0, outline=False),
                    dbc.Button("Out-Degree", id="btn-outdeg", color="light", size="sm",
                              className="me-1", n_clicks=0, outline=True),
                    dbc.Button("Betweenness", id="btn-between", color="light", size="sm",
                              n_clicks=0, outline=True),
                ], className="measure-pills")
            ], className="mb-3"),
            
            # Interpretation guide (Analyze mode only)
            html.Div(id='interpretation-section', style={'display': 'none'}),
            
            # Filtration slider (only for betweenness)
            html.Div(id='filtration-section', children=[
                html.Label("Edge Filter", className="text-muted small mb-2 d-block"),
                dcc.Slider(
                    id='filtration-slider',
                    min=0, max=3, step=1, value=0,
                    marks={0: 'All', 1: 'Light', 2: 'Med', 3: 'Strong'},
                    className="mb-2"
                )
            ], style={'display': 'none'}),
            
            # Edge toggle
            html.Div([
                dbc.Switch(
                    id='edge-toggle',
                    label="Show trade flows",
                    value=False,
                    className="text-white"
                )
            ], className="mb-2"),
            
            # Edge count slider
            html.Div(id='edge-count-section', children=[
                dcc.Slider(
                    id='edge-count-slider',
                    min=20, max=200, step=20, value=60,
                    marks={20: '20', 100: '100', 200: '200'},
                )
            ], style={'display': 'none'}),
            
            html.Hr(style={'borderColor': 'rgba(255,255,255,0.1)', 'margin': '12px 0'}),
            
            # Dark/Light mode toggle
            html.Div([
                dbc.Switch(
                    id='dark-mode-toggle',
                    label="Light mode",
                    value=False,
                    className="text-white"
                )
            ]),
            
        ], style={
            'position': 'absolute',
            'top': '20px',
            'left': '20px',
            'zIndex': '1000',
            'background': 'rgba(26, 26, 46, 0.9)',
            'backdropFilter': 'blur(10px)',
            'borderRadius': '12px',
            'padding': '16px',
            'minWidth': '200px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)'
        }),
        
        # State detail drawer (right side)
        html.Div(id='state-drawer', className="state-drawer hidden", children=[
            html.Div([
                html.Div([
                    html.H5(id='drawer-state-name', className="mb-0 drawer-title"),
                    html.Span(id='drawer-state-abbr', className="drawer-subtitle ms-2")
                ], style={'flex': '1'}),
                dbc.Button("×", id='close-drawer', color="link", 
                          className="close-btn p-0", style={'fontSize': '24px'})
            ], className="drawer-header d-flex align-items-center"),
            
            html.Div(id='drawer-content', className="drawer-body")
        ]),
        
        # Bottom sheet for rankings table
        html.Div(id='bottom-sheet', className="bottom-sheet collapsed", children=[
            html.Div([
                html.Div(className="handle-bar"),
                html.Span("Rankings Table", className="text-muted small ms-3")
            ], id='sheet-handle', className="sheet-handle"),
            
            html.Div([
                html.Div(id='rankings-table-container', style={'maxHeight': '300px', 'overflow': 'auto'})
            ], className="p-3")
        ]),
        
        # Stats badge (bottom-left) - Explore mode
        html.Div([
            html.Span(f"{num_nodes} states • {num_edges:,} trade flows • {density:.1%} connected")
        ], className="stats-badge", id='stats-badge'),
        
        # Expanded stats panel (bottom-left) - Analyze mode
        html.Div(id='stats-panel-expanded', children=[
            html.Div([
                html.Div("Network Metrics", className="stats-panel-title"),
                html.Div([
                    html.Div([
                        html.Span(f"{num_nodes}", className="stat-value"),
                        html.Span("States", className="stat-label")
                    ], className="stat-item"),
                    html.Div([
                        html.Span(f"{num_edges:,}", className="stat-value"),
                        html.Span("Edges", className="stat-label")
                    ], className="stat-item"),
                    html.Div([
                        html.Span(f"{density:.1%}", className="stat-value"),
                        html.Span("Density", className="stat-label")
                    ], className="stat-item"),
                    html.Div([
                        html.Span(f"{clustering_coef:.3f}", className="stat-value"),
                        html.Span("Clustering", className="stat-label")
                    ], className="stat-item"),
                    html.Div([
                        html.Span(f"{reciprocity:.1%}", className="stat-value"),
                        html.Span("Reciprocity", className="stat-label")
                    ], className="stat-item"),
                ], className="stats-grid")
            ])
        ], className="stats-panel-expanded", style={'display': 'none'}),
        
    ], style={
        'height': '100vh',
        'width': '100vw',
        'position': 'relative',
        'overflow': 'hidden',
        'backgroundColor': '#1a1a2e'
    })
    
], style={'margin': '0', 'padding': '0', 'overflow': 'hidden'})


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _format_divergence(gdp_rank, centrality_rank, text_color):
    """Format GDP vs centrality divergence with color coding."""
    if gdp_rank is None:
        return html.Span("—", style={'color': text_color, 'fontSize': '12px'})
    
    diff = gdp_rank - centrality_rank  # Positive = outperforms GDP
    
    if diff >= 10:
        color = '#2ecc71'  # Strong green
        symbol = '▲'
    elif diff >= 5:
        color = '#27ae60'  # Light green
        symbol = '▲'
    elif diff <= -10:
        color = '#e74c3c'  # Strong red
        symbol = '▼'
    elif diff <= -5:
        color = '#c0392b'  # Light red
        symbol = '▼'
    else:
        color = text_color
        symbol = '•'
    
    if diff == 0:
        display = "—"
    elif diff > 0:
        display = f"{symbol} +{diff}"
    else:
        display = f"{symbol} {diff}"
    
    return html.Span(display, style={'color': color, 'fontSize': '12px', 'fontWeight': '600'})


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output('btn-explore', 'outline'),
    Output('btn-analyze', 'outline'),
    Output('btn-explore', 'color'),
    Output('btn-analyze', 'color'),
    Output('app-mode', 'data'),
    Input('btn-explore', 'n_clicks'),
    Input('btn-analyze', 'n_clicks'),
    Input('dark-mode-toggle', 'value'),
)
def toggle_app_mode(explore_clicks, analyze_clicks, dark_mode):
    """Toggle between Explore and Analyze modes."""
    triggered = ctx.triggered_id
    
    btn_color = 'light' if dark_mode else 'secondary'
    
    if triggered == 'btn-analyze':
        return True, False, btn_color, btn_color, 'analyze'
    else:
        return False, True, btn_color, btn_color, 'explore'


@callback(
    Output('interpretation-section', 'children'),
    Output('interpretation-section', 'style'),
    Input('app-mode', 'data'),
    Input('selected-measure', 'data'),
    Input('dark-mode-toggle', 'value'),
)
def update_interpretation(mode, measure, dark_mode):
    """Show interpretation guide in Analyze mode."""
    if mode != 'analyze':
        return [], {'display': 'none'}
    
    if measure is None:
        measure = 'eigenvector'
    
    # Interpretation content
    interpretations = {
        'eigenvector': {
            'title': 'Eigenvector Centrality',
            'text': 'Measures influence through connections to other economically important states. High scores indicate structural power through relationships with economic powerhouses.',
            'insight_label': 'Key Finding',
            'insight_value': 'Robust across network changes (ρ > 0.98). Iowa: #31 GDP → #13 Eigenvector'
        },
        'out_degree': {
            'title': 'Weighted Out-Degree',
            'text': 'Quantifies direct distribution capacity—total outbound trade value. Closely tracks GDP but reveals trade-specific production capacity.',
            'insight_label': 'Correlation',
            'insight_value': 'High GDP alignment expected. Exceptions reveal trade-specific hubs.'
        },
        'betweenness': {
            'title': 'Betweenness Centrality',
            'text': 'Identifies states occupying bridging positions between regional clusters. Uses weight inversion (high trade = short distance) for meaningful computation.',
            'insight_label': 'Methodology',
            'insight_value': 'Rankings stable under filtration. Try the Edge Filter slider to verify.'
        }
    }
    
    info = interpretations.get(measure, interpretations['eigenvector'])
    
    content = html.Div([
        html.Div([
            html.Div(info['title'], className="interpretation-title"),
            html.P(info['text'], className="interpretation-text"),
        ], className="interpretation-card"),
        html.Div([
            html.Div(info['insight_label'], className="insight-label"),
            html.Div(info['insight_value'], className="insight-value")
        ], className="insight-highlight")
    ])
    
    return content, {'display': 'block', 'marginBottom': '12px'}


@callback(
    Output('stats-badge', 'style'),
    Output('stats-panel-expanded', 'style'),
    Input('app-mode', 'data'),
    Input('selected-state', 'data'),
    Input('dark-mode-toggle', 'value'),
)
def toggle_stats_display(mode, selected_state, dark_mode):
    """Switch between simple badge and expanded stats panel."""
    # Hide both if state is selected (drawer is open)
    if selected_state:
        return {'display': 'none'}, {'display': 'none'}
    
    if mode == 'analyze':
        badge_style = {'display': 'none'}
        panel_style = {
            'display': 'block',
            'position': 'absolute',
            'bottom': '20px',
            'left': '20px',
            'zIndex': '998',
            'background': 'rgba(26, 26, 46, 0.9)' if dark_mode else 'rgba(255, 255, 255, 0.95)',
            'backdropFilter': 'blur(10px)',
            'borderRadius': '12px',
            'padding': '16px',
            'minWidth': '280px'
        }
    else:
        badge_style = {'display': 'block'}
        panel_style = {'display': 'none'}
    
    return badge_style, panel_style


@callback(
    Output('btn-eigen', 'color'),
    Output('btn-outdeg', 'color'),
    Output('btn-between', 'color'),
    Output('btn-eigen', 'outline'),
    Output('btn-outdeg', 'outline'),
    Output('btn-between', 'outline'),
    Output('filtration-section', 'style'),
    Output('selected-measure', 'data'),
    Input('btn-eigen', 'n_clicks'),
    Input('btn-outdeg', 'n_clicks'),
    Input('btn-between', 'n_clicks'),
    Input('dark-mode-toggle', 'value'),
)
def update_measure_buttons(n1, n2, n3, dark_mode):
    """Update button states and show/hide filtration."""
    triggered = ctx.triggered_id
    
    # Determine which measure is selected
    if triggered == 'btn-outdeg':
        selected = 'out_degree'
    elif triggered == 'btn-between':
        selected = 'betweenness'
    else:
        selected = 'eigenvector'
    
    # Button color based on theme
    # In dark mode: use 'light' buttons (white text/bg)
    # In light mode: use 'dark' buttons (dark text/bg)
    btn_color = 'light' if dark_mode else 'secondary'
    
    # Set outline property (True = outline style, False = solid)
    eigen_outline = selected != 'eigenvector'
    outdeg_outline = selected != 'out_degree'
    between_outline = selected != 'betweenness'
    
    # Show filtration only for betweenness
    filtration_style = {'display': 'block'} if selected == 'betweenness' else {'display': 'none'}
    
    return btn_color, btn_color, btn_color, eigen_outline, outdeg_outline, between_outline, filtration_style, selected


@callback(
    Output('edge-count-section', 'style'),
    Input('edge-toggle', 'value')
)
def toggle_edge_count(show_edges):
    if show_edges:
        return {'display': 'block', 'marginTop': '8px'}
    return {'display': 'none'}


@callback(
    Output('network-map', 'figure'),
    Input('selected-measure', 'data'),
    Input('filtration-slider', 'value'),
    Input('edge-toggle', 'value'),
    Input('edge-count-slider', 'value'),
    Input('selected-state', 'data'),
    Input('dark-mode-toggle', 'value')
)
def update_map(measure, filtration, show_edges, edge_count, selected_state, dark_mode):
    """Update the map visualization."""
    if measure is None:
        measure = 'eigenvector'
    
    # Select centralities based on filtration
    filtration_map = {0: 'full_network', 1: 'threshold_1', 2: 'threshold_2', 3: 'threshold_3'}
    threshold_key = filtration_map.get(filtration, 'full_network')
    
    if measure == 'betweenness' and threshold_key != 'full_network':
        centralities = filtration_data[threshold_key].copy()
        centralities = centralities.merge(
            gdp[['state_abbrev', 'gdp_billions', 'gdp_rank']],
            left_on='state', right_on='state_abbrev', how='left'
        ).drop(columns=['state_abbrev'], errors='ignore')
        centralities = centralities.merge(
            coords[['state_abbr', 'state_name']],
            left_on='state', right_on='state_abbr', how='left'
        ).drop(columns=['state_abbr'], errors='ignore')
    else:
        centralities = centralities_base.copy()
    
    # Get edge data if needed
    edge_data = None
    if show_edges:
        if selected_state:
            # Get edges for selected state
            id_to_label = dict(zip(centralities['state_id'], centralities['state']))
            label_to_id = {v: k for k, v in id_to_label.items()}
            state_id = label_to_id.get(selected_state)
            
            coords_lookup = {r['state_abbr']: {'lat': r['lat'], 'lon': r['lon']}
                            for _, r in coords.iterrows()}
            
            edge_data = []
            for s, t, d in network.edges(data=True):
                s_label, t_label = id_to_label.get(s), id_to_label.get(t)
                if s == state_id or t == state_id:
                    if s_label and t_label and s_label in coords_lookup and t_label in coords_lookup:
                        edge_data.append({
                            'source': s_label, 'target': t_label, 'weight': d['weight'],
                            'source_lat': coords_lookup[s_label]['lat'],
                            'source_lon': coords_lookup[s_label]['lon'],
                            'target_lat': coords_lookup[t_label]['lat'],
                            'target_lon': coords_lookup[t_label]['lon']
                        })
        else:
            edge_data = get_top_edges(network, coords, centralities, top_n=edge_count or 60)
    
    fig = create_network_map(
        centralities, coords, measure,
        selected_state=selected_state,
        show_edges=show_edges,
        edge_data=edge_data,
        dark_mode=dark_mode
    )
    
    return fig


@callback(
    Output('selected-state', 'data'),
    Input('network-map', 'clickData'),
    Input('close-drawer', 'n_clicks'),
    State('selected-state', 'data'),
    prevent_initial_call=True
)
def handle_state_selection(click_data, close_clicks, current_state):
    """Handle state selection from map clicks."""
    triggered = ctx.triggered_id
    
    if triggered == 'close-drawer':
        return None
    
    if click_data and click_data.get('points'):
        point = click_data['points'][0]
        if 'customdata' in point:
            new_state = point['customdata']
            # Toggle off if clicking same state
            if new_state == current_state:
                return None
            return new_state
    
    return current_state


@callback(
    Output('state-drawer', 'style'),
    Output('drawer-state-name', 'children'),
    Output('drawer-state-abbr', 'children'),
    Output('drawer-content', 'children'),
    Input('selected-state', 'data'),
    Input('selected-measure', 'data'),
    Input('dark-mode-toggle', 'value'),
    Input('app-mode', 'data'),
)
def update_drawer(selected_state, measure, dark_mode, app_mode):
    """Update the state detail drawer."""
    if measure is None:
        measure = 'eigenvector'
    if app_mode is None:
        app_mode = 'explore'
    
    # Base drawer styles based on theme
    if dark_mode:
        base_style = {
            'position': 'absolute',
            'top': '20px',
            'right': '20px',
            'bottom': '20px',
            'width': '320px',
            'zIndex': '1000',
            'background': 'rgba(26, 26, 46, 0.95)',
            'backdropFilter': 'blur(10px)',
            'borderRadius': '12px',
            'boxShadow': '0 4px 30px rgba(0,0,0,0.4)',
            'overflow': 'hidden',
            'transition': 'transform 0.3s ease, opacity 0.3s ease'
        }
    else:
        base_style = {
            'position': 'absolute',
            'top': '20px',
            'right': '20px',
            'bottom': '20px',
            'width': '320px',
            'zIndex': '1000',
            'background': 'rgba(255, 255, 255, 0.98)',
            'backdropFilter': 'blur(10px)',
            'borderRadius': '12px',
            'boxShadow': '0 4px 30px rgba(0,0,0,0.15)',
            'overflow': 'hidden',
            'transition': 'transform 0.3s ease, opacity 0.3s ease',
            'color': '#333'
        }
    
    if not selected_state:
        # Hidden state
        base_style['transform'] = 'translateX(340px)'
        base_style['opacity'] = '0'
        base_style['pointerEvents'] = 'none'
        return base_style, "", "", ""
    
    # Get state data
    state_row = centralities_base[centralities_base['state'] == selected_state].iloc[0]
    state_name = state_row['state_name'] if 'state_name' in centralities_base.columns else selected_state
    
    # Calculate trade stats
    id_to_label = dict(zip(centralities_base['state_id'], centralities_base['state']))
    label_to_id = {v: k for k, v in id_to_label.items()}
    state_id = label_to_id[selected_state]
    
    outbound_value = sum(d['weight'] for s, t, d in network.edges(data=True) if s == state_id)
    inbound_value = sum(d['weight'] for s, t, d in network.edges(data=True) if t == state_id)
    
    # Get ranking for current measure
    rank = int(state_row[f'rank_{measure}'])
    gdp_rank = int(state_row['gdp_rank']) if 'gdp_rank' in state_row else None
    
    # Rank badge styling
    if rank <= 10:
        rank_class = "rank-badge top-10"
    elif rank <= 20:
        rank_class = "rank-badge top-20"
    else:
        rank_class = "rank-badge other"
    
    # Get top partners
    partners = []
    for s, t, d in network.edges(data=True):
        if s == state_id:
            partners.append((id_to_label[t], d['weight'], 'out'))
        elif t == state_id:
            partners.append((id_to_label[s], d['weight'], 'in'))
    partners.sort(key=lambda x: x[1], reverse=True)
    
    # Text colors based on mode
    text_color = 'white' if dark_mode else '#333'
    muted_color = 'rgba(255,255,255,0.5)' if dark_mode else '#666'
    bg_subtle = 'rgba(255,255,255,0.05)' if dark_mode else 'rgba(0,0,0,0.05)'
    border_color = 'rgba(255,255,255,0.05)' if dark_mode else 'rgba(0,0,0,0.08)'
    
    # Build drawer content
    content = html.Div([
        # Rank and measure
        html.Div([
            html.Div([
                html.Span(f"#{rank}", className=rank_class),
                html.Span(f" in {measure.replace('_', ' ').title()}", 
                         style={'color': muted_color, 'marginLeft': '8px', 'fontSize': '13px'})
            ]),
            html.Div([
                html.Small(f"GDP Rank: #{gdp_rank}" if gdp_rank else "", style={'color': muted_color})
            ], style={'marginTop': '4px'}) if gdp_rank else None
        ], style={'marginBottom': '20px'}),
        
        # Trade metrics
        html.Div([
            html.Div([
                html.Div(f"${outbound_value/1e9:.1f}B", className="metric-value", style={'color': text_color}),
                html.Div("Outbound", className="metric-label", style={'color': muted_color})
            ], className="metric-card", style={'flex': '1', 'background': bg_subtle}),
            html.Div([
                html.Div(f"${inbound_value/1e9:.1f}B", className="metric-value", style={'color': text_color}),
                html.Div("Inbound", className="metric-label", style={'color': muted_color})
            ], className="metric-card", style={'flex': '1', 'marginLeft': '10px', 'background': bg_subtle}),
        ], className="d-flex", style={'marginBottom': '20px'}),
        
        # Centrality scores
        html.Div([
            html.Label("Centrality Scores", style={'color': muted_color, 'fontSize': '12px', 'marginBottom': '8px', 'display': 'block'}),
            html.Div([
                html.Div([
                    html.Span("Eigenvector", style={'color': muted_color, 'fontSize': '12px'}),
                    html.Span(f"#{int(state_row['rank_eigenvector'])}", 
                             style={'color': text_color, 'fontSize': '12px'})
                ], className="d-flex justify-content-between"),
                html.Div([
                    html.Span("Out-Degree", style={'color': muted_color, 'fontSize': '12px'}),
                    html.Span(f"#{int(state_row['rank_out_degree'])}", 
                             style={'color': text_color, 'fontSize': '12px'})
                ], className="d-flex justify-content-between"),
                html.Div([
                    html.Span("Betweenness", style={'color': muted_color, 'fontSize': '12px'}),
                    html.Span(f"#{int(state_row['rank_betweenness'])}", 
                             style={'color': text_color, 'fontSize': '12px'})
                ], className="d-flex justify-content-between"),
            ], style={'background': bg_subtle, 'borderRadius': '8px', 'padding': '12px'})
        ], style={'marginBottom': '20px'}),
        
        # Top partners
        html.Div([
            html.Label("Top Trading Partners", style={'color': muted_color, 'fontSize': '12px', 'marginBottom': '8px', 'display': 'block'}),
            html.Div([
                html.Div([
                    html.Span(f"{p[0]}", style={'color': text_color}),
                    html.Span([
                        html.Span("→ " if p[2] == 'out' else "← ", style={'color': muted_color}),
                        f"${p[1]/1e9:.1f}B"
                    ], style={'color': muted_color})
                ], style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'padding': '8px 0',
                    'borderBottom': f'1px solid {border_color}',
                    'fontSize': '13px'
                })
                for p in partners[:8]
            ])
        ]),
        
        # GDP Divergence Analysis (Analyze mode only)
        html.Div(id='gdp-divergence-section', children=[
            html.Hr(style={'borderColor': border_color, 'margin': '16px 0'}),
            html.Label("GDP vs Centrality Divergence", style={'color': muted_color, 'fontSize': '12px', 'marginBottom': '8px', 'display': 'block'}),
            html.Div([
                html.Div([
                    html.Span("Eigenvector", style={'color': muted_color, 'fontSize': '12px'}),
                    html.Span([
                        _format_divergence(gdp_rank, int(state_row['rank_eigenvector']), text_color)
                    ])
                ], className="d-flex justify-content-between mb-1"),
                html.Div([
                    html.Span("Out-Degree", style={'color': muted_color, 'fontSize': '12px'}),
                    html.Span([
                        _format_divergence(gdp_rank, int(state_row['rank_out_degree']), text_color)
                    ])
                ], className="d-flex justify-content-between mb-1"),
                html.Div([
                    html.Span("Betweenness", style={'color': muted_color, 'fontSize': '12px'}),
                    html.Span([
                        _format_divergence(gdp_rank, int(state_row['rank_betweenness']), text_color)
                    ])
                ], className="d-flex justify-content-between"),
            ], style={'background': bg_subtle, 'borderRadius': '8px', 'padding': '12px'}),
            html.Small("Green = outperforms GDP rank, Red = underperforms", 
                      style={'color': muted_color, 'fontSize': '10px', 'marginTop': '8px', 'display': 'block'})
        ], style={'display': 'block' if (app_mode == 'analyze' and gdp_rank is not None) else 'none'})
    ])
    
    return base_style, state_name, f"({selected_state})", content


@callback(
    Output('bottom-sheet', 'className'),
    Input('sheet-handle', 'n_clicks'),
    State('bottom-sheet', 'className'),
    prevent_initial_call=True
)
def toggle_bottom_sheet(n_clicks, current_class):
    """Toggle the bottom sheet expansion."""
    if 'collapsed' in current_class:
        return "bottom-sheet"
    return "bottom-sheet collapsed"


@callback(
    Output('rankings-table-container', 'children'),
    Input('selected-measure', 'data'),
    Input('dark-mode-toggle', 'value'),
)
def update_rankings_table(measure, dark_mode):
    """Update rankings table."""
    if measure is None:
        measure = 'eigenvector'
    
    df = centralities_base[['state', 'state_name', 'gdp_rank', 'rank_eigenvector', 
                            'rank_out_degree', 'rank_betweenness']].copy()
    
    df = df.rename(columns={
        'state': 'Abbr',
        'state_name': 'State',
        'gdp_rank': 'GDP',
        'rank_eigenvector': 'Eigen',
        'rank_out_degree': 'OutDeg',
        'rank_betweenness': 'Betw'
    })
    
    for col in ['GDP', 'Eigen', 'OutDeg', 'Betw']:
        df[col] = df[col].astype(int)
    
    sort_map = {'eigenvector': 'Eigen', 'out_degree': 'OutDeg', 'betweenness': 'Betw'}
    df = df.sort_values(sort_map[measure]).reset_index(drop=True)
    
    # Theme-aware colors
    if dark_mode:
        text_color = 'white'
        bg_color = 'transparent'
        header_bg = 'rgba(255,255,255,0.05)'
        border_color = 'rgba(255,255,255,0.05)'
        green_bg = 'rgba(46, 204, 113, 0.3)'
        green_text = '#2ecc71'
        green_light_bg = 'rgba(46, 204, 113, 0.15)'
        red_bg = 'rgba(231, 76, 60, 0.3)'
        red_text = '#e74c3c'
        red_light_bg = 'rgba(231, 76, 60, 0.15)'
    else:
        text_color = '#333'
        bg_color = 'transparent'
        header_bg = 'rgba(0,0,0,0.05)'
        border_color = 'rgba(0,0,0,0.08)'
        green_bg = 'rgba(46, 204, 113, 0.25)'
        green_text = '#1a8a4c'
        green_light_bg = 'rgba(46, 204, 113, 0.12)'
        red_bg = 'rgba(231, 76, 60, 0.25)'
        red_text = '#c0392b'
        red_light_bg = 'rgba(231, 76, 60, 0.12)'
    
    # Compute styles
    style_data_conditional = []
    for idx, row in df.iterrows():
        gdp = row['GDP']
        for col in ['Eigen', 'OutDeg', 'Betw']:
            diff = gdp - row[col]
            if diff >= 10:
                style_data_conditional.append({
                    'if': {'row_index': idx, 'column_id': col},
                    'backgroundColor': green_bg,
                    'color': green_text
                })
            elif diff >= 5:
                style_data_conditional.append({
                    'if': {'row_index': idx, 'column_id': col},
                    'backgroundColor': green_light_bg,
                    'color': green_text
                })
            elif diff <= -10:
                style_data_conditional.append({
                    'if': {'row_index': idx, 'column_id': col},
                    'backgroundColor': red_bg,
                    'color': red_text
                })
            elif diff <= -5:
                style_data_conditional.append({
                    'if': {'row_index': idx, 'column_id': col},
                    'backgroundColor': red_light_bg,
                    'color': red_text
                })
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': c, 'id': c} for c in df.columns],
        sort_action='native',
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'center',
            'padding': '10px 8px',
            'fontSize': '12px',
            'backgroundColor': bg_color,
            'color': text_color,
            'border': 'none',
            'borderBottom': f'1px solid {border_color}'
        },
        style_header={
            'fontWeight': '600',
            'backgroundColor': header_bg,
            'borderBottom': f'1px solid {border_color}'
        },
        style_data_conditional=style_data_conditional,
        page_size=51
    )


# Update UI theme based on dark/light mode
@callback(
    Output('floating-controls', 'style'),
    Output('bottom-sheet', 'style'),
    Output('main-container', 'style'),
    Output('main-container', 'className'),
    Output('stats-badge', 'className'),
    Output('dark-mode-toggle', 'label'),
    Input('dark-mode-toggle', 'value'),
    State('selected-state', 'data')
)
def update_theme(dark_mode, selected_state):
    if dark_mode:
        floating_style = {
            'position': 'absolute',
            'top': '20px',
            'left': '20px',
            'zIndex': '1000',
            'background': 'rgba(26, 26, 46, 0.9)',
            'backdropFilter': 'blur(10px)',
            'borderRadius': '12px',
            'padding': '16px',
            'minWidth': '200px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.3)'
        }
        sheet_style = {
            'position': 'absolute',
            'bottom': '0',
            'left': '20px',
            'right': '20px',
            'zIndex': '999',
            'background': 'rgba(26, 26, 46, 0.95)',
            'backdropFilter': 'blur(10px)',
            'borderRadius': '12px 12px 0 0',
            'boxShadow': '0 -4px 20px rgba(0,0,0,0.3)'
        }
        container_style = {
            'height': '100vh',
            'width': '100vw',
            'position': 'relative',
            'overflow': 'hidden',
            'backgroundColor': '#1a1a2e'
        }
        container_class = "theme-dark"
        badge_class = "stats-badge"
        label = "Dark mode"
    else:
        floating_style = {
            'position': 'absolute',
            'top': '20px',
            'left': '20px',
            'zIndex': '1000',
            'background': 'rgba(255, 255, 255, 0.95)',
            'backdropFilter': 'blur(10px)',
            'borderRadius': '12px',
            'padding': '16px',
            'minWidth': '200px',
            'boxShadow': '0 4px 20px rgba(0,0,0,0.1)'
        }
        sheet_style = {
            'position': 'absolute',
            'bottom': '0',
            'left': '20px',
            'right': '20px',
            'zIndex': '999',
            'background': 'rgba(255, 255, 255, 0.98)',
            'backdropFilter': 'blur(10px)',
            'borderRadius': '12px 12px 0 0',
            'boxShadow': '0 -4px 20px rgba(0,0,0,0.1)'
        }
        container_style = {
            'height': '100vh',
            'width': '100vw',
            'position': 'relative',
            'overflow': 'hidden',
            'backgroundColor': '#f0f2f5'
        }
        container_class = "theme-light"
        badge_class = "stats-badge stats-badge-light"
        label = "Light mode"
    
    return floating_style, sheet_style, container_style, container_class, badge_class, label


# =============================================================================
# RUN
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=8050)
