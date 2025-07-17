import os
import re
import json
from pymatgen.core import Composition

def extract_core_formula(species_name):
    m = re.match(r'^([A-Z][a-z]?\d*)+', species_name)
    return m.group(0) if m else ""

def compute_overlap(comp1, comp2):
    return sum(min(comp1[e], comp2[e]) for e in comp1.keys() & comp2.keys())

def parse_procstat_output(file_path, ini_config=None, fin_config=None):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    reactions = re.split(r'\s+', lines[0].strip())
    reactions = [r for r in reactions if r.lower() != 'overall']
    counts = [int(c) for c in re.split(r'\s+', lines[-1].strip())[1:]]
    stats = []
    for i in range(0, len(reactions), 2):
        fwd, rev = reactions[i], reactions[i+1]
        fwd_c, rev_c = counts[i], counts[i+1]
        net = fwd_c - rev_c
        idx = i // 2  # index 从 0 开始计数
        if ini_config is not None and idx < ini_config:
            continue
        if fin_config is not None and idx > fin_config:
            continue
        stats.append({
            "reaction_name": fwd[:-4],
            "fwd_count": fwd_c,
            "rev_count": rev_c,
            "net_count": net
        })
    return stats

def parse_general_output(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if "Reaction network:" in line:
                break
        for line in f:
            m = re.match(
                r'^\s*(\d+)\.\s+(\S+_(fwd|rev)):.*?Reaction:\s+(.+?)\s*->\s*(.+)$',
                line
            )
            if not m:
                continue
            idx  = int(m.group(1))
            tag  = m.group(2)          # e.g. CH4->CH3*_Cu+H*_Cu_fwd
            name = tag.rsplit('_', 1)[0]  # strip _fwd/_rev
            dire = m.group(3)          # "fwd" or "rev"
            react = m.group(4).split('  +  ')
            prod  = m.group(5).split('  +  ')
            data.append({
                "index": idx,
                "tag"  : tag,
                "reaction_name": name,
                "direction": dire,
                "reactants": react,
                "products": prod
            })
    return data

def merge_reaction_data(procstat, general):
    # 把同名反应分到一个列表
    buckets = {}
    for g in general:
        buckets.setdefault(g["reaction_name"], []).append(g)

    merged = []
    for item in procstat:
        name = item["reaction_name"]
        # 默认用第一条；如果有 _fwd 就选它
        chosen = buckets.get(name, [{}])[0]
        for g in buckets.get(name, []):
            if g.get("direction") == "fwd":
                chosen = g
                break
        merged.append({
            **item,
            "reactants": chosen.get("reactants", []),
            "products":  chosen.get("products",  [])
        })
    return merged

def element_analysis_with_pymatgen(merged_data):
    comp_map = {}
    for rxn in merged_data:
        for side in ("reactants", "products"):
            for sp in rxn.get(side, []):
                if sp.startswith('*') or sp in comp_map:
                    continue
                core = extract_core_formula(sp)
                comp_map[sp] = Composition(core).as_dict() if core else {}
    return comp_map

def identify_transformations(merged_data, species_composition,
                             mapping_path='transformations.json'):
    """
    始终重建并返回正向+逆向两套映射：
      {
        "forward": { rxn: {reactant: [products...]}, ... },
        "reverse": { rxn: {product:  [reactants...]}, ... }
      }
    并把它写入 mapping_path，覆盖任何旧文件。
    """
    forward = {}
    reverse = {}
    for rxn in merged_data:
        name = rxn["reaction_name"]
        rlist = [s for s in rxn["reactants"] if not s.startswith('*')]
        plist = [s for s in rxn["products"]   if not s.startswith('*')]
        if not rlist or not plist:
            continue

        # ── 构建正向映射 ──
        if len(rlist) == 1:
            forward[name] = {rlist[0]: plist[:]}
        else:
            rm = {}
            for r in rlist:
                comp_r = species_composition.get(r, {})
                best_ps = []
                best_score = 0
                for p in plist:
                    ov = compute_overlap(comp_r, species_composition.get(p, {}))
                    if ov > best_score:
                        best_score, best_ps = ov, [p]
                    elif ov == best_score and ov > 0:
                        best_ps.append(p)
                rm[r] = best_ps
            forward[name] = rm

        # ── 构建逆向映射 ──
        revm = {}
        for r, ps in forward[name].items():
            for p in ps:
                revm.setdefault(p, []).append(r)
        reverse[name] = revm

    # 坚决覆盖旧文件
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump({"forward": forward, "reverse": reverse},
                  f, indent=2, ensure_ascii=False)

    return {"forward": forward, "reverse": reverse}

def analyze_species(merged_data, species_key, ignore_diffusion=False):
    """
    返回两组事件：
      producers: 净生成 species_key 的事件（正向产物且不在反应物，或反向反应物且不在产物）
      consumers: 净消耗 species_key 的事件（正向反应物且不在产物，或反向产物且不在反应物）
    count 始终为正值，表示该事件数。
    """
    producers, consumers = [], []
    for rxn in merged_data:
        if ignore_diffusion:
            r = sorted([s for s in rxn["reactants"] if not s.startswith('*')])
            p = sorted([s for s in rxn["products"] if not s.startswith('*')])
            if r == p:
                continue

        net = rxn["net_count"]
        name = rxn["reaction_name"]

       # print(f"[Debug] Reaction: {name}, Net: {net}, Reactants: {rxn['reactants']}, Products: {rxn['products']}")

        if net > 0:
            # 正向事件 net 次
            if species_key in rxn["products"] and species_key not in rxn["reactants"]:
                producers.append({"reaction_name": name, "count": net})
                print(f"[Debug] Added to producers: {name}, count: {net}")
            if species_key in rxn["reactants"] and species_key not in rxn["products"]:
                consumers.append({"reaction_name": name, "count": net})
                print(f"[Debug] Added to consumers: {name}, count: {net}")

        elif net < 0:
            # 反向事件 -net 次
            rev = -net
            if species_key in rxn["reactants"] and species_key not in rxn["products"]:
                producers.append({"reaction_name": name, "count": rev})
                print(f"[Debug] Added to producers (reverse): {name}, count: {rev}")
            if species_key in rxn["products"] and species_key not in rxn["reactants"]:
                consumers.append({"reaction_name": name, "count": rev})
                print(f"[Debug] Added to consumers (reverse): {name}, count: {rev}")

    return producers, consumers

def summarize_species_flow(species_key, merged_data, transformations,
                           ignore_diffusion=False,
                           output_path=None, overwrite=False):
    """
    对 species_key：
      - 正向 (net>0) 用 forward map
      - 反向 (net<0) 用 reverse map
    自动分类 producers/consumers，并写 summary 文件。
    返回 summary dict 包含 producers, consumers, generated_from, transformed_to。
    """
    # 1. 分类
    producers, consumers = analyze_species(merged_data, species_key, ignore_diffusion)
    net_map = {rxn["reaction_name"]: rxn["net_count"] for rxn in merged_data}

    fwd_map = transformations["forward"]
    rev_map = transformations["reverse"]

    # 2. 生成来源
    gen_map = {}
    for e in producers:
        rxn, cnt = e["reaction_name"], e["count"]
        if net_map[rxn] > 0:                          # 正向
            for r, ps in fwd_map[rxn].items():
                if species_key in ps:
                    gen_map[r] = gen_map.get(r, 0) + cnt
        else:                                         # 反向
            for prod, r_list in rev_map[rxn].items():     # 注意：遍历 items
                if species_key in r_list:                  # species_key 在 value
                    gen_map[prod] = gen_map.get(prod, 0) + cnt

    # 3. 消耗去向
    to_map = {}
    for e in consumers:
        rxn, cnt = e["reaction_name"], e["count"]
        if net_map[rxn] > 0:                       # 正向
            for p in fwd_map[rxn].get(species_key, []):
                to_map[p] = to_map.get(p, 0) + cnt
        else:                                      # 反向
            for prod, r_list in rev_map[rxn].items():
                if prod == species_key:            # species_key 在 key
                    for r in r_list:               # value 列表都是被消耗的物种
                        to_map[r] = to_map.get(r, 0) + cnt

    # 4. 写文件
    if not output_path:
        safe = species_key.replace('*','').replace('(','').replace(')','')
        output_path = f"summary_{safe}.txt"
    if overwrite or not os.path.exists(output_path):
        total_gen = sum(e["count"] for e in producers)
        total_con = sum(e["count"] for e in consumers)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"Species: {species_key}\n\n")

            f.write(f"Generated (total +{total_gen}):\n")
            for e in producers:
                f.write(f"  {e['reaction_name']:50s} +{e['count']}\n")
            f.write("By reactant contributions:\n")
            for sp, c in gen_map.items():
                f.write(f"  {sp:50s} +{c}\n")

            f.write(f"\nConsumed (total -{total_con}):\n")
            for e in consumers:
                f.write(f"  {e['reaction_name']:50s} -{e['count']}\n")
            f.write("By product contributions:\n")
            for sp, c in to_map.items():
                f.write(f"  {sp:50s} -{c}\n")
        print(f"[Saved] Summary written to {output_path}")
    else:
        print(f"[Info] {output_path} exists; set overwrite=True to replace.")

    return {
        "producers": producers,
        "consumers": consumers,
        "generated_from": gen_map,
        "transformed_to": to_map
    }

