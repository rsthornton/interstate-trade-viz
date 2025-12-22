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

## Key Files

- `app.py` - Single-file Dash application (all logic consolidated)
- `data/` - Precomputed centralities and network data
- `plotly-cloud.toml` - Plotly Cloud deployment config

## Python Environment

Always use project venv:
```bash
source venv/bin/activate
# or
/Users/home/Desktop/interstate-trade/venv/bin/python
```

Never install packages globally.
