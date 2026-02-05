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

## Features

- **Commodity-specific filtering**: Filter both node centralities and edge flows by SCTG commodity code (42 individual codes + 8 grouped categories)
- **Boundary sensitivity toggle**: Compare domestic-only (51x51) vs with-international (52x52) networks
- **Rank change indicators**: Visual arrows showing how state centrality rankings shift when international trade is included
- **Three centrality measures**: Eigenvector, Out-Degree, Betweenness
- **Dark/light mode toggle**
- **Explore vs Analyze modes**
- **Interactive map** with state selection and detail drawer
- **Rankings table** with GDP divergence coloring
- **Filtration slider** for betweenness stability analysis

## Data

- **Source**: U.S. Census Bureau [CFS 2017 Public Use File](https://www2.census.gov/programs-surveys/cfs/datasets/2017/)
- **51x51 Network**: 51 nodes (50 states + DC), ~2,500 directed edges
- **52x52 Network**: Adds international trade flows (Rest of World node)
- **Weights**: Survey-adjusted trade values with weight inversion for betweenness
- **Commodity edges**: 80,867 directed edges across 50 SCTG commodity codes, extracted from CFS via thesis pipeline

## Project Structure

```
interstate-trade/
├── app.py                    # Entry point
├── data_loader.py            # Data loading, rank change computation
├── components/
│   ├── __init__.py
│   ├── layout.py             # App layout with boundary toggle
│   └── map.py                # Network map visualization
├── callbacks/
│   ├── __init__.py
│   └── interactions.py       # All Dash callbacks
├── styles/
│   ├── __init__.py
│   └── css.py                # Custom CSS
├── data/
│   ├── centralities_51x51.csv
│   ├── centralities_52x52.csv
│   ├── commodity_centralities.csv  # Per-commodity node centralities
│   ├── commodity_edges.csv         # Per-commodity edge weights (50 SCTG codes)
│   ├── filtration_results_51x51.csv
│   ├── network_graph.gpickle
│   ├── state_coords.csv
│   └── state_gdp_2017.csv
├── requirements.txt
├── Procfile                  # For deployment
└── plotly-cloud.toml         # Plotly Cloud config
```

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
Edit `external_stylesheets` in `app.py`:
```python
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
```

### Add custom CSS
Edit `styles/css.py` or create `assets/custom.css` (Dash auto-loads assets/).

## Architecture Notes

| Module | Purpose |
|--------|---------|
| `app.py` | Slim entry point, initializes Dash app |
| `data_loader.py` | Loads networks, rank changes, commodity centralities and edges |
| `components/layout.py` | Full app layout with stores, controls, panels |
| `components/map.py` | Scattermapbox visualization with rank indicators |
| `callbacks/interactions.py` | All interactivity (toggles, clicks, commodity-aware edge rendering) |
| `styles/css.py` | Custom CSS for theming |

## Known Issues

- **Deprecation warning**: `scattermapbox` deprecated in favor of `scattermap` (Plotly's MapLibre migration)

## Related

This visualization connects to thesis research on boundary sensitivity in trade network analysis. The 52x52 data comes from the canonical thesis pipeline run (November 2025).