# 绘图: 从 transformations dict 生成网络 PNG + GraphML
import math
import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional, Union, Dict

def draw_reaction_network(
    transformations: Dict,  # 如果你希望更明确类型可用 Dict[str, Any]
    outfile_prefix: str = "reaction_network",
    highlight_species: Optional[str] = None,
    skip_self_loops: bool = True,
    use_graphviz: bool = True,
    summary_filter: Optional[Dict] = None,
    fig_width: Optional[float] = None,
    fig_height: Optional[float] = None
):
    """
    根据 transformations = {"forward": {...}, "reverse": {...}}
    画全量正/逆反应网络图，并导出：
        outfile_prefix + ".png"
        outfile_prefix + ".graphml"
    如果 highlight_species 给定，则把该节点染成橙色并加粗描边。
    可自定义 fig_width, fig_height（单位：英寸）
    """
    import math
    import networkx as nx
    import matplotlib.pyplot as plt

    fwd, rev = transformations["forward"], transformations["reverse"]
    G = nx.DiGraph(name="Reaction Network (auto-generated)")

    allowed_edges = set()
    if summary_filter and highlight_species:
        srcs = set(summary_filter["generated_from"].keys())
        tgts = set(summary_filter["transformed_to"].keys())
        for r in srcs:
            allowed_edges.add((r, highlight_species))
        for t in tgts:
            allowed_edges.add((highlight_species, t))

    for rxn, mapping in fwd.items():
        for reactant, products in mapping.items():
            for p in products:
                if skip_self_loops and reactant == p:
                    continue
                if summary_filter and (reactant, p) not in allowed_edges:
                    continue
                G.add_edge(reactant, p, reaction=rxn, direction="fwd")

    for rxn, mapping in rev.items():
        for product, reactants in mapping.items():
            for r in reactants:
                if skip_self_loops and r == product:
                    continue
                if summary_filter and (product, r) not in allowed_edges:
                    continue
                G.add_edge(product, r, reaction=rxn, direction="rev")

    if G.number_of_nodes() == 0:
        print("[Warn] network is empty, skip drawing.")
        return
    
    try:
        if summary_filter and highlight_species:

            pos = nx.spring_layout(G, seed=42, k=1.5)
        elif G.number_of_nodes() <= 10:

            pos = nx.spring_layout(G, seed=42, k=1.5)
        else:

            pos = nx.spring_layout(G, seed=42, k=8.5,scale=5.0)
    except Exception as e:
        print("[Fallback] layout failed, using basic spring layout:", e)
        pos = nx.spring_layout(G, seed=42, k=2.0)




    NODE_SIZE = 2000
    EDGE_WIDTH = 5
    ARROW_SIZE = 9
    FONT_SIZE = 7

    edge_cols = ["#E24A33AA" if d["direction"] == "fwd" else "#348ABD88"
                 for _, _, d in G.edges(data=True)]

    node_cols = []
    node_edges = []
    for n in G.nodes():
        if highlight_species and n == highlight_species:
            node_cols.append("#FFA34E")
            node_edges.append("#CC5500")
        else:
            node_cols.append("#A6D854")
            node_edges.append("#555555")

    # 自定义或自动推算画布大小
    fig_w = fig_width or max(14, G.number_of_nodes() * 0.14)
    fig_h = fig_height or (0.75 * fig_w)

    plt.figure(figsize=(fig_w, fig_h), dpi=300)

    nx.draw_networkx_nodes(
        G, pos,
        node_size=NODE_SIZE,
        node_color=node_cols,
        edgecolors=node_edges,
        linewidths=1.4
    )
    nx.draw_networkx_edges(
        G, pos,
        arrows=True,
        edge_color=edge_cols,
        width=EDGE_WIDTH,
        arrowsize=ARROW_SIZE,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.07"
    )
    nx.draw_networkx_labels(
        G, pos,
        font_size=FONT_SIZE,
        font_color="#000000"
    )

    plt.title(f"Reaction Network (highlight: {highlight_species})"
              if highlight_species else "Reaction Network",
              fontsize=12, pad=12)

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(outfile_prefix + ".png", bbox_inches="tight")
    nx.write_graphml(G, outfile_prefix + ".graphml")






