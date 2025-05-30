import sys
import json
import math
from pathlib import Path

import networkx as nx
import matplotlib.pyplot as plt

json_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("transformations.json")
if not json_file.exists():
    sys.exit(f"Can not find the Fucking file ：{json_file}")

with json_file.open("r", encoding="utf-8") as fh:
    data = json.load(fh)

forward = data.get("forward", {})
reverse = data.get("reverse", {})


G = nx.DiGraph(name="Reaction Network (self-loops removed)")

def add_reactions(mapping: dict, direction: str):
    for rxn_name, mapping_dict in mapping.items():
        for reactant, products in mapping_dict.items():
            r = reactant.strip()
            for product in products:
                p = product.strip()
                if r == p:                 #  diffusion bu xie jin qu
                    continue
                G.add_edge(
                    r, p,
                    reaction=rxn_name,
                    direction=direction
                )

add_reactions(forward, "forward")
add_reactions(reverse, "reverse")

print(f"✅ Loaded {G.number_of_nodes()} nodes, {G.number_of_edges()} edges (no self-loops)")


try:
    pos = nx.nx_agraph.graphviz_layout(G, prog="sfdp")
except Exception as e:
    print("⚠️  Graphviz can not find, just use the  spring_layout：", e)
    pos = nx.spring_layout(
        G,
        seed=42,
        k=1.2 / math.sqrt(max(G.number_of_nodes(), 1)),
        iterations=300
    )


NODE_SIZE   = 600     # 节点尺寸
NODE_EDGE   = 1.5     # 节点描边
EDGE_WIDTH  = 1.5     # 边线宽
ARROW_SIZE  = 10      # 箭头大小
FONT_SIZE   = 8       # 标签字号

FIG_W = max(14, G.number_of_nodes() * 0.14)  
FIG_H = 0.75 * FIG_W

plt.figure(figsize=(FIG_W, FIG_H), dpi=300)


nx.draw_networkx_nodes(
    G, pos,
    node_size=NODE_SIZE,
    node_color="#A6D854",
    edgecolors="#555555",
    linewidths=NODE_EDGE
)


edge_colors = [
    "#E24A33AA" if d["direction"] == "forward" else "#348ABD88"
    for _, _, d in G.edges(data=True)
]

nx.draw_networkx_edges(
    G, pos,
    arrows=True,
    edge_color=edge_colors,
    width=EDGE_WIDTH,
    arrowsize=ARROW_SIZE,
    arrowstyle="-|>",
    connectionstyle="arc3,rad=0.08"       
)

# 如节点太密，可注释掉以下块
nx.draw_networkx_labels(
    G, pos,
    font_size=FONT_SIZE,
    font_color="#000000"
)

plt.title("Full Reaction Network ", fontsize=12, pad=12)
plt.axis("off")
plt.tight_layout()


png_path     = json_file.with_suffix("").name + "_full_network.png"
graphml_path = json_file.with_suffix("").name + "_network.graphml"

plt.savefig(png_path, bbox_inches="tight")
nx.write_graphml(G, graphml_path)

print("📄 PNG saved   →", Path(png_path).resolve())
print("📄 GraphML saved →", Path(graphml_path).resolve())


plt.show()
