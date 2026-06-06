#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { performance } = require("perf_hooks");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..", "..");
const CIRCUIT_DIR = path.join(__dirname, "circuits");
const OUT_DIR = path.join(ROOT, "experiment_results", "table7_zkbench");
const BUILD_DIR = path.join(OUT_DIR, "build");
const PTAU_POWER = 14;

const CIRCUITS = [
  {
    name: "pi_mix",
    file: "pi_mix.circom",
    input: {
      noteValue: 1000,
      noteRandomness: 123456789,
      pathElements: [11, 13, 17, 19, 23, 29, 31, 37],
      pathIndices: [0, 1, 0, 1, 1, 0, 0, 1],
    },
  },
  {
    name: "pi_N_i",
    file: "pi_N_i.circom",
    input: {
      valueIn: 1000,
      valueStake: 700,
      valueChange: 300,
      inputRandomness: 99887766,
      stakeRandomness: 11223344,
      changeRandomness: 55667788,
      index: 42,
      epoch: 20260606,
    },
  },
  {
    name: "pi_l",
    file: "pi_l.circom",
    input: {
      stakeValue: 700,
      stakeRandomness: 11223344,
      taskId: 31415926,
      electionSalt: 27182818,
      workloadWeight: 987654,
      snapshotDigest: 42424242,
    },
  },
];

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function removeDir(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

function executable(name) {
  const localBin = path.join(ROOT, "node_modules", ".bin", name);
  if (fs.existsSync(localBin)) return localBin;
  return name;
}

function commandExists(command, args) {
  const result = spawnSync(command, args, {
    cwd: ROOT,
    encoding: "utf8",
    maxBuffer: 1024 * 1024,
  });
  return result.error ? false : result.status === 0;
}

function snarkjsVersion() {
  const pkg = path.join(ROOT, "node_modules", "snarkjs", "package.json");
  if (fs.existsSync(pkg)) {
    return `snarkjs@${JSON.parse(fs.readFileSync(pkg, "utf8")).version}`;
  }
  const result = spawnSync(executable("snarkjs"), [], { encoding: "utf8" });
  return (result.stdout || result.stderr || "snarkjs version unavailable").split(/\r?\n/)[0];
}

function run(command, args, options = {}) {
  const start = performance.now();
  const result = spawnSync(command, args, {
    cwd: options.cwd || ROOT,
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 64,
  });
  const elapsed = (performance.now() - start) / 1000;
  if (result.status !== 0) {
    const rendered = [command, ...args].join(" ");
    throw new Error(
      `Command failed (${rendered})\nSTDOUT:\n${result.stdout}\nSTDERR:\n${result.stderr}`
    );
  }
  return { elapsed, stdout: result.stdout || "", stderr: result.stderr || "" };
}

function timed(label, command, args, options = {}) {
  console.log(`[${label}] ${[command, ...args].join(" ")}`);
  return run(command, args, options).elapsed;
}

function writeJson(file, value) {
  ensureDir(path.dirname(file));
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + "\n");
}

function writeCsv(file, rows) {
  const headers = Object.keys(rows[0]);
  const escape = (value) => {
    const s = String(value);
    if (s.includes(",") || s.includes("\n") || s.includes('"')) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };
  const lines = [headers.join(",")];
  for (const row of rows) lines.push(headers.map((h) => escape(row[h])).join(","));
  fs.writeFileSync(file, lines.join("\n") + "\n");
}

