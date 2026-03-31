"""
Spectroscopic network graph for OCS isotopologues - specify input file and number of largest components to show
"""

import re
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import warnings
from collections import Counter
warnings.filterwarnings('ignore')

#config
CHECK_FILE = "632_check_transitions.txt"  
N_COMPONENTS = 11                         

#style
SPRING_K = 0.3
SPRING_ITER = 100
SPRING_SEED = 42

EDGE_COLOUR = '#3A7BBF'
EDGE_WIDTH = 1.2
EDGE_ALPHA = 0.6

NODE_COLOUR = '#2A6CB0'
NODE_SIZE = 18
NODE_ALPHA = 0.8

FIG_SIZE = (10, 10)
DPI = 300
COMPONENT_SPACING = 3.5  #spacing between separated components


#parser
def get_component_ids(filename, n_largest):
    """Find the n_largest component IDs by node count."""
    with open(filename) as f:
        lines = f.readlines()
    comp_counts = Counter()
    for line in lines:
        m = re.match(
            r'\d+\)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\w+'
            r'\s+in component\s+(\d+)', line)
        if m:
            comp_counts[int(m.group(1))] += 1
    return {c for c, _ in comp_counts.most_common(n_largest)}


def parse_check_file(filename, components):
    """Parse MARVEL check file, returning nodes and edges for specified components."""
    with open(filename) as f:
        lines = f.readlines()

    nodes = set()
    edges = set()
    current_level = None
    current_comp = None

    for line in lines:
        line = line.rstrip('\n')
        m = re.match(
            r'\d+\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)'
            r'\s+in component\s+(\d+)', line)
        if m:
            current_level = (int(m.group(1)), int(m.group(2)),
                             int(m.group(3)), int(m.group(4)),
                             int(m.group(5)), m.group(6))
            current_comp = int(m.group(7))
            if current_comp in components:
                nodes.add(current_level)
            continue

        stripped = line.strip()
        if stripped and current_level is not None and current_comp in components:
            parts = stripped.split()
            if len(parts) >= 11 and '.' in parts[0]:
                try:
                    partner = (int(parts[4]), int(parts[5]),
                               int(parts[6]), int(parts[7]),
                               int(parts[8]), parts[9])
                    edge = tuple(sorted([current_level, partner]))
                    edges.add(edge)
                except (ValueError, IndexError):
                    pass

    return nodes, edges


#layout
def layout_components(G, n_components):
    """Layout each component separately with clear spatial separation."""
    components = sorted(nx.connected_components(G), key=len, reverse=True)
    pos = {}

    #single component, standard spring layout
    if len(components) == 1:
        return nx.spring_layout(G, k=SPRING_K, iterations=SPRING_ITER,
                                seed=SPRING_SEED)

    #multiple components, grid layout with separation
    ncols = min(4, len(components))
    for idx, comp in enumerate(components):
        subgraph = G.subgraph(comp)
        sub_pos = nx.spring_layout(subgraph, k=0.8, iterations=150,
                                   seed=SPRING_SEED + idx)
        scale = np.sqrt(len(comp)) / 4.0
        row = idx // ncols
        col = idx % ncols
        offset_x = col * COMPONENT_SPACING
        offset_y = -row * COMPONENT_SPACING

        for node, (x, y) in sub_pos.items():
            pos[node] = (x * scale + offset_x, y * scale + offset_y)

    return pos


#plot
if __name__ == "__main__":
    print(f"File: {CHECK_FILE}")
    print(f"Showing {N_COMPONENTS} largest component(s)\n")

    comp_ids = get_component_ids(CHECK_FILE, N_COMPONENTS)
    print(f"Component IDs: {sorted(comp_ids)}")

    nodes, edges = parse_check_file(CHECK_FILE, comp_ids)
    print(f"Nodes: {len(nodes)}, Edges: {len(edges)}")

    G = nx.Graph()
    G.add_nodes_from(nodes)
    for e in edges:
        if e[0] in nodes and e[1] in nodes:
            G.add_edge(e[0], e[1])

    n_actual = nx.number_connected_components(G)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {n_actual} components")

    print("Computing layout...")
    pos = layout_components(G, N_COMPONENTS)

    print("Plotting...")
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    fig.patch.set_alpha(0.0)
    ax.set_facecolor('none')

    nx.draw_networkx_edges(G, pos, edge_color=EDGE_COLOUR,
                           width=EDGE_WIDTH, alpha=EDGE_ALPHA, ax=ax)

    nx.draw_networkx_nodes(G, pos, node_color=NODE_COLOUR,
                           node_size=NODE_SIZE, alpha=NODE_ALPHA,
                           ax=ax, linewidths=0)

    ax.set_axis_off()

    legend_elements = [
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor=NODE_COLOUR, markersize=14,
               label='Energy levels'),
        Line2D([0], [0], color=EDGE_COLOUR, linewidth=3,
               label='Transitions'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=28,
              framealpha=0.0, frameon=False, edgecolor='none')

    fig.tight_layout()

    outname = CHECK_FILE.replace('_check_transitions.txt', '')
    fig.savefig(f'spider_{outname}.png', dpi=DPI, bbox_inches='tight',
                transparent=True)
    fig.savefig(f'spider_{outname}.pdf', bbox_inches='tight',
                transparent=True)
    print(f"\nSaved: spider_{outname}.png / .pdf")