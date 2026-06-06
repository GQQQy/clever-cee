// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../../../experiment_results/evm/generated/PiMixProofData.sol";
import "../../../experiment_results/evm/generated/PiMixVerifier.sol";

contract CleVerGasBenchmark {
    Groth16Verifier internal verifier;
    mapping(bytes32 => bool) internal nullifiers;
    bytes32[] internal verifierRecords;

    constructor() {
        verifier = new Groth16Verifier();
    }

    function zkProofVerification(uint256 verifiers) external returns (uint256 accepted) {
        uint256[2] memory pA = PiMixProofData.pA();
        uint256[2][2] memory pB = PiMixProofData.pB();
        uint256[2] memory pC = PiMixProofData.pC();
        uint256[2] memory pubSignals = PiMixProofData.pubSignals();

        for (uint256 i = 0; i < verifiers; i++) {
            if (verifier.verifyProof(pA, pB, pC, pubSignals)) {
                accepted++;
            }
        }
    }

    function storageAppend(uint256 verifiers) external {
        for (uint256 i = 0; i < verifiers; i++) {
            bytes32 record = keccak256(abi.encodePacked(address(this), i, block.number));
            verifierRecords.push(record);
            nullifiers[record] = true;
        }
    }

    function ecOperations(uint256 verifiers) external view returns (uint256 accumulator) {
        uint256[3] memory input;
        uint256[2] memory output;
        input[0] = 1;
        input[1] = 2;

        for (uint256 i = 0; i < verifiers; i++) {
            input[2] = i + 1;
            bool success;
            assembly {
                success := staticcall(gas(), 7, input, 0x60, output, 0x40)
            }
            require(success, "ecmul failed");
            accumulator ^= output[0] ^ output[1];
        }
    }

    function mappingLookup(uint256 verifiers) external view returns (uint256 hits) {
        for (uint256 i = 0; i < verifiers; i++) {
            bytes32 key = keccak256(abi.encodePacked(address(this), i, block.number));
            if (nullifiers[key]) {
                hits++;
            }
        }
    }

    function controlLogic(uint256 verifiers) external pure returns (uint256 accumulator) {
        for (uint256 i = 0; i < verifiers; i++) {
            uint256 score = uint256(keccak256(abi.encodePacked(i, accumulator)));
            if (score & 1 == 0) {
                accumulator += score % 997;
            } else {
                accumulator ^= score % 991;
            }
        }
    }
}
