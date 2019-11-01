# Tools to manage algorithm definitions, problem definitions, and their solutions

## Setup

First, download this repository by running
```
git clone https://gitlab.fit.cvut.cz/acm/acm-algo.git
```

Now, you can add a symbolic link to `./algo.sh` to your path, e.g. `~/bin`, so that you can run this script from any location.
```
ln -s acm-algo/algo.py ~/bin/algo
```

## Basic usage

To test your code run:
```
algo -P PROBLEM_ID -S [SOLUTION.cpp ...]
```

<!--todo-->

The script will compile your code and run it against respective datasets.

```
Dataset: /basic
testcase: ./test0001.in is VALID
segment_tree: WRONG ANSWER
[0:0] [1:0] [2:2] [3:2] [4:2] [5:2] [6:2] [7:2] [8:2] [9:0] [10:0] [11:0] [12:0]
F/T:1 5
error sum 6 != 7
testcase: ./test0002.in is VALID
segment_tree: OK
testcase: ./test0003.in is VALID
segment_tree: OK
Dataset: /static
testcase: ./test1.in is VALID
segment_tree: OK

============== Summary ====================
segment_tree: Errors in ./test0001.in
```

You will see which of the testcases were failed and possibly some additional information from the checker/judge to help with debugging.
To test against them specifically use dataset regex `-D` and testcase regex `-C`.

```
algo -D basic -C 001 -P segment_tree -S segment_tree.cpp
```

## Advanced usage

### Testing variants

You may test your program in several various ways depending on how much you entangle your solution to the problem.

1. Basic level - simply load input, solve, print output; measures: total speed, total code complexity
2. (todo) Measurement tools - you make few additional calls to the algo library; measures: speed of various algorithm parts, algorithm code complexity.

#### Changing solution to allow more precise measurements

; keep your code compilable without these tools using `#ifdef ALGME`

### Problem definition structure
The folder/file structure in problems folder represents the primary categorization of each problem. The problem definition with its input/output definition to solve it

* problem - contains the problem statement and input/output definitions
* validator - checks whether the input is correct (mainly for custom made input)
* corectness check
    * checker - compares your solution with the referential solution (requires solution)
    * judge - is given your solution and input and decides if it is correct
* generator - creates testing datasets and their testcases
* solution - referential solution which is assumed to be correct

```
<problem_name>
    def.toml
    gen
    val
    jud
    chk
    sol
```

Each part can be either a cpp file directly, or a directory containing several cpp files.

### Problem temporary files

All files are compiled into a temporary folder `.tmp` in the `<problem_name>` folder.
The structure is as follows.

```
<problem_name>
    .tmp
        build
            <executable of gengenerator 1>
            <executable of gengenerator 2>
            <executable of validator>
            <executable of solution 1>
            <executable of solution 2>
            ...
        data
            sol
                <solution name 1>
                    <output for testcase 1>
                    <output for testcase 2>
                    ...
                <solution name 2>
                    <output for testcase 1>
                    <output for testcase 2>
                    ...
                ...
            <dataset 1>
                <testcase 1>
                <testcase 2>
                <testcase 3>
                ...
            <dataset 2>
            ...
    gen
    ...
```

