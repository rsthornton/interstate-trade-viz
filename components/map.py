"""Network map visualization component."""

import plotly.graph_objects as go
import pandas as pd


def create_network_map(centralities, coordinates, centrality_measure='eigenvector',
                       selected_state=None, show_edges=False, edge_data=None, dark_mode=True,
                       rank_changes=None, network_type='51x51'):
    """Create the network map with refined styling.

    Args:
        rank_changes: DataFrame with columns like 'betweenness_change', 'eigenvector_change'
                     Positive = rank improved when intl added, negative = rank worsened
        network_type: '51x51' or '52x52' - only show indicators when comparing (52x52)
    """

    coords = coordinates.rename(columns={'state_abbr': 'state'})
    df = centralities.merge(coords[['state', 'lat', 'lon']], on='state', how='inner')

    # Merge rank changes if provided
    if rank_changes is not None and network_type == '52x52':
        df = df.merge(rank_changes, on='state', how='left')

    # Sizing
    min_size, max_size = 12, 55
    size_values = df[centrality_measure]
    sizes = min_size + (size_values / size_values.max()) * (max_size - min_size)

    color_values = df[centrality_measure]

    # Build hover text
    has_state_name = 'state_name' in df.columns
    has_gdp = 'gdp_billions' in df.columns
    change_col = f'{centrality_measure}_change'
    has_rank_change = change_col in df.columns

    hover_text = []
    for _, row in df.iterrows():
        display_name = row['state_name'] if has_state_name else row['state']
        text = f"<b>{display_name}</b><br>"
        if has_gdp and pd.notna(row['gdp_billions']):
            text += f"GDP: ${row['gdp_billions']:.1f}B (#{int(row['gdp_rank'])})<br>"
        text += f"<br><b>{centrality_measure.replace('_', ' ').title()}</b>: {row[centrality_measure]:.4f} (#{int(row[f'rank_{centrality_measure}'])})"

        # Add rank change info if available (52x52 mode)
        if has_rank_change and pd.notna(row[change_col]):
            change = int(row[change_col])
            if change > 0:
                text += f"<br><span style='color:#2ecc71'>▲ +{change} vs domestic</span>"
            elif change < 0:
                text += f"<br><span style='color:#e74c3c'>▼ {change} vs domestic</span>"
            else:
                text += f"<br>— No change vs domestic"

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
    # Hover enabled via invisible midpoint markers - capped at 1000 edges for performance
    if show_edges and edge_data:
        max_weight = max(e['weight'] for e in edge_data) if edge_data else 1

        # Group bidirectional edges by state pair for combined hover
        edge_pairs = {}  # (stateA, stateB) sorted -> {out: weight, in: weight, coords}

        for edge in edge_data:
            # Create canonical key (alphabetically sorted pair)
            pair_key = tuple(sorted([edge['source'], edge['target']]))

            if pair_key not in edge_pairs:
                edge_pairs[pair_key] = {
                    'coords': (edge['source_lat'], edge['source_lon'],
                              edge['target_lat'], edge['target_lon']),
                    'flows': {}
                }

            # Store flow by direction
            direction = f"{edge['source']}→{edge['target']}"
            edge_pairs[pair_key]['flows'][direction] = edge['weight']

        # Now render edges and build hover layer
        midpoint_lats = []
        midpoint_lons = []
        midpoint_texts = []
        midpoint_sizes = []

        for pair_key, pair_data in edge_pairs.items():
            coords_data = pair_data['coords']
            flows = pair_data['flows']
            total_weight = sum(flows.values())

            scaled_width = 0.5 + (total_weight / max_weight) * 3

            # Highlight edges connected to selected state
            if selected_state and selected_state in pair_key:
                edge_color = 'rgba(255, 193, 7, 0.7)'  # Gold for selected
                scaled_width *= 1.5
            else:
                edge_color = 'rgba(100, 149, 237, 0.3)' if dark_mode else 'rgba(70, 130, 180, 0.4)'

            # Add line trace (visual)
            fig.add_trace(go.Scattermapbox(
                lat=[coords_data[0], coords_data[2]],
                lon=[coords_data[1], coords_data[3]],
                mode='lines',
                line=dict(width=scaled_width, color=edge_color),
                hoverinfo='skip',
                showlegend=False
            ))

            # Build hover text showing both directions
            mid_lat = (coords_data[0] + coords_data[2]) / 2
            mid_lon = (coords_data[1] + coords_data[3]) / 2

            state_a, state_b = pair_key
            flow_lines = []
            for direction, weight in sorted(flows.items()):
                flow_lines.append(f"{direction}: ${weight/1e9:.1f}B")

            hover_text = f"<b>{state_a} ↔ {state_b}</b><br>" + "<br>".join(flow_lines)

            midpoint_lats.append(mid_lat)
            midpoint_lons.append(mid_lon)
            midpoint_texts.append(hover_text)
            midpoint_sizes.append(max(scaled_width * 4, 15))  # Min size for hit area

        # Add single trace with all midpoints for efficient hover
        if midpoint_lats:
            fig.add_trace(go.Scattermapbox(
                lat=midpoint_lats,
                lon=midpoint_lons,
                mode='markers',
                marker=dict(
                    size=midpoint_sizes,
                    color='rgba(0,0,0,0)',  # Invisible
                    opacity=0
                ),
                text=midpoint_texts,
                hovertemplate='%{text}<extra></extra>',
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

    # Add rank change indicator labels (52x52 mode only, for significant changes)
    if has_rank_change:
        indicator_lats = []
        indicator_lons = []
        indicator_texts = []
        indicator_colors = []

        for _, row in df.iterrows():
            if pd.notna(row[change_col]):
                change = int(row[change_col])
                # Only show indicators for significant changes (|change| >= 3)
                if abs(change) >= 3:
                    indicator_lats.append(row['lat'] + 0.8)  # Offset slightly north
                    indicator_lons.append(row['lon'])
                    if change > 0:
                        indicator_texts.append(f"▲{change}")
                        indicator_colors.append('#2ecc71')  # Green
                    else:
                        indicator_texts.append(f"▼{abs(change)}")
                        indicator_colors.append('#e74c3c')  # Red

        if indicator_lats:
            # Add each indicator separately to control color
            for lat, lon, text, color in zip(indicator_lats, indicator_lons, indicator_texts, indicator_colors):
                fig.add_trace(go.Scattermapbox(
                    lat=[lat],
                    lon=[lon],
                    mode='text',
                    text=[text],
                    textfont=dict(size=11, color=color, family='Arial Black'),
                    hoverinfo='skip',
                    showlegend=False
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
