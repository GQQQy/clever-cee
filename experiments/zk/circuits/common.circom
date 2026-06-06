pragma circom 2.1.8;

template Bool() {
    signal input in;
    in * (in - 1) === 0;
}

template QuadraticChain(n) {
    signal input in;
    signal output out;
    signal x[n + 1];

    x[0] <== in + 1;
    for (var i = 0; i < n; i++) {
        x[i + 1] <== x[i] * x[i] + i + 3;
    }
    out <== x[n];
}

template Commitment2() {
    signal input left;
    signal input right;
    signal output out;
    signal leftSq;
    signal rightSq;

    leftSq <== left * left;
    rightSq <== right * right;
    out <== leftSq + rightSq + 17 * left + 31 * right + 7;
}
