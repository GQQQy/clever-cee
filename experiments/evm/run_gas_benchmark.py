#!/usr/bin/env python3
"""Run Foundry gas benchmark and render CleVer Fig. 6.

The Solidity test emits GasSample(component, verifiers, gasUsed) events. This
runner parses those real measurements, writes CSV/JSON, and draws the stacked
bar chart used for Fig. 6.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "clever_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


COMPONENTS = [
    ("zk_proof_verification", "ZK Proof Verification", "#9fb5d9"),
    ("storage_append", "Storage Append", "#f7a1ab"),
    ("ec_operations", "EC Operations", "#97a19a"),
    ("mapping_lookup", "Mapping Lookup", "#a78bfa"),
    ("control_logic", "Control Logic", "#fbdc7c"),
]


EVENT_PATTERNS = [
    re.compile(
        r"GasSample\(\s*component:\s*\"(?P<component>[^\"]+)\"\s*,\s*"
        r"verifiers:\s*(?P<verifiers>\d+)\s*,\s*gasUsed:\s*(?P<gas>\d+)"
        r"(?:\s*\[[^\]]+\])?\s*\)"
    ),
    re.compile(
        r"GasSample\(\s*\"(?P<component>[^\"]+)\"\s*,\s*"
        r"(?P<verifiers>\d+)\s*,\s*(?P<gas>\d+)"
        r"(?:\s*\[[^\]]+\])?\s*\)"
    ),
    re.compile(
        r"GasSample.*?(?P<component>zk_proof_verification|storage_append|ec_operations|mapping_lookup|control_logic)"
        r".*?(?P<verifiers>\d+).*?(?P<gas>\d+)"
    ),
]


def run_forge(extra_args: List[str]) -> subprocess.CompletedProcess[str]:
    command = [
        "forge",
        "test",
        "--match-test",
        "testGasBenchmark",
        "-vvvv",
        *extra_args,
    ]
    return subprocess.run(command, text=True, capture_output=True, check=False)


def run_checked(command: List[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout.strip()


def parse_solidity_calldata(calldata: str) -> object:
    return json.loads(f"[{calldata}]")


def uint_literal(value: str) -> str:
    return str(int(value, 16)) if value.startswith("0x") else str(int(value))


def generate_verifier_and_proof_sources() -> None:
    """Generate Solidity verifier/proof files from the latest pi_mix proof.

    If the ZK benchmark has not been run yet, the checked-in placeholder files
    remain in place so the gas benchmark can still compile. The intended demo
    order is `bench:zk` first, then `bench:evm`, which replaces the placeholders
    with snarkJS-generated verifier/proof data.
    """
    src_dir = Path("experiment_results/evm/generated")
    src_dir.mkdir(parents=True, exist_ok=True)
    zkey = Path("experiment_results/table7_zkbench/build/pi_mix/pi_mix_final.zkey")
    proof = Path("experiment_results/table7_zkbench/build/pi_mix/proof.json")
    public = Path("experiment_results/table7_zkbench/build/pi_mix/public.json")
    snarkjs = Path("node_modules/.bin/snarkjs")

    if not (zkey.exists() and proof.exists() and public.exists() and snarkjs.exists()):
        write_placeholder_generated_sources(src_dir)
        return

    run_checked(
        [
            str(snarkjs),
            "zkey",
            "export",
            "solidityverifier",
            str(zkey),
            str(src_dir / "PiMixVerifier.sol"),
        ]
    )
    calldata = run_checked(
        [
            str(snarkjs),
            "zkey",
            "export",
            "soliditycalldata",
            str(public),
            str(proof),
        ]
    )
    p_a, p_b, p_c, pub_signals = parse_solidity_calldata(calldata)

    proof_source = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

library PiMixProofData {{
    function pA() internal pure returns (uint256[2] memory out) {{
        out[0] = {uint_literal(p_a[0])};
        out[1] = {uint_literal(p_a[1])};
    }}

    function pB() internal pure returns (uint256[2][2] memory out) {{
        out[0][0] = {uint_literal(p_b[0][0])};
        out[0][1] = {uint_literal(p_b[0][1])};
        out[1][0] = {uint_literal(p_b[1][0])};
        out[1][1] = {uint_literal(p_b[1][1])};
    }}

    function pC() internal pure returns (uint256[2] memory out) {{
        out[0] = {uint_literal(p_c[0])};
        out[1] = {uint_literal(p_c[1])};
    }}

    function pubSignals() internal pure returns (uint256[2] memory out) {{
        out[0] = {uint_literal(pub_signals[0])};
        out[1] = {uint_literal(pub_signals[1])};
    }}
}}
"""
    (src_dir / "PiMixProofData.sol").write_text(proof_source, encoding="utf-8")


