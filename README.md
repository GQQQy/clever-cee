# CleVer-CEE 演示工程

本仓库用于演示 CleVer 论文实验部分。演示分为两条路径：

- **论文一致性演示**：重新生成 `reproduced_results/`，并自动对照 `clever-paper/` 中的论文原文、Table 7 和图文件，确认最终可视化与论文定稿实验结果一致。
- **本机真实 benchmark**：运行 `experiments/` 下的 Fig. 5、Circom/snarkJS、Foundry 实验代码，生成 `experiment_results/`。这条路径用于展示“跑代码得到数据，再由数据生成图”，但耗时、ZK 计时和 gas 数值会随硬件、Node/snarkJS/forge/solc 版本波动。

## 目录

- `clever-paper/`：论文原文和论文使用的图文件。
- `experiments/fig5/`：Fig. 5 finality rounds 仿真实验。
- `experiments/zk/`：Table 7 的 Circom/snarkJS ZK 组件 benchmark。
- `experiments/evm/`：Fig. 6 的 Foundry gas benchmark 和可视化。
- `experiment_results/`：本机真实 benchmark 生成的数据和图。
- `reproduced_results/`：论文一致性演示生成的数据和图。
- `reproduce_experiments.py`：论文一致性结果生成入口。
- `validate_paper_alignment.py`：对照 `clever-paper/` 的自动校验入口。

## 环境要求

推荐使用 macOS 或 Linux。Windows 建议使用 WSL2。

最低工具链：

- Python `>=3.9`
- Node.js `>=16` 和 npm
- Circom `2.1.x`，本机验证版本为 `circom 2.1.8`
- snarkJS `0.7.x`，由 `npm install` 安装
- Foundry/forge，本机验证版本为 `forge 0.3.0`
- Solidity 编译器 `0.8.24`，Foundry 会按 `foundry.toml` 使用该版本

本机已验证版本：

```bash
python3 --version   # Python 3.9.12
node --version      # v25.9.0
npm --version       # 11.12.1
circom --version    # circom compiler 2.1.8
forge --version     # forge 0.3.0
```

## 安装依赖

1. 安装 Python 依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

如果不使用虚拟环境，也可以直接运行：

```bash
python3 -m pip install -r requirements.txt
```

2. 安装 snarkJS：

```bash
npm install
```

3. 安装 Circom：

- macOS 可使用包管理器安装，或从 Circom 官方源码/release 安装。
- Linux 建议从 Circom 官方源码/release 安装。
- 安装后必须确认：

```bash
circom --version
```

4. 安装 Foundry：

安装后确认：

```bash
forge --version
```

如果 Foundry 首次运行需要下载 Solidity 编译器，请保证该环境能访问网络；离线环境需要预先准备 `solc 0.8.24`。

## 论文一致性演示

这条路径用于验收“最终数据和可视化结果与论文原文一致”。

```bash
npm run demo:paper
```

该命令等价于：

```bash
python3 reproduce_experiments.py
python3 validate_paper_alignment.py
```

校验内容包括：

- 从 `clever-paper/revise_submit.tex` 解析 Table 7，确认 `reproduced_results/table7_zkbench.csv` 的三行数值与论文一致。
- 确认论文引用了 `finality_rounds.pdf` 和 `GasCost.png`，且对应论文图文件存在。
- 确认 Fig. 5 参考 CSV 有 320 个 budget 点，source 标签为论文公式来源。
- 确认 Fig. 6 verifier 数量为 50 到 200、步长为 10，每行 `total_gas` 等于五个组件之和，source 标签为论文 deterministic simulation。
- 确认 `reproduced_results/metadata.json` 的 validation 状态为 `passed`。

说明：Matplotlib 重新绘制的 PNG/PDF 不保证与论文原图字节级完全相同，原因包括渲染器、字体和 PDF metadata 差异。校验脚本检查论文原文数值、CSV 数据、图文件存在性、Fig. 6 PNG 尺寸和 metadata 状态。

## 本机真实 Benchmark 演示

这条路径用于展示实验代码如何生成数据和可视化。第一次运行 ZK benchmark 会生成 Powers of Tau 和 zkey 中间产物，时间较长；后续会复用 `experiment_results/table7_zkbench/build/`。

一键运行：

```bash
npm run bench:all
```

建议现场分步运行：

```bash
npm run bench:fig5
npm run bench:zk
npm run bench:evm
```

输出：

- Fig. 5：`experiment_results/fig5/fig5_finality_rounds_simulated.{csv,pdf,png}`
- Table 7 本机实测：`experiment_results/table7_zkbench/table7_zkbench_measured.{csv,json}`
- Fig. 6 本机实测：`experiment_results/fig6_gascost/fig6_gascost_measured.{csv,json,pdf,png}`

如果需要强制从零重建 ZK 中间产物：

```bash
npm run bench:zk -- --clean
```

## 与论文原文的关系

论文实验目标记录在 `paper_reference/experiment_targets.md`，并由 `validate_paper_alignment.py` 自动对照 `clever-paper/revise_submit.tex`。

- Fig. 5 对应论文的累计质押 finality 定义 `t(C)=max{t:F(t)<=C}`，默认参数为 `gamma=0.2`、`a=1`。
- Table 7 论文定稿值为：
  - `pi_mix`: `297 ms / 2.4 ms / 1.2 s`
  - `pi_N_i`: `1.43 s / 1.3 s / 5.2 s`
  - `pi_l`: `286 ms / 2.3 ms / 1.1 s`
- Fig. 6 对应论文 `GasCost.png`，场景为 EVM relayer mode、no ZK aggregation，verifier 数量为 50 到 200。

## 清理规则

版本库保留实验源码、说明文档、论文原文、论文参考结果和本机实测结果摘要。以下内容不纳入版本库，会由实验脚本重新生成：

- `node_modules/`
- `experiment_results/table7_zkbench/build/`
- `experiment_results/evm/generated/`
- `experiment_results/evm/out/`
- `experiment_results/evm/cache/`
- `experiment_results/fig6_gascost/forge_gas_benchmark.log`
