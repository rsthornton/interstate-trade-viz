# Interstate Trade Network Visualization

Interactive tool for exploring U.S. interstate trade networks using centrality measures. Built for SSIE-641 (Advanced Network Science) at Binghamton University, Fall 2025.

**Author**: Shingai Thornton
**Framework**: Jang & Yang (2023) three-level centrality analysis

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Opens at http://localhost:8050

## Data

- **Source**: U.S. Census Bureau [CFS 2017 Public Use File](https://www2.census.gov/programs-surveys/cfs/datasets/2017/)
- **Network**: 51 nodes (50 states + DC), ~2,500 directed edges
- **Weights**: Survey-adjusted trade values

## Features

- Dark/light mode toggle
- Explore vs Analyze modes
- Interactive map with state selection
- Floating controls and state detail drawer
- Rankings table with GDP divergence coloring
- Filtration slider for betweenness stability analysis

## Architecture (Dash vs Streamlit)

| Aspect | Streamlit | Dash |
|--------|-----------|------|
| Layout | `st.sidebar`, `st.columns` | Bootstrap grid, full CSS control |
| State | `st.session_state` + `st.rerun()` | `dcc.Store` + callbacks |
| Click handling | `on_select="rerun"` workaround | Native `clickData` property |
| Styling | Limited themes | Bootstrap themes, custom CSS |
| URL routing | None | Possible (add `dcc.Location`) |

## What Stayed the Same

- All Plotly figure creation code
- NetworkX computations
- Data loading logic
- Core analysis functionality

## Deployment

### Plotly Cloud (Current)

Live at: https://e3613c3b-348f-45d9-8a15-989fb9a415f1.plotly.app/

```bash
pip install "dash[cloud]"
python -m plotly_cloud.cli app publish --project-path .
```

### Render / Railway / Fly.io

```bash
# Procfile
web: gunicorn app:server --bind 0.0.0.0:$PORT
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8050
CMD ["gunicorn", "app:server", "--bind", "0.0.0.0:8050"]
```

## Customization

### Change theme
Edit `external_stylesheets` in app initialization:
```python
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
# Options: BOOTSTRAP, CERULEAN, COSMO, CYBORG, DARKLY, FLATLY, 
#          JOURNAL, LITERA, LUMEN, LUX, MATERIA, MINTY, MORPH,
#          PULSE, QUARTZ, SANDSTONE, SIMPLEX, SKETCHY, SLATE,
#          SOLAR, SPACELAB, SUPERHERO, UNITED, VAPOR, YETI, ZEPHYR
```

### Add custom CSS
Create `assets/custom.css` - Dash auto-loads anything in `assets/`.

### Add URL routing
```python
from dash import dcc

# In layout
dcc.Location(id='url', refresh=False)

# Add callback to handle URL changes
@callback(Output('centrality-measure', 'value'), Input('url', 'pathname'))
def route_to_measure(pathname):
    if pathname == '/eigenvector':
        return 'eigenvector'
    # etc.
```

## Project Structure

```
interstate-trade/
├── app.py                  # Main Dash application
├── requirements.txt        # Dependencies
├── Procfile                # For deployment
├── plotly-cloud.toml       # Plotly Cloud config
├── data/
│   ├── centralities_51x51.csv
│   ├── filtration_results_51x51.csv
│   ├── network_graph.gpickle
│   ├── state_coords.csv
│   └── state_gdp_2017.csv
└── assets/                 # Optional: custom CSS, favicon
```

## Notes

- The app consolidates `main.py`, `data_loader.py`, and `visualizations.py` into a single file for simplicity
- For larger projects, you'd split these back out into modules
- `server = app.server` exposes the Flask server for WSGI deployment

## Known Issues

- **Deprecation warning**: `scattermapbox` is deprecated in favor of `scattermap` (Plotly's MapLibre migration). Not urgent but worth updating eventually.

## Future Enhancements

- **Methodology tab**: Add explanation of Jang & Yang three-level centrality hierarchy for academic audiences
