"""
Spectroscopic network graph for OCS MARVEL analysis.
Every validated main-network energy level is a node; every validated
transition is an edge.  All existing nodes/edges in blue; new levels
and transitions highlighted in orange.

Uses spring layout for topology

Requires:
    - old_check_transitions.txt   (old MARVEL check output)
    - new_check_transitions.txt   (new MARVEL check output)
"""

import re
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

#config
OLD_CHECK = "old_check_transitions.txt" #marvel 3 output convention
NEW_CHECK = "new_check_transitions.txt" #marvel 3 output convention

#tuneable params
SPRING_K = 0.15          # smaller = tighter clusters
SPRING_ITER = 80         # more = slower but cleaner
SPRING_SEED = 42         # random seed

#style
OLD_EDGE_COLOUR ='#7FB3D8'
OLD_EDGE_WIDTH = 0.3
OLD_EDGE_ALPHA = 0.4

NEW_EDGE_COLOUR = '#E67E22'
NEW_EDGE_WIDTH = 0.6
NEW_EDGE_ALPHA = 0.55

OLD_NODE_COLOUR = '#4A90D9'
OLD_NODE_SIZE = 3
OLD_NODE_ALPHA = 0.6

NEW_NODE_COLOUR = '#E67E22'
NEW_NODE_SIZE = 10
NEW_NODE_ALPHA = 0.75

FIG_SIZE = (14, 14)
DPI = 300


#parser
def parse_check_file(filename):
    """
    Parse MARVEL check transitions file.
    Returns main-network (component 0) nodes and edges.
    Nodes are (v1, v2, v3, ell, J, parity) tuples.
    Edges are frozensets of two nodes, stored as sorted tuples.
    
    """
    with open(filename) as f:
        lines = f.readlines()

    nodes = set()
    edges = set()
    current_level = None
    current_comp = None

    for line in lines:
        line = line.rstrip('\n')

        # Level header: "N) v1 v2 v3 ell J parity  in component C = energy"
        m = re.match(
            r'\d+\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)'
            r'\s+in component\s+(\d+)', line)
        if m:
            current_level = (int(m.group(1)), int(m.group(2)),
                             int(m.group(3)), int(m.group(4)),
                             int(m.group(5)), m.group(6))
            current_comp = int(m.group(7))
            if current_comp == 0:
                nodes.add(current_level)
            continue

        # Transition line (only for component 0):
        stripped = line.strip()
        if stripped and current_level is not None and current_comp == 0:
            parts = stripped.split()
            if len(parts) == 11 and '.' in parts[0]:
                try:
                    partner = (int(parts[4]), int(parts[5]),
                               int(parts[6]), int(parts[7]),
                               int(parts[8]), parts[9])
                    edge = tuple(sorted([current_level, partner]))
                    edges.add(edge)
                except (ValueError, IndexError):
                    pass

    return nodes, edges


#graph construction
if __name__ == "__main__":
    print("Parsing old check transitions...")
    old_nodes, old_edges = parse_check_file(OLD_CHECK)
    print(f"  Nodes: {len(old_nodes)}, Edges: {len(old_edges)}")

    print("Parsing new check transitions...")
    new_nodes, new_edges = parse_check_file(NEW_CHECK)
    print(f"  Nodes: {len(new_nodes)}, Edges: {len(new_edges)}")

    #identify changes
    added_nodes = new_nodes - old_nodes
    removed_nodes = old_nodes - new_nodes
    added_edges = new_edges - old_edges
    removed_edges = old_edges - new_edges

    print(f"\nAdded nodes: {len(added_nodes)}")
    print(f"Removed nodes: {len(removed_nodes)}")
    print(f"Net change: {len(added_nodes) - len(removed_nodes)}")
    print(f"Added edges: {len(added_edges)}")
    print(f"Removed edges: {len(removed_edges)}")

    new_node_edges = {e for e in added_edges
                      if e[0] in added_nodes or e[1] in added_nodes}
    new_bridge_edges = added_edges - new_node_edges

    print(f"  Edges to new nodes: {len(new_node_edges)}")
    print(f"  New edges between existing nodes: {len(new_bridge_edges)}")

    #build graph from the new network
    print("\nBuilding graph...")
    G = nx.Graph()
    G.add_nodes_from(new_nodes)
    for e in new_edges:
        G.add_edge(e[0], e[1])
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Connected: {nx.is_connected(G)}")

    #spring layout
    print("Computing layout (this may take a moment)...")
    pos = nx.spring_layout(G, k=SPRING_K, iterations=SPRING_ITER,
                           seed=SPRING_SEED)

    #classify nodes and edges
    old_nodes_list = [n for n in G.nodes() if n not in added_nodes]
    new_nodes_list = [n for n in G.nodes() if n in added_nodes]

    old_edges_list = []
    new_edges_list = []
    for e in G.edges():
        if e[0] in added_nodes or e[1] in added_nodes:
            new_edges_list.append(e)
        else:
            old_edges_list.append(e)

    #plot
    print("Plotting...")
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    ax.set_facecolor('white')

    #old edges 
    nx.draw_networkx_edges(G, pos, edgelist=old_edges_list,
                           edge_color=OLD_EDGE_COLOUR,
                           width=OLD_EDGE_WIDTH, alpha=OLD_EDGE_ALPHA, ax=ax)

    #new edges 
    if new_edges_list:
        nx.draw_networkx_edges(G, pos, edgelist=new_edges_list,
                               edge_color=NEW_EDGE_COLOUR,
                               width=NEW_EDGE_WIDTH, alpha=NEW_EDGE_ALPHA,
                               ax=ax)

    #old nodes
    nx.draw_networkx_nodes(G, pos, nodelist=old_nodes_list,
                           node_color=OLD_NODE_COLOUR,
                           node_size=OLD_NODE_SIZE, alpha=OLD_NODE_ALPHA,
                           ax=ax, linewidths=0)

    #new nodes (larger)
    if new_nodes_list:
        nx.draw_networkx_nodes(G, pos, nodelist=new_nodes_list,
                               node_color=NEW_NODE_COLOUR,
                               node_size=NEW_NODE_SIZE, alpha=NEW_NODE_ALPHA,
                               ax=ax, linewidths=0.3, edgecolors='#C0650F')

    ax.set_axis_off()

    #legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor=OLD_NODE_COLOUR, markersize=6,
               label='Previous energy levels'),
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor=NEW_NODE_COLOUR, markersize=8,
               label='New energy levels'),
        Line2D([0], [0], color=OLD_EDGE_COLOUR, linewidth=1.5,
               label='Previous transitions'),
        Line2D([0], [0], color=NEW_EDGE_COLOUR, linewidth=1.5,
               label='New transitions'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=11,
              framealpha=0.9, frameon=True)

    fig.tight_layout()
    fig.savefig('spider_definitive.png', dpi=DPI, bbox_inches='tight',
                facecolor='white')
    fig.savefig('spider_definitive.pdf', bbox_inches='tight',
                facecolor='white')
    plt.show()
    print("\nSaved: spider_definitive.png / .pdf")