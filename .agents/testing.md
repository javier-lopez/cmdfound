# Testing

    ./build && cd tests && sh tools.sh          # the whole block, ~70-80 s
    sh tools.sh -l cmdfound                     # its sections
    TESTS_UPTO=hook sh tools.sh cmdfound        # stop at the end of a section

`tools.db` holds one block, `@begin{cmdfound}` ... `@end`. It is one script: every
line gets `|| exit 1`, and later lines use what earlier ones built, so add tests
where their fixtures exist. `#@section{name}` lines mark where a run may stop.

- `cmdfound` in a test is the built script at the repo root, so build before
  running: a test fails when it is not what ./build makes from the tree; `../../cmdfound.d`
  is the real channels and `$(cd .. && pwd)/cmdfound.d` the fakes.
- The block runs under `sh -x` with `PS4=">>"`. A `$(...)` inside a command whose
  stderr a test captures with `2>&1` leaks its trace into the capture: compute
  values into variables first.
- Nothing may touch the real home or the network: every test sets `CMDFOUND_HOME`,
  and downloads go to the fake web server in the fakes. The block ends checking
  that `~` is unchanged.
- A test is proven by watching it fail on the old code first.
- Every change that adds tests reports three numbers: the suite's time before,
  after, and the new test's own cost. The owner decides whether it earns its keep.
