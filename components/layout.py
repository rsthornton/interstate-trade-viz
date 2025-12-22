"""Application layout definition."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from data_loader import num_nodes, num_edges, density, clustering_coef, reciprocity


# Centrality measure descriptions for info popovers
MEASURE_INFO = {
    'eigenvector': {
        'title': 'Eigenvector Centrality',
        'description': 'Measures influence through connections to other economically important states. High scores indicate structural power through relationships with economic powerhouses.'
    },
    'out_degree': {
        'title': 'Weighted Out-Degree',
        'description': 'Quantifies direct distribution capacity—total outbound trade value. Closely tracks GDP but reveals trade-specific production capacity.'
    },
    'betweenness': {
        'title': 'Betweenness Centrality',
        'description': 'Identifies states occupying bridging positions between regional clusters. Uses weight inversion (high trade = short distance) for meaningful computation.'
    }
}


def create_layout():
    """Create the main application layout."""
    return html.Div([
        # Stores
        dcc.Store(id='selected-state', data=None),
        dcc.Store(id='show-edges-store', data=False),
        dcc.Store(id='table-expanded', data=False),
        dcc.Store(id='selected-measure', data='eigenvector'),
        dcc.Store(id='network-type', data='51x51'),  # '51x51' or '52x52'
        dcc.Store(id='insight-visible', data=True),  # For floating insight card
        dcc.Store(id='insight-timestamp', data=0),   # Track when to auto-hide
        dcc.Interval(id='insight-timer', interval=1000, n_intervals=0),  # 1s timer for auto-hide

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

            # Floating controls (top-left) - COMPACT, never expands
            html.Div(id='floating-controls', children=[
                # Title
                html.Div([
                    html.H5("U.S. Interstate Trade", className="mb-0 text-white",
                           style={'fontWeight': '600', 'fontSize': '16px'}),
                    html.Small("Network Analysis", className="text-muted")
                ], className="mb-3"),

                # Measure selector with info icons
                html.Div([
                    html.Label("Centrality Measure", className="text-muted small mb-2 d-block"),
                    html.Div([
                        # Eigenvector button + info
                        html.Span([
                            dbc.Button("Eigenvector", id="btn-eigen", color="light", size="sm",
                                      className="me-1", n_clicks=0, outline=False),
                            html.Span("ⓘ", id="info-eigen", className="info-icon",
                                     style={'cursor': 'pointer', 'marginRight': '4px'}),
                        ]),
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(MEASURE_INFO['eigenvector']['title']),
                                dbc.PopoverBody(MEASURE_INFO['eigenvector']['description'])
                            ],
                            target="info-eigen", trigger="click", placement="right"
                        ),
                        # Out-Degree button + info
                        html.Span([
                            dbc.Button("Out-Degree", id="btn-outdeg", color="light", size="sm",
                                      className="me-1", n_clicks=0, outline=True),
                            html.Span("ⓘ", id="info-outdeg", className="info-icon",
                                     style={'cursor': 'pointer', 'marginRight': '4px'}),
                        ]),
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(MEASURE_INFO['out_degree']['title']),
                                dbc.PopoverBody(MEASURE_INFO['out_degree']['description'])
                            ],
                            target="info-outdeg", trigger="click", placement="right"
                        ),
                        # Betweenness button + info
                        html.Span([
                            dbc.Button("Betweenness", id="btn-between", color="light", size="sm",
                                      n_clicks=0, outline=True),
                            html.Span("ⓘ", id="info-between", className="info-icon",
                                     style={'cursor': 'pointer', 'marginLeft': '4px'}),
                        ]),
                        dbc.Popover(
                            [
                                dbc.PopoverHeader(MEASURE_INFO['betweenness']['title']),
                                dbc.PopoverBody(MEASURE_INFO['betweenness']['description'])
                            ],
                            target="info-between", trigger="click", placement="right"
                        ),
                    ], className="measure-pills", style={'display': 'flex', 'flexWrap': 'wrap', 'alignItems': 'center'})
                ], className="mb-3"),

                # Boundary sensitivity toggle (51x51 vs 52x52)
                html.Div([
                    html.Label("Network Boundary", className="text-muted small mb-2 d-block"),
                    dbc.ButtonGroup([
                        dbc.Button("Domestic", id="btn-51x51", color="light", size="sm",
                                  outline=False, className="mode-btn"),
                        dbc.Button("+ International", id="btn-52x52", color="light", size="sm",
                                  outline=True, className="mode-btn"),
                    ], size="sm", className="w-100")
                ], className="mb-3"),

                # Filtration slider (only for betweenness)
                html.Div(id='filtration-section', children=[
                    html.Label("Trade Volume Filter", className="text-muted small mb-2 d-block"),
                    dcc.Slider(
                        id='filtration-slider',
                        min=0, max=3, step=1, value=0,
                        marks={0: 'All', 1: 'Top 75%', 2: 'Top 50%', 3: 'Top 25%'},
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
                    html.Label("Top N Flows", className="text-muted small mb-2 d-block"),
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
                'maxWidth': '240px',  # Constrain width
                'boxShadow': '0 4px 20px rgba(0,0,0,0.3)'
            }),

            # Floating insight card (bottom-right)
            html.Div(id='insight-card', children=[
                html.Div([
                    html.Span("KEY INSIGHT", className="insight-card-label"),
                    html.Button("×", id='dismiss-insight', className="insight-dismiss-btn")
                ], className="insight-card-header"),
                html.Div(id='insight-card-content', className="insight-card-body")
            ], className="insight-card", style={'display': 'block'}),

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

            # Stats badge (bottom-left) - always visible, compact
            html.Div([
                html.Span(f"{num_nodes} states • {num_edges:,} edges • {density:.1%} density • {clustering_coef:.3f} clustering")
            ], className="stats-badge", id='stats-badge'),

        ], style={
            'height': '100vh',
            'width': '100vw',
            'position': 'relative',
            'overflow': 'hidden',
            'backgroundColor': '#1a1a2e'
        })

    ], style={'margin': '0', 'padding': '0', 'overflow': 'hidden'})
