from itertools import combinations
import networkx as nx
from networkx.algorithms import isomorphism
from pprint import pprint

def parse_cluster_block(cluster_text: str):
    lines = cluster_text.strip().splitlines()
    cluster_name = lines[0].split()[1]

    lattice_state = []
    site_types = []
    neighboring = []
    angles = []

    in_lattice = False
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("lattice_state"):
            in_lattice = True
            continue
        elif line.startswith("site_types"):
            in_lattice = False
            site_types = line.replace("site_types", "").strip().split()
        elif line.startswith("neighboring"):
            neighboring = line.replace("neighboring", "").strip().split()
        elif line.startswith("angles"):
            angle_part = line.replace("angles", "").strip()
            angles = [a.split(":")[0] for a in angle_part.split()]
        elif in_lattice:
            tokens = line.split()
            if len(tokens) == 3:
                _, species, _ = tokens
                lattice_state.append(species)
            else:
                lattice_state.append("*")
        elif line.startswith("end_cluster"):
            break

    return {
        "name": cluster_name,
        "lattice_state": lattice_state,
        "site_types": site_types,
        "neighboring": neighboring,
        "angles": angles,
    }

def parse_neighboring(neighboring_lines):
    pairs = []
    for entry in neighboring_lines:
        for part in entry.strip().split():
            a, b = map(int, part.split('-'))
            pairs.append((a, b))
    return pairs

def build_cluster_graph(sites, species, site_types, neighboring_pairs):
    G = nx.Graph()
    for i, s in enumerate(sites):
        G.add_node(s, species=species[i], site_type=site_types[i])
    for a, b in neighboring_pairs:
        if a in sites and b in sites:
            G.add_edge(a, b)
    return G

def are_graphs_equivalent(G1, G2):
    nm = isomorphism.categorical_node_match(["species", "site_type"], [None, None])
    return nx.is_isomorphic(G1, G2, node_match=nm)

def generate_unique_clusters_with_geometry(cluster_dict):
    occupied = [(i + 1, sp, cluster_dict['site_types'][i])
                for i, sp in enumerate(cluster_dict['lattice_state']) if sp != '*']

    neighboring_pairs = parse_neighboring(cluster_dict.get("neighboring", []))

    seen_graphs = []
    all_clusters = []

    for k in range(1, len(occupied) + 1):
        for combo in combinations(occupied, k):
            sites = [x[0] for x in combo]
            species = [x[1] for x in combo]
            types = [x[2] for x in combo]

            G_new = build_cluster_graph(sites, species, types, neighboring_pairs)

            if not any(are_graphs_equivalent(G_new, G_old) for G_old in seen_graphs):
                seen_graphs.append(G_new)
                all_clusters.append({
                    'sites': sites,
                    'species': species,
                    'site_types': types,
                    'order': k
                })

    return all_clusters

# 示例 cluster
cluster_text = '''
cluster H2O*+O*
  sites 9
  neighboring 1-2 1-4 1-6 1-8 2-3 4-5 6-7 8-9   
  lattice_state
    1 H2O*_Rh   1
    2 *         1
    3 O*_Cu     1
    4 *         1
    5 O*_Cu     1
    6 *         1
    7 O*_Cu     1
    8 *         1
    9 O*_Cu     1
  site_types topRh hollowRh hollowCu hollowRh hollowCu hollowRh hollowCu hollowRh hollowCu  
  graph_multiplicity 1
  cluster_eng    0.035
  angles     1-2-3:180.00000000000000 1-4-5:180.00000000000000 1-6-7:180.00000000000000 1-8-9:180.00000000000000  
end_cluster
'''

# 使用方法
parsed = parse_cluster_block(cluster_text)
unique_clusters_geom = generate_unique_clusters_with_geometry(parsed)
pprint(unique_clusters_geom, sort_dicts=False)
