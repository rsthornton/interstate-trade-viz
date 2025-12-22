"""Application layout definition."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from data_loader import num_nodes, num_edges, density, clustering_coef, reciprocity


def create_layout():
    """Create the main application layout."""
    return html.Div([
        # Stores
        dcc.Store(id='selected-state', data=None),
        dcc.Store(id='show-edges-store', data=False),
        dcc.Store(id='table-expanded', data=False),
        dcc.Store(id='selected-measure', data='eigenvector'),
        dcc.Store(id='app-mode', data='explore'),
        dcc.Store(id='network-type', data='51x51'),  # '51x51' or '52x52'

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

                # Boundary sensitivity toggle (51x51 vs 52x52)
                html.Div([
                    html.Label("Network Boundary", className="text-muted small mb-2 d-block"),
                    dbc.ButtonGroup([
                        dbc.Button("Domestic", id="btn-51x51", color="light", size="sm",
                                  outline=False, className="mode-btn"),
                        dbc.Button("+ Intl", id="btn-52x52", color="light", size="sm",
                                  outline=True, className="mode-btn"),
                    ], size="sm", className="w-100")
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
