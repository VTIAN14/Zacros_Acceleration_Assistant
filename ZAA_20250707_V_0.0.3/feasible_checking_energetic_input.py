import os
from parse_energetics_file import parse_energetics_file

VACANCY_TOKEN   = "*"          # site must be empty
WILDCARD_TOKEN  = "&"          # any species allowed
WILDCARD_MARKER = "__ANY__"    # stored in lattice when wildcard encountered

def check_energetics_feasibility(selected_folder):
    """检查指定文件夹中的 energetics_input.dat 文件的可行性"""
    energetics_file = os.path.join(selected_folder, "energetics_input.dat")
    
    if not os.path.exists(energetics_file):
        print(f"Error: 在 {selected_folder} can not find energetics_input.dat file")
        return []
    
    clusters = parse_energetics_file(energetics_file)
    for c in clusters:
        dentate_info = f" (dentate={c.get('dentate', 1)})" if c.get('dentate', 1) > 1 else ""
        print(f"[{c['type']}] {c['name']} - energy: {c['energy']}{dentate_info}")
    
    # =========================================================
    from typing import List, Dict, Any, Tuple, Set

    def validate_ecis(clusters: List[Dict[str, Any]]) -> List[str]:
        singles: Set[Tuple[str, str | None]] = {
            (site["species"], site["site_type"])
            for c in clusters if c["type"] == "on-site"
            for site in c["lattice"].values()
            if site["species"] not in (None, WILDCARD_MARKER)
        }

        alerts: List[str] = []
        for c in clusters:
            if c["type"] != "eci":
                continue
            missing = {
                (s["species"], s["site_type"])
                for s in c["lattice"].values()
                if s["species"] not in (None, WILDCARD_MARKER)
                and (s["species"], s["site_type"]) not in singles
            }
            if missing:
                alerts.append(
                    f"[WARN] ECI '{c['name']}' (id={c['id']}) lacks on‑site: {sorted(missing)}"
                )
        return alerts

    alerts = validate_ecis(clusters)                    
    result = "\n".join(alerts) or "All ECIs are covered "
    print(result)
    return alerts

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        selected_folder = sys.argv[1]
        check_energetics_feasibility(selected_folder)
    else:
        print("请提供文件夹路径作为参数")

