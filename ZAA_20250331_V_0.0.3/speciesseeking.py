import os
import re
import json
from pymatgen.core import Composition

def extract_core_formula(species_name):
    m = re.match(r'^([A-Z][a-z]?\d*)+', species_name)
    return m.group(0) if m else ""

def compute_overlap(comp1, comp2):
    return sum(min(comp1[e], comp2[e]) for e in comp1.keys() & comp2.keys())

def parse_procstat_output(file_path,ini_config=None, fin_config=None):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    reactions = re.split(r'\s+', lines[0].strip())
    reactions = [r for r in reactions if r.lower() != 'overall']
    
    #Collect the configuration lines.
    config_data = {}
    for i in range(len(lines)):
       if lines[i].startswith("configuration"):
           parts = lines[i].split()
           if len(parts) >= 2 and parts[1].isdigit():
               cfg_num = int(parts[1])
               int_counts_line = lines[i + 2].strip()
               counts = [int(c) for c in re.split(r'\s+', int_counts_line)]
               config_data[cfg_num] = counts
    
    if ini_config is None or fin_config is None:
        print('hello')
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
            stats.append({
                "reaction_name": fwd[:-4],
                "fwd_count": fwd_c,
                "rev_count": rev_c,
                "net_count": net
            })
        return stats

    if ini_config not in config_data or fin_config not in config_data:
        raise ValueError(f"INI ({ini_config}) 或 FIN ({fin_config}) 配置未在文件中找到")

    ini_counts = config_data[ini_config]
    fin_counts = config_data[fin_config]
    print('ini_counts')
    print(ini_counts)
    stats = []
    for i in range(0, len(reactions), 2):
        rxn_name = reactions[i][:-4]
        ini_fwd, ini_rev = ini_counts[i], ini_counts[i + 1]
        fin_fwd, fin_rev = fin_counts[i], fin_counts[i + 1]
    
        delta_fwd = fin_fwd - ini_fwd
        delta_rev = fin_rev - ini_rev
        delta_net = delta_fwd - delta_rev  
    
        stats.append({
            "reaction_name": rxn_name,
            "fwd_count": delta_fwd,
            "rev_count": delta_rev,
            "net_count": delta_net
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

def main(directory, species_key,
         ignore_diffusion=False,
         mapping_path='transformations.txt',
         overwrite_mapping=True,
         overwrite_summary=False,ini_config=None,
         fin_config=None):
    procfile = os.path.join(directory, 'procstat_output.txt')
    genfile = os.path.join(directory, 'general_output.txt')
    procstat_data = parse_procstat_output(procfile,ini_config,fin_config)
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
    species_key = "CH3O*_Cu(hollowCu)"
    result = main(
        directory, species_key,
        ignore_diffusion=True,
        mapping_path='transformations.txt',
        overwrite_mapping=True,  # 强制重新生成映射
        overwrite_summary=False,ini_config=None,
        fin_config=None
    )
    print(result)
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