# Interstate Trade Visualization

## Quick Reference

**Run locally:**
```bash
source venv/bin/activate
python app.py
# Opens at http://localhost:8050
```

**Deploy to Plotly Cloud:**
```bash
source venv/bin/activate
python -m plotly_cloud.cli app publish --project-path .
```

**Live app:** https://e3613c3b-348f-45d9-8a15-989fb9a415f1.plotly.app/

## Project Context

- Dash app for SSIE-641 (Advanced Network Science) final project
- Visualizes U.S. interstate trade network centrality measures
- Framework: Jang & Yang (2023) three-level centrality analysis
- Supports boundary sensitivity analysis (51x51 domestic vs 52x52 with international)

## Project Structure

```
interstate-trade/
├── app.py                    # Entry point (slim, imports modules)
├── data_loader.py            # Data loading, pre-computed rank changes
├── components/
│   ├── __init__.py
│   ├── layout.py             # App layout with boundary toggle
│   └── map.py                # Network map with rank indicators
├── callbacks/
│   ├── __init__.py
│   └── interactions.py       # All Dash callbacks
├── styles/
│   ├── __init__.py
│   └── css.py                # Custom CSS
├── data/
│   ├── centralities_51x51.csv
│   ├── centralities_52x52.csv   # From thesis canonical run
│   ├── filtration_results_51x51.csv
│   ├── network_graph.gpickle
│   ├── state_coords.csv
│   └── state_gdp_2017.csv
└── requirements.txt
```

## Key Features

- **Boundary sensitivity toggle**: Switch between domestic (51x51) and international (52x52) networks
- **Rank change indicators**: Visual arrows showing how state rankings shift with international trade
- **Three centrality measures**: Eigenvector, Out-Degree, Betweenness
- **Dark/light mode**, Explore/Analyze modes

## Python Environment

Always use project venv:
```bash
source venv/bin/activate
# or
/Users/home/Desktop/interstate-trade/venv/bin/python
```

Never install packages globally.

## Data Source

- 51x51: CFS 2017 domestic interstate trade
- 52x52: Thesis canonical run (Nov 29, 2025) with international trade (RoW node)
- Weight inversion fix applied for betweenness centrality
