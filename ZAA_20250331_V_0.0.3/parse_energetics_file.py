from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set


VACANCY_TOKEN   = "*"          # site must be empty
WILDCARD_TOKEN  = "&"          # any species allowed
WILDCARD_MARKER = "__ANY__"    # stored in lattice when wildcard encountered


def parse_energetics_file(filepath: str | Path) -> List[Dict[str, Any]]:
    """Parse *filepath* and return cluster dictionaries.

    • Vacancies (`*`) saved as species == None
    • Wildcards (`&`) saved as species == WILDCARD_MARKER
    • Keeps true site order so it aligns with `site_types`
    """
    fp = Path(filepath)

    # ---- strip comments ----
    with fp.open(encoding="utf-8") as fh:
        raw = [ln.rstrip("\n") for ln in fh if not ln.lstrip().startswith("#")]

    # ---- isolate energetics block ----
    # ---- isolate energetics block ----
    block, grabbing = [], False
    for ln in raw:
        s = ln.strip()
        if s == "end_energetics":
            break
        if s.startswith("cluster "):
            grabbing = True  # ensure current line is included
        if grabbing:
            block.append(s)


    clusters: List[Dict[str, Any]] = []
    i = cid = 0

    while i < len(block):
        if not block[i].startswith("cluster "):
            i += 1
            continue

        cid += 1
        cl: Dict[str, Any] = {
            "id": cid,
            "name": block[i].split("cluster", 1)[1].strip(),
            "sites": None,
            "lattice": {"species": {}},
            "vacancy_sites": set(),
            "wildcard_sites": set(),
            "neighboring": [],
            "energy": None,
            "type": None,
            "raw_lattice_lines": [],
        }
        i += 1

        # ---- parse until end_cluster ----
        while i < len(block) and not block[i].startswith("end_cluster"):
            line = block[i]

            if line.startswith("sites"):
                cl["sites"] = int(line.split()[1])

            elif line.startswith("lattice_state"):
                i += 1
                while i < len(block) and not block[i].startswith(("site_types", "end_cluster")):
                    ln = block[i]
                    cl["raw_lattice_lines"].append(ln)
                    tokens = ln.split()
                    if not tokens:
                        i += 1
                        continue

                    idx = len(cl["lattice"]["species"]) + 1  # site index = line position
                    sp = tokens[1] if tokens[0].isdigit() else tokens[0]

                    if sp == VACANCY_TOKEN:
                        cl["lattice"]["species"][idx] = None
                        cl["vacancy_sites"].add(idx)
                    elif sp == WILDCARD_TOKEN:
                        cl["lattice"]["species"][idx] = WILDCARD_MARKER
                        cl["wildcard_sites"].add(idx)
                    else:
                        cl["lattice"]["species"][idx] = sp

                    i += 1
                continue  # done with lattice_state block

            elif line.startswith("site_types"):
                cl["lattice"]["site_types"] = line.split()[1:]

            elif line.startswith("neighboring"):
                cl["neighboring"] = [tuple(map(int, x.split("-"))) for x in line.split()[1:]]

            elif line.startswith("cluster_eng"):
                cl["energy"] = float(line.split()[1])

            i += 1  # advance inside cluster

        # skip end_cluster token
        if i < len(block):
            i += 1

        # ---- finalize lattice mapping ----
        spmap = cl["lattice"].get("species", {})
        stypes = cl["lattice"].get("site_types", [])
        n = cl["sites"] or max(len(spmap), len(stypes))
        cl["lattice"] = {
            j: {
                "species": spmap.get(j),
                "site_type": stypes[j - 1] if j - 1 < len(stypes) else None,
            }
            for j in range(1, n + 1)
        }

        # ---- classify cluster ----
        ads_ids = {
            int(m.group(1))
            for ln in cl["raw_lattice_lines"]
            if (m := re.match(r"^(\d+)\s+\S+", ln))
        }
        cl["type"] = "on-site" if len(ads_ids) == 1 else "eci"

        clusters.append(cl)

    return clusters