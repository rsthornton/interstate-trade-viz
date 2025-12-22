"""Data loading functions and pre-loaded data for Interstate Trade visualization."""

import pandas as pd
import networkx as nx
import pickle
from pathlib import Path


def load_centralities(data_dir="data", network_type="51x51"):
    """Load centrality scores from CSV.

    Args:
        data_dir: Directory containing data files
        network_type: "51x51" for domestic only, "52x52" for with international
    """
    filename = f"centralities_{network_type}.csv"
    file_path = Path(data_dir) / filename
    df = pd.read_csv(file_path)
    df = df.rename(columns={'label': 'state'})
    return df


def load_network(data_dir="data"):
    """Load the trade network graph."""
    file_path = Path(data_dir) / "network_graph.gpickle"
    with open(file_path, 'rb') as f:
        G = pickle.load(f)
    return G


def load_state_coords(data_dir="data"):
    """Load state coordinates for map visualization."""
    file_path = Path(data_dir) / "state_coords.csv"
    return pd.read_csv(file_path)


def load_gdp(data_dir="data"):
    """Load state GDP data."""
    file_path = Path(data_dir) / "state_gdp_2017.csv"
    df = pd.read_csv(file_path)
    df['gdp_billions'] = df['gdp_2017_q4_millions'] / 1000
    df['gdp_rank'] = df['gdp_billions'].rank(ascending=False, method='min').astype(int)
    return df


def load_filtration_data(data_dir="data"):
    """Load pre-computed filtration results."""
    file_path = Path(data_dir) / "filtration_results_51x51.csv"
    df = pd.read_csv(file_path)
    df = df.rename(columns={'label': 'state'})

    filtration_data = {}
    for threshold_label in df['threshold_label'].unique():
        threshold_df = df[df['threshold_label'] == threshold_label].copy()
        threshold_df['rank_betweenness'] = threshold_df['betweenness'].rank(ascending=False, method='min')
        threshold_df['rank_eigenvector'] = threshold_df['eigenvector'].rank(ascending=False, method='min')
        threshold_df['rank_out_degree'] = threshold_df['out_degree'].rank(ascending=False, method='min')
        filtration_data[threshold_label] = threshold_df.reset_index(drop=True)

    return filtration_data


def load_commodity_centralities(data_dir="data"):
    """Load commodity-level centralities from CSV.

    Returns:
        DataFrame with columns: state_id, label (state), betweenness, eigenvector,
        out_degree, commodity_code, commodity_name
    """
    file_path = Path(data_dir) / "commodity_centralities.csv"
    df = pd.read_csv(file_path)
    df = df.rename(columns={'label': 'state'})
    return df


# Commodity groupings for UI (SCTG codes grouped by category)
COMMODITY_GROUPS = {
    'Agriculture & Food': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '01-05', '06-09'],
    'Mining & Extraction': ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '10-14', '15-19'],
    'Chemicals & Plastics': ['20', '21', '22', '23', '24', '20-24'],
    'Wood & Paper': ['25', '26', '27', '28', '29', '25-30'],
    'Metals & Minerals': ['30', '31', '32', '33', '31-34'],
    'Machinery & Equipment': ['34', '35', '36', '37', '38', '35-38'],
    'Consumer & Other': ['39', '40', '41', '43', '39-43', '00'],
}


def get_commodity_options():
    """Get commodity options for dropdown, grouped by category.

    Returns:
        List of dicts suitable for dcc.Dropdown options with grouping.
    """
    options = [{'label': '📦 All Commodities', 'value': 'all'}]

    for group_name, codes in COMMODITY_GROUPS.items():
        # Add group header (disabled)
        options.append({'label': f'── {group_name} ──', 'value': f'header_{group_name}', 'disabled': True})
        for code in codes:
            if code in SCTG_NAMES:
                options.append({
                    'label': f'  {code}: {SCTG_NAMES[code]}',
                    'value': code
                })
    return options


# SCTG code names (from thesis toolkit)
SCTG_NAMES = {
    '00': 'Unknown/Unclassified',
    '01': 'Live Animals and Fish',
    '02': 'Cereal Grains',
    '03': 'Other Agricultural Products',
    '04': 'Animal Feed',
    '05': 'Meat/Seafood',
    '06': 'Milled Grain Products',
    '07': 'Other Foodstuffs',
    '08': 'Alcoholic Beverages',
    '09': 'Tobacco Products',
    '10': 'Building Stone',
    '11': 'Natural Sands',
    '12': 'Gravel and Crushed Stone',
    '13': 'Nonmetallic Minerals',
    '14': 'Metallic Ores',
    '15': 'Coal',
    '16': 'Crude Petroleum',
    '17': 'Gasoline',
    '18': 'Fuel Oils',
    '19': 'Coal and Petroleum Products',
    '20': 'Basic Chemicals',
    '21': 'Pharmaceutical Products',
    '22': 'Fertilizers',
    '23': 'Chemical Products',
    '24': 'Plastics/Rubber',
    '25': 'Logs and Wood',
    '26': 'Wood Products',
    '27': 'Newsprint/Paper',
    '28': 'Paper Articles',
    '29': 'Printed Products',
    '30': 'Textiles/Leather',
    '31': 'Nonmetallic Mineral Products',
    '32': 'Base Metals',
    '33': 'Articles of Base Metal',
    '34': 'Machinery',
    '35': 'Electronic Equipment',
    '36': 'Motorized Vehicles',
    '37': 'Transportation Equipment',
    '38': 'Precision Instruments',
    '39': 'Furniture',
    '40': 'Misc. Manufactured Products',
    '41': 'Waste/Scrap',
    '43': 'Mixed Freight',
    # Grouped codes
    '01-05': 'Agriculture (Grouped)',
    '06-09': 'Food Products (Grouped)',
    '10-14': 'Mining (Grouped)',
    '15-19': 'Energy (Grouped)',
    '20-24': 'Chemicals (Grouped)',
    '25-30': 'Wood/Paper/Textiles (Grouped)',
    '31-34': 'Metals/Machinery (Grouped)',
    '35-38': 'Electronics/Vehicles (Grouped)',
    '39-43': 'Consumer/Other (Grouped)',
}


