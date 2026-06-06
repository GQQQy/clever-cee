#!/usr/bin/env python3
"""Reproduce the final CleVer demo artifacts for Fig. 5, Table 7, and Fig. 6.

The demo is intentionally paper-aligned:

* Fig. 5 is regenerated from the cumulative staking/finality formula.
* Table 7 is exported from the exact values reported in the manuscript.
* Fig. 6 is regenerated from the deterministic gas-cost model used for the
  manuscript figure.

The generated metadata records provenance and a small consistency check so the
CSV data, figures, and paper-reported values stay tied together.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Callable, Dict, Iterable, List

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "clever_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


DEFAULT_OUT_DIR = Path("reproduced_results")


TABLE7_ROWS = [
    {
        "circuit": "pi_mix",
        "circuit_latex": r"$\pi_{\text{mix}}$",
        "compile_time": "297 ms",
        "compile_seconds": 0.297,
        "proof_gen_time": "2.4 ms",
        "proof_gen_seconds": 0.0024,
        "setup_time": "1.2 s",
        "setup_seconds": 1.2,
        "source": "paper_reported_table7",
    },
    {
        "circuit": "pi_N_i",
        "circuit_latex": r"$\pi_{N_i}$",
        "compile_time": "1.43 s",
        "compile_seconds": 1.43,
        "proof_gen_time": "1.3 s",
        "proof_gen_seconds": 1.3,
        "setup_time": "5.2 s",
        "setup_seconds": 5.2,
        "source": "paper_reported_table7",
    },
    {
        "circuit": "pi_l",
        "circuit_latex": r"$\pi_\ell$",
        "compile_time": "286 ms",
        "compile_seconds": 0.286,
        "proof_gen_time": "2.3 ms",
        "proof_gen_seconds": 0.0023,
        "setup_time": "1.1 s",
        "setup_seconds": 1.1,
        "source": "paper_reported_table7",
    },
]


def ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError(f"no rows to write for {path}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def cumulative_schedule(
    f: Callable[[int], float], max_budget: float, max_rounds: int = 1_000_000
) -> np.ndarray:
    """Return [F(0), F(1), ..., F(t)] until F(t) exceeds max_budget."""
    values: List[float] = [0.0]
    total = 0.0
    round_index = 1
    while total <= max_budget:
        total += f(round_index)
        values.append(total)
        round_index += 1
        if round_index > max_rounds:
            raise RuntimeError(
                f"staking schedule did not exceed budget {max_budget} "
                f"within {max_rounds} rounds"
            )
    return np.asarray(values, dtype=float)


def inverse_rounds(cumulative: np.ndarray, budgets: np.ndarray) -> np.ndarray:
    """Generalized inverse: max t such that F(t) <= C."""
    return np.searchsorted(cumulative, budgets, side="right") - 1


def compute_fig5_finality(
    min_budget: float = 10.0,
    max_budget: float = 100_000.0,
    num_points: int = 320,
    gamma: float = 0.2,
    linear_a: float = 1.0,
    log_a: float = 1.0,
) -> Dict[str, np.ndarray]:
    budgets = np.logspace(math.log10(min_budget), math.log10(max_budget), num_points)
    schedules = {
        "multiplicative": cumulative_schedule(
            lambda s: (1.0 + gamma) ** (s - 1), max_budget
        ),
        "linear": cumulative_schedule(lambda s: linear_a * s, max_budget),
        "logarithmic": cumulative_schedule(lambda s: log_a * math.log(s + 1), max_budget),
    }
    return {
        "budget": budgets,
        "multiplicative_rounds": inverse_rounds(schedules["multiplicative"], budgets),
        "linear_rounds": inverse_rounds(schedules["linear"], budgets),
        "logarithmic_rounds": inverse_rounds(schedules["logarithmic"], budgets),
        "gamma": np.asarray([gamma]),
        "linear_a": np.asarray([linear_a]),
        "log_a": np.asarray([log_a]),
    }


def plot_fig5_finality(data: Dict[str, np.ndarray], out_dir: Path) -> None:
    plt.figure(figsize=(10, 7.5))
    plt.plot(
        data["budget"],
        data["multiplicative_rounds"],
        color="#e69f00",
        linewidth=2.5,
        label="Multiplicative f(s): f(s+1) >= (1+gamma)f(s)",
    )
    plt.plot(
        data["budget"],
        data["linear_rounds"],
        color="#56b4e9",
        linewidth=2.5,
        label="Linear f(s) = a*s",
    )
    plt.plot(
        data["budget"],
        data["logarithmic_rounds"],
        color="#009e73",
        linewidth=2.5,
        label="Logarithmic f(s) = a*log(s+1)",
    )
    plt.xscale("log")
    plt.xlim(10, 100_000)
    plt.ylim(-500, 12_500)
    plt.yticks(np.arange(0, 12_001, 2_000))
    plt.xlabel("Adversary budget C (log scale)", fontsize=18)
    plt.ylabel("Max blocking rounds t(C)", fontsize=18)
    plt.title("Finality rounds under different staking schedules f(s)", fontsize=24)
    plt.legend(loc="upper left", fontsize=14, frameon=True)
    plt.grid(True, which="major", linestyle="--", alpha=0.65)
    plt.tick_params(axis="both", which="major", labelsize=16)
    plt.tight_layout()
    plt.savefig(out_dir / "fig5_finality_rounds.pdf")
    plt.savefig(out_dir / "fig5_finality_rounds.png", dpi=160)
    plt.close()


def export_fig5_finality(out_dir: Path) -> Dict[str, object]:
    data = compute_fig5_finality()
    rows = []
    for i, budget in enumerate(data["budget"]):
        rows.append(
            {
                "budget_C": f"{budget:.8f}",
                "multiplicative_rounds": int(data["multiplicative_rounds"][i]),
                "linear_rounds": int(data["linear_rounds"][i]),
                "logarithmic_rounds": int(data["logarithmic_rounds"][i]),
                "source": "paper_fig5_formula_generalized_inverse",
            }
        )
    write_csv(out_dir / "fig5_finality_rounds.csv", rows)
    plot_fig5_finality(data, out_dir)
    return {
        "figure": "fig5_finality_rounds",
        "source": "paper_fig5_formula_generalized_inverse",
        "parameters": {"gamma": 0.2, "linear_a": 1.0, "log_a": 1.0},
        "outputs": [
            "fig5_finality_rounds.csv",
            "fig5_finality_rounds.pdf",
            "fig5_finality_rounds.png",
        ],
    }


def compute_fig6_gas(seed: int = 42) -> Dict[str, np.ndarray]:
    """Return deterministic gas-cost rows for the paper's Fig. 6.

    The manuscript reports the Fig. 6 gas breakdown as a deterministic
    relayer-mode simulation over 50..200 verifiers. Keeping the seed and per
    component coefficients fixed makes the plotted CSV and labels reproducible.
    """
    user_counts = np.arange(50, 201, 10)
    rng = np.random.RandomState(seed)

    zk_per_user = 250_000
    storage_per_user = 40_000
    ec_per_user = 7_000
    mapping_per_user = 200
    logic_per_user = 5_000

    zk_gas = (
        user_counts
        * zk_per_user
        * (1 + rng.uniform(-0.02, 0.02, len(user_counts)))
    ).astype(int)
    storage_gas = (
        user_counts
        * storage_per_user
        * (1 + rng.uniform(-0.03, 0.03, len(user_counts)))
    ).astype(int)
    ec_gas = (
        user_counts
        * ec_per_user
        * (1 + rng.uniform(-0.05, 0.05, len(user_counts)))
    ).astype(int)
    mapping_gas = (
        user_counts
        * mapping_per_user
        * (1 + rng.uniform(-0.1, 0.1, len(user_counts)))
    ).astype(int)
    logic_gas = (
        user_counts
        * logic_per_user
        * (1 + rng.uniform(-0.1, 0.1, len(user_counts)))
    ).astype(int)
    total_gas = zk_gas + storage_gas + ec_gas + mapping_gas + logic_gas

    return {
        "user_counts": user_counts,
        "zk_proof_verification": zk_gas,
        "storage_append": storage_gas,
        "ec_operations": ec_gas,
        "mapping_lookup": mapping_gas,
        "control_logic": logic_gas,
        "total_gas": total_gas,
    }


def plot_fig6_gas(data: Dict[str, np.ndarray], out_dir: Path) -> None:
    user_counts = data["user_counts"]
    x = np.arange(len(user_counts))
    bar_width = 0.6

    zk_gas = data["zk_proof_verification"]
    storage_gas = data["storage_append"]
    ec_gas = data["ec_operations"]
    mapping_gas = data["mapping_lookup"]
    logic_gas = data["control_logic"]
    total_gas = data["total_gas"]

    plt.figure(figsize=(14, 8))
    plt.bar(x, zk_gas, bar_width, label="ZK Proof Verification", color="#9fb5d9")
    plt.bar(
        x,
        storage_gas,
        bar_width,
        bottom=zk_gas,
        label="Storage Append",
        color="#f7a1ab",
    )
    plt.bar(
        x,
        ec_gas,
        bar_width,
        bottom=zk_gas + storage_gas,
        label="EC Operations",
        color="#97a19a",
    )
    plt.bar(
        x,
        mapping_gas,
        bar_width,
        bottom=zk_gas + storage_gas + ec_gas,
        label="Mapping Lookup",
        color="#a78bfa",
    )
    plt.bar(
        x,
        logic_gas,
        bar_width,
        bottom=zk_gas + storage_gas + ec_gas + mapping_gas,
        label="Control Logic",
        color="#fbdc7c",
    )

    for i, value in enumerate(total_gas):
        plt.text(
            i,
            value + 10_000,
            f"{value / 1e6:.1f}M",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )

    plt.xticks(x, [str(n) for n in user_counts])
    plt.xlabel("Number of Verifiers")
    plt.ylabel("Gas Usage (in Gas Units)")
    plt.title("Gas Cost Breakdown vs. Number of Verifiers\n(Relayer Mode, No ZK Aggregation)")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(out_dir / "fig6_gascost.png", dpi=100)
    plt.savefig(out_dir / "fig6_gascost.pdf")
    plt.close()


def export_fig6_gas(out_dir: Path) -> Dict[str, object]:
    data = compute_fig6_gas()
    rows = []
    for i, verifiers in enumerate(data["user_counts"]):
        rows.append(
            {
                "verifiers": int(verifiers),
                "zk_proof_verification": int(data["zk_proof_verification"][i]),
                "storage_append": int(data["storage_append"][i]),
                "ec_operations": int(data["ec_operations"][i]),
                "mapping_lookup": int(data["mapping_lookup"][i]),
                "control_logic": int(data["control_logic"][i]),
                "total_gas": int(data["total_gas"][i]),
                "total_gas_millions_label": f"{data['total_gas'][i] / 1e6:.1f}M",
                "source": "paper_fig6_deterministic_simulation_seed_42",
            }
        )
    write_csv(out_dir / "fig6_gascost.csv", rows)
    plot_fig6_gas(data, out_dir)
    return {
        "figure": "fig6_gascost",
        "source": "paper_fig6_deterministic_simulation_seed_42",
        "outputs": ["fig6_gascost.csv", "fig6_gascost.png", "fig6_gascost.pdf"],
    }


def table7_latex(rows: List[Dict[str, object]]) -> str:
    body = []
    for row in rows:
        body.append(
            "{circuit} & {compile_time} & {proof_gen_time} & {setup_time} \\\\".format(
                **row
            )
        )
    return "\n".join(
        [
            r"\begin{tabular}{lccc}",
            r"\toprule",
            r"\textbf{Circuit} & \textbf{Compile Time} & \textbf{Proof Gen Time} & \textbf{Setup Time} \\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabular}",
            "",
        ]
    )


def export_table7(out_dir: Path) -> Dict[str, object]:
    rows = [dict(row) for row in TABLE7_ROWS]
    write_csv(out_dir / "table7_zkbench.csv", rows)
    write_json(out_dir / "table7_zkbench.json", rows)
    write_json(
        out_dir / "table7_zkbench_metadata.json",
        {
            "source": "paper_reported_table7",
            "used_fallback": True,
            "reason": (
                "The final demonstration exports the manuscript-reported "
                "Table 7 values directly. This keeps the demo aligned with the "
                "paper instead of replacing the table with machine-dependent "
                "reruns."
            ),
        },
    )
    latex_rows = []
    for row in rows:
        display_row = dict(row)
        display_row["circuit"] = display_row["circuit_latex"]
        latex_rows.append(display_row)
    (out_dir / "table7_zkbench.tex").write_text(
        table7_latex(latex_rows), encoding="utf-8"
    )
    return {
        "table": "table7_zkbench",
        "source": "paper_reported_table7",
        "outputs": [
            "table7_zkbench.csv",
            "table7_zkbench.json",
            "table7_zkbench_metadata.json",
            "table7_zkbench.tex",
        ],
    }


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def require_nonempty(path: Path, errors: List[str]) -> None:
    if not path.exists():
        errors.append(f"missing output: {path}")
    elif path.stat().st_size == 0:
        errors.append(f"empty output: {path}")


def validate_fig5(out_dir: Path, errors: List[str]) -> None:
    csv_path = out_dir / "fig5_finality_rounds.csv"
    require_nonempty(csv_path, errors)
    require_nonempty(out_dir / "fig5_finality_rounds.pdf", errors)
    require_nonempty(out_dir / "fig5_finality_rounds.png", errors)
    if not csv_path.exists():
        return

    rows = read_csv(csv_path)
    expected = compute_fig5_finality()
    if len(rows) != len(expected["budget"]):
        errors.append(f"Fig. 5 row count mismatch: {len(rows)}")
        return

    for i, row in enumerate(rows):
        checks = {
            "multiplicative_rounds": int(expected["multiplicative_rounds"][i]),
            "linear_rounds": int(expected["linear_rounds"][i]),
            "logarithmic_rounds": int(expected["logarithmic_rounds"][i]),
        }
        for key, expected_value in checks.items():
            if int(row[key]) != expected_value:
                errors.append(f"Fig. 5 mismatch at row {i}, {key}")
                return
        if row["source"] != "paper_fig5_formula_generalized_inverse":
            errors.append(f"Fig. 5 source mismatch at row {i}")
            return


def validate_table7(out_dir: Path, errors: List[str]) -> None:
    csv_path = out_dir / "table7_zkbench.csv"
    require_nonempty(csv_path, errors)
    require_nonempty(out_dir / "table7_zkbench.json", errors)
    require_nonempty(out_dir / "table7_zkbench.tex", errors)
    if not csv_path.exists():
        return

    rows = read_csv(csv_path)
    if len(rows) != len(TABLE7_ROWS):
        errors.append(f"Table 7 row count mismatch: {len(rows)}")
        return

    keys = [
        "circuit",
        "compile_time",
        "proof_gen_time",
        "setup_time",
        "source",
    ]
    for row, expected in zip(rows, TABLE7_ROWS):
        for key in keys:
            if row[key] != str(expected[key]):
                errors.append(f"Table 7 mismatch for {expected['circuit']} {key}")
                return


def validate_fig6(out_dir: Path, errors: List[str]) -> None:
    csv_path = out_dir / "fig6_gascost.csv"
    require_nonempty(csv_path, errors)
    require_nonempty(out_dir / "fig6_gascost.pdf", errors)
    require_nonempty(out_dir / "fig6_gascost.png", errors)
    if not csv_path.exists():
        return

    rows = read_csv(csv_path)
    expected = compute_fig6_gas()
    expected_counts = [int(v) for v in expected["user_counts"]]
    if [int(row["verifiers"]) for row in rows] != expected_counts:
        errors.append("Fig. 6 verifier sequence mismatch")
        return

    components = [
        "zk_proof_verification",
        "storage_append",
        "ec_operations",
        "mapping_lookup",
        "control_logic",
    ]
    for i, row in enumerate(rows):
        total = 0
        for component in components:
            value = int(row[component])
            if value != int(expected[component][i]):
                errors.append(f"Fig. 6 mismatch at row {i}, {component}")
                return
            total += value
        if total != int(row["total_gas"]):
            errors.append(f"Fig. 6 total mismatch at row {i}")
            return
        if row["source"] != "paper_fig6_deterministic_simulation_seed_42":
            errors.append(f"Fig. 6 source mismatch at row {i}")
            return


def validate_outputs(out_dir: Path, generated: List[Dict[str, object]]) -> Dict[str, object]:
    selected = {str(item.get("figure") or item.get("table")) for item in generated}
    errors: List[str] = []
    if "fig5_finality_rounds" in selected:
        validate_fig5(out_dir, errors)
    if "table7_zkbench" in selected:
        validate_table7(out_dir, errors)
    if "fig6_gascost" in selected:
        validate_fig6(out_dir, errors)

    if errors:
        raise RuntimeError("output validation failed:\n" + "\n".join(errors))

    return {
        "status": "passed",
        "checked_artifacts": sorted(selected),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce CleVer Fig. 5, Table 7, and Fig. 6 artifacts."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Directory for generated figures, tables, and data.",
    )
    parser.add_argument(
        "--only",
        choices=["all", "fig5", "table7", "fig6"],
        default="all",
        help="Select a single artifact or generate all artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    ensure_out_dir(out_dir)

    generated = []
    if args.only in ("all", "fig5"):
        generated.append(export_fig5_finality(out_dir))
    if args.only in ("all", "table7"):
        generated.append(export_table7(out_dir))
    if args.only in ("all", "fig6"):
        generated.append(export_fig6_gas(out_dir))

    validation = validate_outputs(out_dir, generated)
    metadata = {
        "paper": "CleVer",
        "artifacts": generated,
        "validation": validation,
        "integrity_note": (
            "Generated outputs distinguish formula-derived, paper-reported, "
            "and deterministic simulation sources. They should not be "
            "presented as newly measured raw benchmarks unless the missing "
            "original implementations are supplied and rerun."
        ),
    }
    write_json(out_dir / "metadata.json", metadata)
    print(f"Wrote {len(generated)} artifact group(s) to {out_dir}")


if __name__ == "__main__":
    main()
