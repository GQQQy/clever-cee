#!/usr/bin/env python3
"""Simulate CleVer challenge finality under different staking schedules.

This is the executable experiment behind Fig. 5. For each adversary budget C,
a stubborn adversary repeatedly submits invalid challenges. Each blocked round
burns f(s)+fee from the adversary. The simulator counts the maximum blocked
rounds before the next honest challenge must be admitted.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/clever_mplconfig")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class StakingSchedule:
    name: str
    label: str
    color: str
    stake: Callable[[int], float]


def simulate_blocking_rounds(
    budget: float,
    schedule: StakingSchedule,
    fee: float,
    invalid_challengers_per_round: int,
) -> int:
    """Return maximum invalid rounds the adversary can sustain."""
    remaining = float(budget)
    rounds = 0
    s = 1
    while True:
        round_cost = invalid_challengers_per_round * (schedule.stake(s) + fee)
        if remaining + 1e-12 < round_cost:
            return rounds
        remaining -= round_cost
        rounds += 1
        s += 1


def make_schedules(gamma: float, linear_a: float, log_a: float) -> List[StakingSchedule]:
    return [
        StakingSchedule(
            name="multiplicative",
            label="Multiplicative f(s): f(s+1) >= (1+gamma)f(s)",
            color="#e69f00",
            stake=lambda s: (1.0 + gamma) ** (s - 1),
        ),
        StakingSchedule(
            name="linear",
            label="Linear f(s) = a*s",
            color="#56b4e9",
            stake=lambda s: linear_a * s,
        ),
        StakingSchedule(
            name="logarithmic",
            label="Logarithmic f(s) = a*log(s+1)",
            color="#009e73",
            stake=lambda s: log_a * math.log(s + 1),
        ),
    ]


def write_csv(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError(f"no rows to write for {path}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(args: argparse.Namespace) -> List[Dict[str, object]]:
    budgets = np.logspace(
        math.log10(args.min_budget), math.log10(args.max_budget), args.points
    )
    schedules = make_schedules(args.gamma, args.linear_a, args.log_a)
    rows: List[Dict[str, object]] = []

    for budget in budgets:
        row: Dict[str, object] = {
            "budget_C": f"{budget:.8f}",
            "fee": args.fee,
            "invalid_challengers_per_round": args.invalid_challengers,
        }
        for schedule in schedules:
            row[f"{schedule.name}_blocked_rounds"] = simulate_blocking_rounds(
                budget,
                schedule,
                args.fee,
                args.invalid_challengers,
            )
        rows.append(row)
    return rows


def plot(rows: List[Dict[str, object]], args: argparse.Namespace, out_dir: Path) -> None:
    budgets = np.array([float(row["budget_C"]) for row in rows])
    schedules = make_schedules(args.gamma, args.linear_a, args.log_a)

    plt.figure(figsize=(10, 7.5))
    for schedule in schedules:
        y = np.array([int(row[f"{schedule.name}_blocked_rounds"]) for row in rows])
        plt.plot(budgets, y, label=schedule.label, color=schedule.color, linewidth=2.5)

    plt.xscale("log")
    plt.xlim(args.min_budget, args.max_budget)
    plt.ylim(args.ymin, args.ymax)
    plt.yticks(np.arange(0, args.ymax + 1, args.ytick))
    plt.xlabel("Adversary budget C (log scale)", fontsize=18)
    plt.ylabel("Max blocking rounds t(C)", fontsize=18)
    plt.title("Finality rounds under different staking schedules f(s)", fontsize=24)
    plt.legend(loc="upper left", fontsize=14, frameon=True)
    plt.grid(True, which="major", linestyle="--", alpha=0.65)
    plt.tick_params(axis="both", which="major", labelsize=16)
    plt.tight_layout()
    plt.savefig(out_dir / "fig5_finality_rounds_simulated.png", dpi=160)
    plt.savefig(out_dir / "fig5_finality_rounds_simulated.pdf")
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CleVer Fig. 5 finality simulation.")
    parser.add_argument("--out-dir", type=Path, default=Path("experiment_results/fig5"))
    parser.add_argument("--min-budget", type=float, default=10.0)
    parser.add_argument("--max-budget", type=float, default=100_000.0)
    parser.add_argument("--points", type=int, default=320)
    parser.add_argument("--gamma", type=float, default=0.2)
    parser.add_argument("--linear-a", type=float, default=1.0)
    parser.add_argument("--log-a", type=float, default=1.0)
    parser.add_argument("--fee", type=float, default=0.0)
    parser.add_argument("--invalid-challengers", type=int, default=1)
    parser.add_argument("--ymin", type=float, default=-500)
    parser.add_argument("--ymax", type=float, default=12_500)
    parser.add_argument("--ytick", type=float, default=2_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = run_experiment(args)
    write_csv(args.out_dir / "fig5_finality_rounds_simulated.csv", rows)
    plot(rows, args, args.out_dir)
    print(f"Wrote Fig. 5 simulation outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