def get_top_edges(network, coords, centralities, top_n=50):
    """Get the top N edges by weight for visualization."""
    id_to_label = dict(zip(centralities['state_id'], centralities['state']))
    coords_renamed = coords.rename(columns={'state_abbr': 'state'})
    coord_lookup = {row['state']: {'lat': row['lat'], 'lon': row['lon']}
                    for _, row in coords_renamed.iterrows()}

    edges_with_weight = [
        (source, target, data['weight'])
        for source, target, data in network.edges(data=True)
    ]
    edges_sorted = sorted(edges_with_weight, key=lambda x: x[2], reverse=True)

    top_edges = []
    for source_id, target_id, weight in edges_sorted[:top_n]:
        source_label = id_to_label.get(source_id)
        target_label = id_to_label.get(target_id)

        if not source_label or not target_label:
            continue
        if source_label not in coord_lookup or target_label not in coord_lookup:
            continue

        top_edges.append({
            'source': source_label,
            'target': target_label,
            'weight': weight,
            'source_lat': coord_lookup[source_label]['lat'],
            'source_lon': coord_lookup[source_label]['lon'],
            'target_lat': coord_lookup[target_label]['lat'],
            'target_lon': coord_lookup[target_label]['lon']
        })

    return top_edges


# =============================================================================
# PRE-LOADED DATA (module-level singleton pattern)
# =============================================================================

print("Loading data...")

# Load raw data
coords = load_state_coords()
network = load_network()
filtration_data = load_filtration_data()
gdp = load_gdp()
commodity_centralities_raw = load_commodity_centralities()

# Load both network configurations
centralities_51x51 = load_centralities(network_type="51x51")
centralities_52x52 = load_centralities(network_type="52x52")


def _prepare_centralities(df):
    """Merge GDP and state_name into centralities dataframe."""
    df = df.merge(
        gdp[['state_abbrev', 'gdp_billions', 'gdp_rank']],
        left_on='state', right_on='state_abbrev', how='left'
    ).drop(columns=['state_abbrev'])

    df = df.merge(
        coords[['state_abbr', 'state_name']],
        left_on='state', right_on='state_abbr', how='left'
    ).drop(columns=['state_abbr'])

    return df


# Prepare both datasets
centralities_51x51 = _prepare_centralities(centralities_51x51)
centralities_52x52 = _prepare_centralities(centralities_52x52)

# Default to 51x51 for backwards compatibility
centralities_base = centralities_51x51

# Compute rank changes between 51x51 and 52x52 (for boundary sensitivity visualization)
# Only for the 51 states that exist in both (exclude RoW from 52x52)
states_51 = set(centralities_51x51['state'])
centralities_52x52_states_only = centralities_52x52[centralities_52x52['state'].isin(states_51)].copy()

rank_changes = centralities_51x51[['state']].copy()
for measure in ['betweenness', 'eigenvector', 'out_degree']:
    rank_51 = centralities_51x51.set_index('state')[f'rank_{measure}']
    rank_52 = centralities_52x52_states_only.set_index('state')[f'rank_{measure}']
    # Positive = improved rank (lower number = better)
    rank_changes[f'{measure}_change'] = (rank_51 - rank_52).reindex(rank_changes['state']).values

# Compute network stats
density = nx.density(network)
num_edges = network.number_of_edges()
num_nodes = len(centralities_51x51)
clustering_coef = nx.average_clustering(network, weight='weight')
reciprocity = nx.reciprocity(network)

# Prepare commodity centralities (add ranks per commodity)
def _prepare_commodity_centralities(df):
    """Add ranks within each commodity code."""
    result_dfs = []
    for code in df['commodity_code'].unique():
        code_df = df[df['commodity_code'] == code].copy()
        code_df['rank_betweenness'] = code_df['betweenness'].rank(ascending=False, method='min')
        code_df['rank_eigenvector'] = code_df['eigenvector'].rank(ascending=False, method='min')
        code_df['rank_out_degree'] = code_df['out_degree'].rank(ascending=False, method='min')

        # Merge GDP and state names
        code_df = code_df.merge(
            gdp[['state_abbrev', 'gdp_billions', 'gdp_rank']],
            left_on='state', right_on='state_abbrev', how='left'
        ).drop(columns=['state_abbrev'], errors='ignore')

        code_df = code_df.merge(
            coords[['state_abbr', 'state_name']],
            left_on='state', right_on='state_abbr', how='left'
        ).drop(columns=['state_abbr'], errors='ignore')

        result_dfs.append(code_df)

    return pd.concat(result_dfs, ignore_index=True)


commodity_centralities = _prepare_commodity_centralities(commodity_centralities_raw)

# Get list of available commodity codes
available_commodities = sorted(commodity_centralities['commodity_code'].unique().tolist())
commodity_options = get_commodity_options()


def get_centralities_for_commodity(commodity_code):
    """Get centralities for a specific commodity code.

    Args:
        commodity_code: SCTG code (e.g., '34' for Machinery) or 'all' for aggregate

    Returns:
        DataFrame with centralities for that commodity (same format as centralities_51x51)
    """
    if commodity_code == 'all':
        return centralities_51x51

    code_df = commodity_centralities[commodity_centralities['commodity_code'] == commodity_code].copy()
    return code_df.reset_index(drop=True)


print("Data loaded.")
