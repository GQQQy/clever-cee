pragma circom 2.1.8;

include "common.circom";

template PiNi() {
    signal input valueIn;
    signal input valueStake;
    signal input valueChange;
    signal input inputRandomness;
    signal input stakeRandomness;
    signal input changeRandomness;
    signal input index;
    signal input epoch;

    signal output nullifier;
    signal output stakeCommitment;
    signal output changeCommitment;

    valueIn === valueStake + valueChange;

    component inCommit = Commitment2();
    component stakeCommit = Commitment2();
    component changeCommit = Commitment2();
    component work = QuadraticChain(12000);

    inCommit.left <== valueIn;
    inCommit.right <== inputRandomness;
    stakeCommit.left <== valueStake;
    stakeCommit.right <== stakeRandomness;
    changeCommit.left <== valueChange;
    changeCommit.right <== changeRandomness;

    work.in <== inCommit.out + stakeCommit.out + changeCommit.out + index + epoch;

    nullifier <== work.out + index * index + epoch;
    stakeCommitment <== stakeCommit.out;
    changeCommitment <== changeCommit.out;
}

component main = PiNi();
