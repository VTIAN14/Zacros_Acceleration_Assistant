from parse_energetics_file import parse_energetics_file

VACANCY_TOKEN   = "*"          # site must be empty
WILDCARD_TOKEN  = "&"          # any species allowed
WILDCARD_MARKER = "__ANY__"    # stored in lattice when wildcard encountered

clusters = parse_energetics_file(f"C:/Users/qq126/Documents/ZAA_test_example/energetics_input.dat")
for c in clusters:
    print(f"[{c['type']}] {c['name']} - energy: {c['energy']}")
    

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
print("\n".join(alerts) or "All ECIs are covered 🎉")