function parseR1csInfo(output) {
  const info = {};
  for (const line of output.split(/\r?\n/)) {
    const cleaned = line
      .replace(/\x1b\[[0-9;]*m/g, "")
      .replace(/^\s*\[INFO\]\s+snarkJS:\s*/, "")
      .trim();
    const m = cleaned.match(/^\s*([^:]+):\s*(.+?)\s*$/);
    if (!m) continue;
    const key = m[1]
      .trim()
      .toLowerCase()
      .replace(/^#\s*of\s+/, "")
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
    info[key] = m[2].trim();
  }
  return info;
}

function preparePtau(snarkjs, clean) {
  const ptauDir = path.join(BUILD_DIR, "ptau");
  ensureDir(ptauDir);
  const prepared = path.join(ptauDir, `powersOfTau28_hez_final_${PTAU_POWER}.ptau`);
  if (!clean && fs.existsSync(prepared)) return { file: prepared, seconds: 0 };

  const pot0 = path.join(ptauDir, "pot_0000.ptau");
  const pot1 = path.join(ptauDir, "pot_0001.ptau");

  let seconds = 0;
  seconds += timed("ptau:new", snarkjs, [
    "powersoftau",
    "new",
    "bn128",
    String(PTAU_POWER),
    pot0,
    "-v",
  ]);
  seconds += timed("ptau:contribute", snarkjs, [
    "powersoftau",
    "contribute",
    pot0,
    pot1,
    "--name=CleVer reproducible contribution",
    "-v",
    "-e=clever-table7-ptau",
  ]);
  seconds += timed("ptau:prepare", snarkjs, [
    "powersoftau",
    "prepare",
    "phase2",
    pot1,
    prepared,
    "-v",
  ]);

  return { file: prepared, seconds };
}

function benchmarkCircuit(circuit, ptauFile, circom, snarkjs) {
  const circuitName = circuit.name;
  const workDir = path.join(BUILD_DIR, circuitName);
  ensureDir(workDir);

  const inputFile = path.join(workDir, "input.json");
  writeJson(inputFile, circuit.input);

  const circuitPath = path.join(CIRCUIT_DIR, circuit.file);
  const compileSeconds = timed(`compile:${circuitName}`, circom, [
    circuitPath,
    "--r1cs",
    "--wasm",
    "--sym",
    "-o",
    workDir,
  ]);

  const stem = path.basename(circuit.file, ".circom");
  const r1cs = path.join(workDir, `${stem}.r1cs`);
  const wasm = path.join(workDir, `${stem}_js`, `${stem}.wasm`);
  const witness = path.join(workDir, "witness.wtns");
  const zkey0 = path.join(workDir, `${circuitName}_0000.zkey`);
  const zkey = path.join(workDir, `${circuitName}_final.zkey`);
  const vkey = path.join(workDir, "verification_key.json");
  const proof = path.join(workDir, "proof.json");
  const publicSignals = path.join(workDir, "public.json");

  const r1csInfoResult = run(snarkjs, ["r1cs", "info", r1cs]);
  const r1csInfoOutput = `${r1csInfoResult.stdout}\n${r1csInfoResult.stderr}`;
  const r1csInfo = parseR1csInfo(r1csInfoOutput);

  let setupSeconds = 0;
  setupSeconds += timed(`setup:${circuitName}`, snarkjs, [
    "groth16",
    "setup",
    r1cs,
    ptauFile,
    zkey0,
  ]);
  setupSeconds += timed(`zkey:${circuitName}`, snarkjs, [
    "zkey",
    "contribute",
    zkey0,
    zkey,
    "--name=CleVer circuit contribution",
    "-v",
    "-e=clever-table7-zkey",
  ]);
  timed(`vkey:${circuitName}`, snarkjs, [
    "zkey",
    "export",
    "verificationkey",
    zkey,
    vkey,
  ]);

  const witnessSeconds = timed(`witness:${circuitName}`, snarkjs, [
    "wtns",
    "calculate",
    wasm,
    inputFile,
    witness,
  ]);

  const proofSeconds = timed(`prove:${circuitName}`, snarkjs, [
    "groth16",
    "prove",
    zkey,
    witness,
    proof,
    publicSignals,
  ]);

  const verifySeconds = timed(`verify:${circuitName}`, snarkjs, [
    "groth16",
    "verify",
    vkey,
    publicSignals,
    proof,
  ]);

  return {
    circuit: circuitName,
    compile_seconds: compileSeconds.toFixed(6),
    setup_seconds: setupSeconds.toFixed(6),
    witness_seconds: witnessSeconds.toFixed(6),
    proof_gen_seconds: proofSeconds.toFixed(6),
    verify_seconds: verifySeconds.toFixed(6),
    wires: r1csInfo.wires || "",
    constraints: r1csInfo.constraints || "",
    private_inputs: r1csInfo.private_inputs || "",
    public_outputs: r1csInfo.public_outputs || "",
    source: "measured_circom_snarkjs_groth16_bn254",
  };
}

function main() {
  const args = new Set(process.argv.slice(2));
  const clean = args.has("--clean");
  const skipPtau = args.has("--skip-ptau-time");

  if (clean) removeDir(BUILD_DIR);
  ensureDir(OUT_DIR);
  ensureDir(BUILD_DIR);

  const circom = executable("circom");
  const snarkjs = executable("snarkjs");
  const missing = [];
  if (!commandExists(circom, ["--version"])) missing.push("circom");
  if (!fs.existsSync(snarkjs) && !commandExists(snarkjs, [])) missing.push("snarkjs");
  if (missing.length) {
    throw new Error(
      `Missing required executable(s): ${missing.join(", ")}. Run npm install to install snarkjs.`
    );
  }

  const ptau = preparePtau(snarkjs, clean);
  const rows = CIRCUITS.map((circuit) => benchmarkCircuit(circuit, ptau.file, circom, snarkjs));
  for (const row of rows) {
    row.ptau_seconds = skipPtau ? "0.000000" : ptau.seconds.toFixed(6);
  }

  writeCsv(path.join(OUT_DIR, "table7_zkbench_measured.csv"), rows);
  writeJson(path.join(OUT_DIR, "table7_zkbench_measured.json"), {
    generated_at: new Date().toISOString(),
    toolchain: {
      circom: run(circom, ["--version"]).stdout.trim(),
      snarkjs: snarkjsVersion(),
      node: process.version,
      ptau_power: PTAU_POWER,
    },
    rows,
  });
  console.log(`Wrote measured Table 7 benchmark outputs to ${OUT_DIR}`);
}

if (require.main === module) {
  main();
}
