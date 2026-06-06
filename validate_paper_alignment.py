#!/usr/bin/env python3
"""Validate that generated paper-reference artifacts match the manuscript.

This check is intentionally focused on the final paper-aligned outputs in
`reproduced_results/`. Local benchmark results in `experiment_results/` are
machine-dependent and are validated by running the benchmark scripts
themselves.
"""

from __future__ import annotations

import csv
import json
import re
import struct
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parent
PAPER_DIR = ROOT / "clever-paper"
RESULT_DIR = ROOT / "reproduced_results"


def require(condition: bool, message: str, errors: List[str]) -> None:
    if not condition:
        errors.append(message)


def require_file(path: Path, errors: List[str]) -> None:
    if not path.exists():
        errors.append(f"missing file: {path.relative_to(ROOT)}")
    elif path.stat().st_size <= 0:
        errors.append(f"empty file: {path.relative_to(ROOT)}")


def compact_latex_cell(value: str) -> str:
    value = value.replace(r"\,", "")
    value = value.replace("\\", "")
    value = value.strip()
    value = re.sub(r"\s+", "", value)
    return value


def parse_paper_table7(tex_path: Path) -> Dict[str, Dict[str, str]]:
    text = tex_path.read_text(encoding="utf-8")
    start = text.index(r"\label{tab:zkbench}")
    end = text.index(r"\bottomrule", start)
    block = text[start:end]

    rows: Dict[str, Dict[str, str]] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if "&" not in line or r"\pi" not in line:
            continue

        if r"\pi_{\text{mix}}" in line:
            circuit = "pi_mix"
        elif r"\pi_{N_i}" in line:
            circuit = "pi_N_i"
        elif r"\pi_\ell" in line:
            circuit = "pi_l"
        else:
            continue

        parts = [part.strip() for part in line.split("&")]
        if len(parts) < 4:
            continue
        rows[circuit] = {
            "compile_time": compact_latex_cell(parts[1]),
            "proof_gen_time": compact_latex_cell(parts[2]),
            "setup_time": compact_latex_cell(parts[3].rstrip(r"\\")),
        }

    return rows


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        header = fh.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG file: {path}")
    return struct.unpack(">II", header[16:24])


def validate_table7(errors: List[str]) -> None:
    before = len(errors)
    tex_path = PAPER_DIR / "revise_submit.tex"
    table_path = RESULT_DIR / "table7_zkbench.csv"
    require_file(tex_path, errors)
    require_file(table_path, errors)
    if len(errors) > before:
        return

    expected = parse_paper_table7(tex_path)
    rows = read_csv_rows(table_path)
    require(set(expected) == {"pi_mix", "pi_N_i", "pi_l"}, "failed to parse paper Table 7 rows", errors)
    require(len(rows) == 3, f"Table 7 CSV row count is {len(rows)}, expected 3", errors)

    for row in rows:
        circuit = row["circuit"]
        require(circuit in expected, f"unexpected Table 7 circuit: {circuit}", errors)
        if circuit not in expected:
            continue
        for key in ("compile_time", "proof_gen_time", "setup_time"):
            actual = compact_latex_cell(row[key])
            require(
                actual == expected[circuit][key],
                f"Table 7 mismatch for {circuit} {key}: {actual} != {expected[circuit][key]}",
                errors,
            )


def validate_fig5(errors: List[str]) -> None:
    before = len(errors)
    tex_path = PAPER_DIR / "revise_submit.tex"
    paper_pdf = PAPER_DIR / "finality_rounds.pdf"
    csv_path = RESULT_DIR / "fig5_finality_rounds.csv"
    png_path = RESULT_DIR / "fig5_finality_rounds.png"
    pdf_path = RESULT_DIR / "fig5_finality_rounds.pdf"
    for path in (tex_path, paper_pdf, csv_path, png_path, pdf_path):
        require_file(path, errors)
    if len(errors) > before:
        return

    text = tex_path.read_text(encoding="utf-8")
    require("finality_rounds.pdf" in text, "paper does not reference finality_rounds.pdf", errors)
    rows = read_csv_rows(csv_path)
    require(len(rows) == 320, f"Fig. 5 CSV row count is {len(rows)}, expected 320", errors)
    if rows:
        require(rows[0]["budget_C"] == "10.00000000", "Fig. 5 first budget is not 10", errors)
        require(rows[-1]["source"] == "paper_fig5_formula_generalized_inverse", "Fig. 5 source tag mismatch", errors)


def validate_fig6(errors: List[str]) -> None:
    before = len(errors)
    tex_path = PAPER_DIR / "revise_submit.tex"
    paper_png = PAPER_DIR / "GasCost.png"
    csv_path = RESULT_DIR / "fig6_gascost.csv"
    png_path = RESULT_DIR / "fig6_gascost.png"
    pdf_path = RESULT_DIR / "fig6_gascost.pdf"
    for path in (tex_path, paper_png, csv_path, png_path, pdf_path):
        require_file(path, errors)
    if len(errors) > before:
        return

    text = tex_path.read_text(encoding="utf-8")
    require("GasCost.png" in text, "paper does not reference GasCost.png", errors)
    rows = read_csv_rows(csv_path)
    verifier_counts = [int(row["verifiers"]) for row in rows]
    require(verifier_counts == list(range(50, 201, 10)), "Fig. 6 verifier counts are not 50..200 step 10", errors)

    components = [
        "zk_proof_verification",
        "storage_append",
        "ec_operations",
        "mapping_lookup",
        "control_logic",
    ]
    for row in rows:
        total = sum(int(row[component]) for component in components)
        require(total == int(row["total_gas"]), f"Fig. 6 total mismatch at {row['verifiers']} verifiers", errors)
        require(
            row["source"] == "paper_fig6_deterministic_simulation_seed_42",
            f"Fig. 6 source tag mismatch at {row['verifiers']} verifiers",
            errors,
        )

    if paper_png.exists() and png_path.exists():
        require(
            png_size(paper_png) == png_size(png_path),
            f"Fig. 6 PNG size mismatch: paper {png_size(paper_png)} vs generated {png_size(png_path)}",
            errors,
        )


def validate_metadata(errors: List[str]) -> None:
    metadata_path = RESULT_DIR / "metadata.json"
    require_file(metadata_path, errors)
    if not metadata_path.exists():
        return
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    require(metadata.get("validation", {}).get("status") == "passed", "metadata validation status is not passed", errors)
    checked = set(metadata.get("validation", {}).get("checked_artifacts", []))
    require(
        checked == {"fig5_finality_rounds", "fig6_gascost", "table7_zkbench"},
        f"metadata checked artifacts mismatch: {sorted(checked)}",
        errors,
    )


def main() -> None:
    errors: List[str] = []
    validate_metadata(errors)
    validate_table7(errors)
    validate_fig5(errors)
    validate_fig6(errors)

    if errors:
        print("Paper alignment validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Paper alignment validation passed.")
    print(f"- Paper source: {PAPER_DIR.relative_to(ROOT)}")
    print(f"- Generated reference outputs: {RESULT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
