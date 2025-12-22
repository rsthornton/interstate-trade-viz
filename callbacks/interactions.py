"""Dash callbacks for user interactions."""

from dash import html, callback, Output, Input, State, ctx, dash_table
from components.map import create_network_map
from data_loader import (
    centralities_base, centralities_51x51, centralities_52x52, rank_changes,
    coords, network, gdp, filtration_data,
    get_top_edges
)


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


def register_callbacks(app):
    """Register all callbacks with the Dash app."""

    @app.callback(
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

    @app.callback(
        Output('btn-51x51', 'outline'),
        Output('btn-52x52', 'outline'),
        Output('btn-51x51', 'color'),
        Output('btn-52x52', 'color'),
        Output('network-type', 'data'),
        Input('btn-51x51', 'n_clicks'),
        Input('btn-52x52', 'n_clicks'),
        Input('dark-mode-toggle', 'value'),
    )
    def toggle_network_type(n1, n2, dark_mode):
        """Toggle between 51x51 (domestic) and 52x52 (with international)."""
        triggered = ctx.triggered_id

        btn_color = 'light' if dark_mode else 'secondary'

        if triggered == 'btn-52x52':
            return True, False, btn_color, btn_color, '52x52'
        else:
            return False, True, btn_color, btn_color, '51x51'

    @app.callback(
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

        interpretations = {
            'eigenvector': {
                'title': 'Eigenvector Centrality',
                'text': 'Measures influence through connections to other economically important states. High scores indicate structural power through relationships with economic powerhouses.',
                'insight_label': 'Key Insight',
                'insight_value': 'Robust across network changes (ρ > 0.98). Iowa: #31 GDP → #13 Eigenvector'
            },
            'out_degree': {
                'title': 'Weighted Out-Degree',
                'text': 'Quantifies direct distribution capacity—total outbound trade value. Closely tracks GDP but reveals trade-specific production capacity.',
                'insight_label': 'Key Insight',
                'insight_value': 'High GDP alignment expected. Exceptions like FL (#4 GDP, #14 OutDeg) reveal consumption vs production hubs.'
            },
            'betweenness': {
                'title': 'Betweenness Centrality',
                'text': 'Identifies states occupying bridging positions between regional clusters. Uses weight inversion (high trade = short distance) for meaningful computation.',
                'insight_label': 'Key Insight',
                'insight_value': 'Rankings stable under filtration. CA and TX dominate as national trade bridges.'
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

    @app.callback(
        Output('stats-badge', 'style'),
        Output('stats-panel-expanded', 'style'),
        Input('app-mode', 'data'),
        Input('selected-state', 'data'),
        Input('dark-mode-toggle', 'value'),
    )
    def toggle_stats_display(mode, selected_state, dark_mode):
        """Switch between simple badge and expanded stats panel."""
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

    @app.callback(
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

        if triggered == 'btn-outdeg':
            selected = 'out_degree'
        elif triggered == 'btn-between':
            selected = 'betweenness'
        else:
            selected = 'eigenvector'

        btn_color = 'light' if dark_mode else 'secondary'

        eigen_outline = selected != 'eigenvector'
        outdeg_outline = selected != 'out_degree'
        between_outline = selected != 'betweenness'

        filtration_style = {'display': 'block'} if selected == 'betweenness' else {'display': 'none'}

        return btn_color, btn_color, btn_color, eigen_outline, outdeg_outline, between_outline, filtration_style, selected

    @app.callback(
        Output('edge-count-section', 'style'),
        Input('edge-toggle', 'value')
    )
    def toggle_edge_count(show_edges):
        if show_edges:
            return {'display': 'block', 'marginTop': '8px'}
        return {'display': 'none'}

    @app.callback(
        Output('network-map', 'figure'),
        Input('selected-measure', 'data'),
        Input('filtration-slider', 'value'),
        Input('edge-toggle', 'value'),
        Input('edge-count-slider', 'value'),
        Input('selected-state', 'data'),
        Input('dark-mode-toggle', 'value'),
        Input('network-type', 'data')
    )
    def update_map(measure, filtration, show_edges, edge_count, selected_state, dark_mode, network_type):
        """Update the map visualization."""
        if measure is None:
            measure = 'eigenvector'
        if network_type is None:
            network_type = '51x51'

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
            # Select dataset based on network type
            if network_type == '52x52':
                # Use 52x52 but filter out RoW (no map coords for Rest of World)
                centralities = centralities_52x52[centralities_52x52['state'] != 'RoW'].copy()
            else:
                centralities = centralities_51x51.copy()

        edge_data = None
        if show_edges:
            if selected_state:
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
            dark_mode=dark_mode,
            rank_changes=rank_changes,
            network_type=network_type
        )

        return fig

    @app.callback(
        Output('selected-state', 'data'),
        Input('network-map', 'clickData'),
        Input('close-drawer', 'n_clicks'),
        Input('rankings-table', 'active_cell'),
        State('rankings-table', 'data'),
        State('selected-state', 'data'),
        prevent_initial_call=True
    )
    def handle_state_selection(click_data, close_clicks, active_cell, table_data, current_state):
        """Handle state selection from map clicks or table row clicks."""
        triggered = ctx.triggered_id

        if triggered == 'close-drawer':
            return None

        # Handle table row click
        if triggered == 'rankings-table' and active_cell:
            row_idx = active_cell['row']
            if table_data and row_idx < len(table_data):
                new_state = table_data[row_idx]['Abbr']
                if new_state == current_state:
                    return None
                return new_state

        # Handle map click
        if click_data and click_data.get('points'):
            point = click_data['points'][0]
            if 'customdata' in point:
                new_state = point['customdata']
                if new_state == current_state:
                    return None
                return new_state

        return current_state

    @app.callback(
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
            base_style['transform'] = 'translateX(340px)'
            base_style['opacity'] = '0'
            base_style['pointerEvents'] = 'none'
            return base_style, "", "", ""

        state_row = centralities_base[centralities_base['state'] == selected_state].iloc[0]
        state_name = state_row['state_name'] if 'state_name' in centralities_base.columns else selected_state

        id_to_label = dict(zip(centralities_base['state_id'], centralities_base['state']))
        label_to_id = {v: k for k, v in id_to_label.items()}
        state_id = label_to_id[selected_state]

        outbound_value = sum(d['weight'] for s, t, d in network.edges(data=True) if s == state_id)
        inbound_value = sum(d['weight'] for s, t, d in network.edges(data=True) if t == state_id)

        rank = int(state_row[f'rank_{measure}'])
        gdp_rank = int(state_row['gdp_rank']) if 'gdp_rank' in state_row else None

        if rank <= 10:
            rank_class = "rank-badge top-10"
        elif rank <= 20:
            rank_class = "rank-badge top-20"
        else:
            rank_class = "rank-badge other"

        partners = []
        for s, t, d in network.edges(data=True):
            if s == state_id:
                partners.append((id_to_label[t], d['weight'], 'out'))
            elif t == state_id:
                partners.append((id_to_label[s], d['weight'], 'in'))
        partners.sort(key=lambda x: x[1], reverse=True)

        text_color = 'white' if dark_mode else '#333'
        muted_color = 'rgba(255,255,255,0.5)' if dark_mode else '#666'
        bg_subtle = 'rgba(255,255,255,0.05)' if dark_mode else 'rgba(0,0,0,0.05)'
        border_color = 'rgba(255,255,255,0.05)' if dark_mode else 'rgba(0,0,0,0.08)'

        content = html.Div([
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

    @app.callback(
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

    @app.callback(
        Output('rankings-table-container', 'children'),
        Input('selected-measure', 'data'),
        Input('dark-mode-toggle', 'value'),
        Input('selected-state', 'data'),
    )
    def update_rankings_table(measure, dark_mode, selected_state):
        """Update rankings table with row selection highlighting."""
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

        style_data_conditional = []
        for idx, row in df.iterrows():
            gdp_val = row['GDP']
            for col in ['Eigen', 'OutDeg', 'Betw']:
                diff = gdp_val - row[col]
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

        # Add highlighting for selected state row
        selected_bg = 'rgba(255, 193, 7, 0.3)' if dark_mode else 'rgba(255, 193, 7, 0.4)'
        if selected_state:
            selected_idx = df[df['Abbr'] == selected_state].index.tolist()
            if selected_idx:
                style_data_conditional.append({
                    'if': {'row_index': selected_idx[0]},
                    'backgroundColor': selected_bg,
                    'fontWeight': '600'
                })

        return dash_table.DataTable(
            id='rankings-table',
            data=df.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in df.columns],
            sort_action='native',
            fixed_rows={'headers': True},
            style_table={'overflowX': 'auto', 'overflowY': 'auto', 'maxHeight': '280px'},
            style_cell={
                'textAlign': 'center',
                'padding': '10px 8px',
                'fontSize': '12px',
                'backgroundColor': bg_color,
                'color': text_color,
                'border': 'none',
                'borderBottom': f'1px solid {border_color}',
                'cursor': 'pointer'
            },
            style_header={
                'fontWeight': '600',
                'backgroundColor': header_bg,
                'borderBottom': f'1px solid {border_color}',
                'cursor': 'default'
            },
            style_data_conditional=style_data_conditional,
            page_size=51
        )

    @app.callback(
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
