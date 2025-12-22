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

print("Data loaded.")
