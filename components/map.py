"""Network map visualization component."""

import plotly.graph_objects as go
import pandas as pd


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
