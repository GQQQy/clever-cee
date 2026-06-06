# CleVer-CEE 演示工程

本仓库是 CleVer 论文实验部分的最终演示包。演示时先运行实验代码得到数据，
再通过这些数据生成可视化结果。当前保留三组最终演示实验：

- Fig. 5：不同 staking schedule 下的 finality rounds 仿真。
- Table 7：Circom/snarkJS 的 ZK proof microbenchmarks。
- Fig. 6：EVM relayer mode、no ZK aggregation 下的 gas cost breakdown。

`experiments/` 是正式演示入口，输出写入 `experiment_results/`。
`reproduced_results/` 是论文原文对齐参考结果，用于核对最终论文里的图表数值。

## 环境准备

使用 Python 3、Node.js、Circom、Foundry。绘图脚本需要：

```bash
python3 -m pip install -r requirements.txt
```

安装 snarkJS：

```bash
npm install
```

本机已验证工具链：

- `circom`
- `snarkjs`
- `forge`
- Python 3 + `numpy` + `matplotlib`

## 演示方式

生成全部最终演示实验结果：

```bash
npm run bench:all
```

建议现场演示时分步运行，便于展示每个实验如何产生数据和可视化：

```bash
npm run bench:fig5
npm run bench:zk
npm run bench:evm
```

如果只需要生成论文原文对齐参考结果，运行：

```bash
npm run paper:reference
```

## 实验输出

Fig. 5 输出：

- `experiment_results/fig5/fig5_finality_rounds_simulated.csv`
- `experiment_results/fig5/fig5_finality_rounds_simulated.pdf`
- `experiment_results/fig5/fig5_finality_rounds_simulated.png`

Table 7 输出：

- `experiment_results/table7_zkbench/table7_zkbench_measured.csv`
- `experiment_results/table7_zkbench/table7_zkbench_measured.json`
- `experiment_results/table7_zkbench/build/`

Fig. 6 输出：

- `experiment_results/fig6_gascost/fig6_gascost_measured.csv`
- `experiment_results/fig6_gascost/fig6_gascost_measured.json`
- `experiment_results/fig6_gascost/fig6_gascost_measured.pdf`
- `experiment_results/fig6_gascost/fig6_gascost_measured.png`
- `experiment_results/fig6_gascost/forge_gas_benchmark.log`

## 论文参考输出

`reproduced_results/` 中保留论文原文对齐参考结果：

- `fig5_finality_rounds.csv`
- `fig5_finality_rounds.pdf`
- `fig5_finality_rounds.png`
- `table7_zkbench.csv`
- `table7_zkbench.json`
- `table7_zkbench.tex`
- `table7_zkbench_metadata.json`
- `fig6_gascost.csv`
- `fig6_gascost.pdf`
- `fig6_gascost.png`
- `metadata.json`

运行 `python3 reproduce_experiments.py` 会重新生成这些参考结果，并在写入
`metadata.json` 前执行一致性校验：

- Table 7 的三行数值必须等于论文原文报告值。
- Fig. 6 每行 `total_gas` 必须等于五个可视化组件之和。
- Fig. 5 的 CSV 行必须能由论文中的 staking/finality 公式重新计算得到。

## 与论文原文的对应关系

实验目标摘要放在 `paper_reference/experiment_targets.md`。

- Fig. 5 对应论文中的累计质押 finality 定义
  `t(C)=max{t:F(t)<=C}` with `gamma=0.2`, `a=1`.
- Table 7 使用论文原文数值：
  `pi_mix = 297 ms / 2.4 ms / 1.2 s`,
  `pi_N_i = 1.43 s / 1.3 s / 5.2 s`,
  `pi_l = 286 ms / 2.3 ms / 1.1 s`.
- Fig. 6 使用 50 到 200 个 verifiers 的 deterministic gas-cost simulation，
  场景为 relayer mode、no ZK aggregation。

当前仓库保留最终实验代码和论文参考数据。依赖目录、缓存和 proof/build
中间产物不纳入版本库，演示时由实验脚本重新生成。
