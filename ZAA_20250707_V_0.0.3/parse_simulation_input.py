from pathlib import Path
import pandas as pd

def parse_simulation_input(path: Path):
    lines = path.read_text().splitlines()

    n_surf_species_line    = next(l for l in lines if 'n_surf_species'    in l)
    surf_specs_names_line  = next(l for l in lines if 'surf_specs_names'  in l)
    surf_specs_dent_line   = next(l for l in lines if 'surf_specs_dent'   in l)

    n_surf_species = int(n_surf_species_line.split()[1])
    surf_specs_names = surf_specs_names_line.split()[1:]
    surf_specs_dent  = list(map(int, surf_specs_dent_line.split()[1:]))

    if not (len(surf_specs_names) == len(surf_specs_dent) == n_surf_species):
        raise ValueError(
            f"Mismatch in species data: "
            f"n_surf_species = {n_surf_species}, "
            f"names = {len(surf_specs_names)}, "
            f"dentate = {len(surf_specs_dent)}"
        )

    dent_map = dict(zip(surf_specs_names, surf_specs_dent))
    df = pd.DataFrame({
        "species": surf_specs_names,
        "dentate": surf_specs_dent
    })

    return n_surf_species, dent_map, df
