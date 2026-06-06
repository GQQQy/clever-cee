// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../src/CleVerGasBenchmark.sol";

contract CleVerGasBenchmarkTest {
    event GasSample(string component, uint256 verifiers, uint256 gasUsed);

    function testGasBenchmark() public {
        uint256[16] memory counts = [
            uint256(50),
            uint256(60),
            uint256(70),
            uint256(80),
            uint256(90),
            uint256(100),
            uint256(110),
            uint256(120),
            uint256(130),
            uint256(140),
            uint256(150),
            uint256(160),
            uint256(170),
            uint256(180),
            uint256(190),
            uint256(200)
        ];

        for (uint256 i = 0; i < counts.length; i++) {
            _measure("zk_proof_verification", counts[i], 0);
            _measure("storage_append", counts[i], 1);
            _measure("ec_operations", counts[i], 2);
            _measure("mapping_lookup", counts[i], 3);
            _measure("control_logic", counts[i], 4);
        }
    }

    function _measure(string memory component, uint256 verifiers, uint256 mode) internal {
        CleVerGasBenchmark bench = new CleVerGasBenchmark();
        uint256 startGas = gasleft();

        if (mode == 0) {
            bench.zkProofVerification(verifiers);
        } else if (mode == 1) {
            bench.storageAppend(verifiers);
        } else if (mode == 2) {
            bench.ecOperations(verifiers);
        } else if (mode == 3) {
            bench.storageAppend(verifiers);
            bench.mappingLookup(verifiers);
        } else {
            bench.controlLogic(verifiers);
        }

        uint256 gasUsed = startGas - gasleft();
        emit GasSample(component, verifiers, gasUsed);
    }
}