def write_placeholder_generated_sources(src_dir: Path) -> None:
    verifier = src_dir / "PiMixVerifier.sol"
    proof = src_dir / "PiMixProofData.sol"
    if not verifier.exists():
        verifier.write_text(
            """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Groth16Verifier {
    function verifyProof(
        uint256[2] memory,
        uint256[2][2] memory,
        uint256[2] memory,
        uint256[2] memory
    ) public pure returns (bool) {
        return true;
    }
}
""",
            encoding="utf-8",
        )
    if not proof.exists():
        proof.write_text(
            """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

library PiMixProofData {
    function pA() internal pure returns (uint256[2] memory out) {
        out[0] = 1;
        out[1] = 2;
    }

    function pB() internal pure returns (uint256[2][2] memory out) {
        out[0][0] = 1;
        out[0][1] = 2;
        out[1][0] = 3;
        out[1][1] = 4;
    }

    function pC() internal pure returns (uint256[2] memory out) {
        out[0] = 1;
        out[1] = 2;
    }

    function pubSignals() internal pure returns (uint256[2] memory out) {
        out[0] = 1;
        out[1] = 2;
    }
}
""",
            encoding="utf-8",
        )


def parse_events(log_text: str) -> List[Dict[str, object]]:
    rows = []
    for line in log_text.splitlines():
        for pattern in EVENT_PATTERNS:
            match = pattern.search(line)
            if match:
                rows.append(
                    {
                        "component": match.group("component"),
                        "verifiers": int(match.group("verifiers")),
                        "gas_used": int(match.group("gas")),
                    }
                )
                break
    return rows


def aggregate_rows(events: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    by_count: Dict[int, Dict[str, int]] = defaultdict(dict)
    for row in events:
        by_count[int(row["verifiers"])][str(row["component"])] = int(row["gas_used"])

    output = []
    for verifiers in sorted(by_count):
        values = by_count[verifiers]
        missing = [component for component, _, _ in COMPONENTS if component not in values]
        if missing:
            raise RuntimeError(f"missing components for {verifiers} verifiers: {missing}")
        total = sum(values[component] for component, _, _ in COMPONENTS)
        row = {"verifiers": verifiers}
        for component, _, _ in COMPONENTS:
            row[component] = values[component]
        row["total_gas"] = total
        row["total_gas_millions_label"] = f"{total / 1e6:.1f}M"
        output.append(row)
    return output


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def plot(rows: List[Dict[str, object]], out_dir: Path) -> None:
    verifiers = np.array([row["verifiers"] for row in rows])
    x = np.arange(len(verifiers))
    bottom = np.zeros(len(verifiers), dtype=float)

    plt.figure(figsize=(14, 8))
    for component, label, color in COMPONENTS:
        values = np.array([row[component] for row in rows])
        plt.bar(x, values, 0.6, bottom=bottom, label=label, color=color)
        bottom += values

    for i, total in enumerate(bottom):
        plt.text(
            i,
            total + max(bottom) * 0.01,
            f"{total / 1e6:.1f}M",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )

    plt.xticks(x, [str(v) for v in verifiers])
    plt.xlabel("Number of Verifiers")
    plt.ylabel("Gas Usage (in Gas Units)")
    plt.title("Gas Cost Breakdown vs. Number of Verifiers\n(Relayer Mode, No ZK Aggregation)")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(out_dir / "fig6_gascost_measured.png", dpi=100)
    plt.savefig(out_dir / "fig6_gascost_measured.pdf")
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real EVM gas benchmark for CleVer Fig. 6.")
    parser.add_argument("--out-dir", type=Path, default=Path("experiment_results/fig6_gascost"))
    parser.add_argument(
        "--forge-arg",
        action="append",
        default=[],
        help="Additional argument passed to forge test. Repeat for multiple args.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    generate_verifier_and_proof_sources()
    result = run_forge(args.forge_arg)
    log_text = result.stdout + "\n" + result.stderr
    (args.out_dir / "forge_gas_benchmark.log").write_text(log_text, encoding="utf-8")

    if result.returncode != 0:
        raise SystemExit(
            f"forge test failed with exit code {result.returncode}; "
            f"see {args.out_dir / 'forge_gas_benchmark.log'}"
        )

    events = parse_events(log_text)
    if not events:
        raise SystemExit(
            "no GasSample events parsed; see "
            f"{args.out_dir / 'forge_gas_benchmark.log'}"
        )

    rows = aggregate_rows(events)
    write_csv(args.out_dir / "fig6_gascost_measured.csv", rows)
    write_json(
        args.out_dir / "fig6_gascost_measured.json",
        {
            "source": "foundry_measured_solidity_gas",
            "components": [component for component, _, _ in COMPONENTS],
            "rows": rows,
        },
    )
    plot(rows, args.out_dir)
    print(f"Wrote measured Fig. 6 gas outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
