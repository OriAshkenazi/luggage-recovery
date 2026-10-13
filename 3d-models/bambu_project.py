#!/usr/bin/env python3
"""Slice the two-part tag into print-ready Bambu Studio projects (P1S + AMS).

Runs Bambu Studio's command line on the STLs from ``two_part_tag.py`` and writes
``front_half.3mf`` and ``back_half.3mf`` next to them. Each project already has the base on
filament 1 and the inlay on filament 2, the P1S 0.4 mm nozzle at 0.20 mm layers, and the
first-layer settings flush inlays need (elephant-foot compensation 0, 0.42 mm first-layer
lines). Each is sliced, so it can be sent to the printer as is, and the slice is checked:
the dark filament may only print on the inlay layers.

    python 3d-models/bambu_project.py [--filament "Bambu PLA Basic"] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
APP = Path(os.environ.get("BAMBU_STUDIO", "/Applications/BambuStudio.app"))
PRINTER = "Bambu Lab P1S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL X1C"
BASE_COLOUR, INLAY_COLOUR = "#F5C400", "#1A1A1A"
INLAY_LAYERS = 3  # 0.6 mm at 0.20 mm


def _profiles() -> Path:
    p = APP / "Contents/Resources/profiles/BBL"
    if not p.exists():
        raise SystemExit(f"Bambu Studio profiles not found at {p} (set BAMBU_STUDIO to the app)")
    return p


def _binary() -> List[str]:
    exe = APP / "Contents/MacOS/BambuStudio"
    if not exe.exists():
        raise SystemExit(f"Bambu Studio not found at {exe}")
    # Run the native arm64 slice on Apple silicon, never under Rosetta
    if sys.platform == "darwin" and platform.machine() == "arm64":
        return ["arch", "-arm64", str(exe)]
    return [str(exe)]


def _flatten(kind: str, name: str) -> Dict:
    """A system preset with its ``inherits`` chain resolved, as the CLI needs it."""
    d = json.loads((_profiles() / kind / f"{name}.json").read_text())
    if "inherits" in d:
        base = _flatten(kind, d["inherits"])
        base.update({k: v for k, v in d.items() if k != "inherits"})
        d = base
    d.pop("inherits", None)
    d["from"], d["instantiation"] = "system", "true"
    return d


def _filament(name: str) -> Dict:
    for variant in (f"{name} @BBL P1S 0.4 nozzle", f"{name} @BBL P1S", f"{name} @BBL X1C"):
        if (_profiles() / "filament" / f"{variant}.json").exists():
            d = _flatten("filament", variant)
            if PRINTER in d.get("compatible_printers", []) or not d.get("compatible_printers"):
                return d
    raise SystemExit(f"No {PRINTER} preset for filament {name!r}")


def _check_slice(gcode: str) -> dict:
    """Dark filament (T1) only on the inlay layers; returns swaps and per-layer use."""
    lines = gcode.splitlines()
    first = next((l for l in lines if re.match(r"^M620 S[01]A", l)), "M620 S1A")
    tool = "1" if first.startswith("M620 S0A") else "0"  # the start G-code loads the other one
    layer, swaps, dark_layers = 0, 0, set()
    for line in lines:
        if line.startswith("; CHANGE_LAYER"):
            layer += 1
        m = re.match(r"^T([01])$", line)
        if m:
            swaps += m.group(1) != tool
            tool = m.group(1)
        if tool == "1" and layer and line.startswith(("G1 ", "G2 ", "G3 ")) and " X" in line and re.search(r" E[\d.]+", line):
            dark_layers.add(layer)
    if not dark_layers or max(dark_layers) > INLAY_LAYERS or 1 not in dark_layers:
        raise SystemExit(f"Unexpected slice: dark filament on layers {sorted(dark_layers)}")
    t = re.search(r"total estimated time: ([^;\n]+)", gcode)
    return {"layers": layer, "dark_layers": sorted(dark_layers), "swaps": swaps, "time": t.group(1).strip() if t else None}


def build(out: Path, filament: str, inlay_filament: Optional[str] = None, plate: str = "Textured PEI Plate") -> dict:
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        process = _flatten("process", PROCESS)
        process.update({"elefant_foot_compensation": "0", "initial_layer_line_width": "0.42",
                        "filament_map": ["1", "1"], "filament_map_mode": "Manual", "curr_bed_type": plate})
        files = {"machine.json": _flatten("machine", PRINTER), "process.json": process}
        for fname, name, colour in (("base.json", filament, BASE_COLOUR), ("inlay.json", inlay_filament or filament, INLAY_COLOUR)):
            d = _filament(name)
            d["filament_colour"] = [colour]
            files[fname] = d
        for fname, d in files.items():
            (tmp / fname).write_text(json.dumps(d))
        for half in ("front", "back"):
            work = tmp / half
            work.mkdir()
            cmd = _binary() + [
                "--load-settings", f"{tmp / 'machine.json'};{tmp / 'process.json'}",
                "--load-filaments", f"{tmp / 'base.json'};{tmp / 'inlay.json'}",
                "--load-filament-ids", "1,2", "--assemble", "--arrange", "1", "--orient", "0",
                "--allow-multicolor-oneplate", "--slice", "0",
                "--export-3mf", f"{half}_half.3mf", "--outputdir", str(work),
                str(out / f"{half}_base.stl"), str(out / f"{half}_inlay.stl"),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            project = work / f"{half}_half.3mf"
            if proc.returncode != 0 or not project.exists():
                raise SystemExit(f"Bambu Studio failed on the {half} half (exit {proc.returncode}):\n{proc.stdout[-1500:]}{proc.stderr[-1500:]}")
            with zipfile.ZipFile(project) as z:
                results[half] = _check_slice(z.read("Metadata/plate_1.gcode").decode())
            shutil.copy2(project, out / project.name)
    return results


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Make print-ready Bambu Studio projects for the two-part tag")
    ap.add_argument("--out", type=Path, default=HERE / "outputs" / "two-part", help="folder with the STLs from two_part_tag.py")
    ap.add_argument("--filament", default="Bambu PLA Basic", help='system filament for both colours, e.g. "Bambu PETG HF"')
    ap.add_argument("--inlay-filament", help="a different system filament for the inlay")
    ap.add_argument("--plate", default="Textured PEI Plate", choices=["Textured PEI Plate", "Cool Plate", "Engineering Plate", "High Temp Plate"],
                    help="build plate (the P1S ships with Textured PEI; a smooth plate gives a glossy face)")
    args = ap.parse_args(argv)
    for half in ("front", "back"):
        for part in ("base", "inlay"):
            if not (args.out / f"{half}_{part}.stl").exists():
                raise SystemExit(f"Missing {half}_{part}.stl in {args.out}: run two_part_tag.py first")
    for half, r in build(args.out, args.filament, args.inlay_filament, args.plate).items():
        print(f"{half}_half.3mf: {r['layers']} layers, dark on layers {r['dark_layers']}, {r['swaps']} colour swaps, {r['time']}")
    print(f"{args.filament} on the {args.plate}. Open in Bambu Studio, put light filament in AMS slot 1 and dark in slot 2, print.")


if __name__ == "__main__":
    main()
