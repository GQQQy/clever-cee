pragma circom 2.1.8;

include "common.circom";

template PiMix() {
    signal input noteValue;
    signal input noteRandomness;
    signal input pathElements[8];
    signal input pathIndices[8];

    signal output root;
    signal output commitment;

    component idxBits[8];
    component commit = Commitment2();
    component work = QuadraticChain(500);

    commit.left <== noteValue;
    commit.right <== noteRandomness;
    commitment <== commit.out;

    signal state[9];
    signal left[8];
    signal right[8];
    signal leftDelta[8];
    signal rightDelta[8];
    state[0] <== commitment;

    for (var i = 0; i < 8; i++) {
        idxBits[i] = Bool();
        idxBits[i].in <== pathIndices[i];

        leftDelta[i] <== pathIndices[i] * (pathElements[i] - state[i]);
        rightDelta[i] <== pathIndices[i] * (state[i] - pathElements[i]);
        left[i] <== state[i] + leftDelta[i];
        right[i] <== pathElements[i] + rightDelta[i];
        state[i + 1] <== left[i] * left[i] + 3 * right[i] + i + 11;
    }

    work.in <== state[8] + commitment;
    root <== work.out;
}

component main = PiMix();
