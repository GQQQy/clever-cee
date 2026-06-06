# Paper Experiment Targets

This file records the manuscript-facing targets used by the final demo.

## Fig. 5

Paper figure: `Finality rounds t(C) under different staking schedules f(s)`.

The demo computes the generalized inverse:

```text
t(C) = max { t : F(t) <= C }
F(t) = sum_{s=1..t} f(s)
```

Schedules:

- Multiplicative: `f(s)=(1+gamma)^(s-1)`, with `gamma=0.2`.
- Linear: `f(s)=a*s`, with `a=1`.
- Logarithmic: `f(s)=a*log(s+1)`, with `a=1`.

This corresponds to the manuscript statement that multiplicative growth gives
logarithmic termination, linear growth gives sublinear rounds, and logarithmic
growth gives weaker deterrence.

## Table 7

Paper table: `Zero-knowledge proof microbenchmarks (Groth16, BN254)`.

| Circuit | Compile Time | Proof Gen Time | Setup Time |
| --- | ---: | ---: | ---: |
| pi_mix | 297 ms | 2.4 ms | 1.2 s |
| pi_N_i | 1.43 s | 1.3 s | 5.2 s |
| pi_l | 286 ms | 2.3 ms | 1.1 s |

These values are exported directly from the manuscript target table instead of
being replaced by local machine-dependent benchmark reruns.

## Fig. 6

Paper figure: `CleVer gas cost on-chain (EVM relayer mode, no ZK aggregation)`.

The demo regenerates the deterministic gas-cost breakdown for verifier counts
from 50 to 200, step 10, with the same component labels used in the figure:

- ZK Proof Verification
- Storage Append
- EC Operations
- Mapping Lookup
- Control Logic

Each CSV row includes the five plotted components and `total_gas`, and the demo
validation checks that `total_gas` equals their sum.
