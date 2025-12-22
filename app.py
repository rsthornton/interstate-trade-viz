"""
Interstate Trade Network Visualization

Design principles:
1. The map IS the interface - everything else serves it
2. Progressive disclosure - show complexity on demand
3. State selection is the primary interaction
4. Controls feel like part of the map, not a separate panel
5. Information appears contextually

Author: Shingai Thornton
"""

from dash import Dash
import dash_bootstrap_components as dbc

from styles import CUSTOM_CSS
from components import create_layout
from callbacks import register_callbacks


# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap'
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    suppress_callback_exceptions=True  # rankings-table is dynamically created
)

# Inject custom CSS via index_string
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Interstate Trade Network</title>
        {%favicon%}
        {%css%}
        <style>''' + CUSTOM_CSS + '''</style>
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

# Set layout
app.layout = create_layout()

# Register callbacks
register_callbacks(app)


# =============================================================================
# RUN
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=8050)
