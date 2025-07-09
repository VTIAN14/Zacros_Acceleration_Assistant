from pathlib import Path
import pandas as pd
def parse_lattice_block(path: Path, block="lattice_structure", block_site="site_type_names"):
    lines = path.read_text().splitlines()
    
    #site_type_name_save
    site_line = next(l for l in lines if block_site in l)
    site_names = site_line.split()[1:] #site_name_list
    site_map = {i + 1 :name for i, name in enumerate(site_names)}
    #lattice_structure block
    start = next(i for i,l in enumerate(lines) if block in l) + 1
    end   = next(i for i,l in enumerate(lines[start:], start) if "end_"+block in l)
    recs  = []
    for l in lines[start:end]:
        p = l.split()
        if not p or not p[0].isdigit():
            continue
        site_idx = int(p[3])
        coord_num = int(p[4])
        #warning for index not found 如果没有这个site比如就两个site写的3会处这个warning
        if site_idx not in site_map:
            print(f"Warning: site index {site_idx} not found in site_type_names.")
        recs.append({
            "idx": int(p[0]),
            "x"  : float(p[1]),
            "y"  : float(p[2]),
            "site": site_map.get(site_idx, f"Unknown{site_idx}"),
            "coord_num":coord_num,
            "nbrs": [n for n in map(int, p[5:]) if n > 0]
        })
    return pd.DataFrame(recs)