def main(directory, species_key,
         ignore_diffusion=False,
         mapping_path='transformations.json',
         overwrite_mapping=True,
         overwrite_summary=True,
         ini_config=None,
         fin_config=None):
    procfile = os.path.join(directory, 'procstat_output.txt')
    genfile = os.path.join(directory, 'general_output.txt')
    procstat_data = parse_procstat_output(procfile, ini_config=ini_config, fin_config=fin_config)
    general_data = parse_general_output(genfile)
    merged_data = merge_reaction_data(procstat_data, general_data)
    species_comp = element_analysis_with_pymatgen(merged_data)
    transformations = identify_transformations(
        merged_data, species_comp,
        mapping_path=mapping_path,
    )
    return summarize_species_flow(
        species_key, merged_data, transformations,
        ignore_diffusion=ignore_diffusion,
        overwrite=overwrite_summary
    )

if __name__ == "__main__":
#    directory = input("请输入包含 procstat_output.txt 和 general_output.txt 的文件夹路径： ")
#    species_key = input("请输入要分析的物种名称（如 CH3*_Cu(hollowCu)）： ")
    directory =  r"C:\Users\qq126\Documents\Vinita_KMC_results\test"
    species_key = "CH3*_Cu(hollowCu)"
    result = main(
        directory, species_key,
        ignore_diffusion=True,
        mapping_path='transformations.json',
        overwrite_mapping=True,  # 强制重新生成映射
        overwrite_summary=True
    )
    print("\n--- Summary ---")
    print(f"Generated by (+{sum(e['count'] for e in result['producers'])}):")
    for e in result['producers']:
        print(f"  {e['reaction_name']:50s} +{e['count']}")
    print("Comes from :")
    for r, c in result['generated_from'].items():
        print(f"  {r:50s} +{c}")
    print(f"\nProducing to (-{sum(e['count'] for e in result['consumers'])}):")
    for e in result['consumers']:
        print(f"  {e['reaction_name']:50s} -{e['count']}")
    print("product:")
    for p, c in result['transformed_to'].items():
        print(f"  {p:50s} -{c}")
    
    
    
    
    with open('transformations.json', 'r', encoding='utf-8') as f:
        transformations = json.load(f)
    draw_reaction_network(
        transformations,
        outfile_prefix="reaction_network_full",
        highlight_species=species_key,         # 高亮目标物种
        skip_self_loops=True,                  # 忽略自环
        use_graphviz=True,                      # 若已装 pygraphviz
        summary_filter=result
    )