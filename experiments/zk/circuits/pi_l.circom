pragma circom 2.1.8;

include "common.circom";

template PiLinkability() {
    signal input stakeValue;
    signal input stakeRandomness;
    signal input taskId;
    signal input electionSalt;
    signal input workloadWeight;
    signal input snapshotDigest;

    signal output verifierTag;
    signal output workloadTag;

    component stakeCommit = Commitment2();
    component verifierWork = QuadraticChain(250);
    component workloadWork = QuadraticChain(120);

    stakeCommit.left <== stakeValue;
    stakeCommit.right <== stakeRandomness;

    verifierWork.in <== stakeCommit.out + taskId + electionSalt;
    workloadWork.in <== workloadWeight + snapshotDigest + taskId;

    verifierTag <== verifierWork.out;
    workloadTag <== workloadWork.out;
}

component main = PiLinkability();
