# Tools to manage algorithm definitions, problem definitions, and their solutions

## Setup

First, download this repository by running.
```
$ git clone https://gitlab.fit.cvut.cz/acm/acm-algo.git
```

Now, you can add a symbolic link to `./algo.sh` to your path, e.g. `~/bin`, so that you can run this script from any location.
```
$ ln -s "$PWD/acm-algo/algo.py" ~/bin/algo
```

Also, to be able to use common problem definitions, download the problem repository.
```
$ git clone https://gitlab.fit.cvut.cz/acm/acm-problems.git
```

## Basic usage

To test your code run:
```
$ algo -P PROBLEM_ID -S [SOLUTION.cpp ...]
```
The `PROBLEM_ID` either represents path to local problem definition, or a problem name from `acm-problems` repository (e.g. *sort*).

The script will compile your code and run it against respective datasets.

```
$ algo -P sort -S default_library_sort.cpp radix_sort.cpp
Generating .................................................. done
2019-11-02 19:38:36,070 - INFO - Testing validity of testcases
2019-11-02 19:38:36,430 - INFO - All testcases were validated successfully
2019-11-02 19:38:36,430 - INFO - Running datasets on solutions
2019-11-02 19:38:36,431 - INFO - Dataset small
2019-11-02 19:38:36,431 - INFO - Testcase: 001
2019-11-02 19:38:36,488 - INFO - Testcase: 002
2019-11-02 19:38:36,548 - INFO - Testcase: 003
2019-11-02 19:38:36,607 - INFO - Testcase: 004
2019-11-02 19:38:36,666 - INFO - Testcase: 005
2019-11-02 19:38:36,728 - INFO - Testcase: 006
2019-11-02 19:38:36,788 - INFO - Testcase: 007
2019-11-02 19:38:36,847 - INFO - Testcase: 008
2019-11-02 19:38:36,431 - INFO - Dataset big
2019-11-02 19:38:36,431 - INFO - Testcase: 001
2019-11-02 19:38:36,488 - INFO - Testcase: 002
2019-11-02 19:38:36,548 - INFO - Testcase: 003
2019-11-02 19:38:37,655 - INFO - Summary
2019-11-02 19:38:37,656 - INFO - default_library_sort (0.507s): OK
2019-11-02 19:38:37,656 - INFO - radix_sort (0.553s): OK
```

You will see which of the testcases were failed and possibly some additional information from the checker/judge to help with debugging.
To test against specific datasets or testcases using dataset regex `-D` and testcase regex `-T` arguments.

```
$ algo -P sort -S default_library_sort.cpp radix_sort.cpp -T 007
Generating .................................................. done
2019-11-02 19:42:55,168 - INFO - Testing validity of testcases
2019-11-02 19:42:55,170 - INFO - All testcases were validated successfully
2019-11-02 19:42:55,170 - INFO - Running datasets on solutions
2019-11-02 19:42:55,170 - INFO - Dataset small
2019-11-02 19:42:55,170 - INFO - Testcase: 007
2019-11-02 19:42:55,178 - INFO - Summary
2019-11-02 19:42:55,178 - INFO - default_library_sort (0.001s): OK
2019-11-02 19:42:55,178 - INFO - radix_sort (0.002s): OK
```

Note that all additional files (datasets, compilation results) are stored in `<problem directory>/.tmp` folder.
Delete it if you think some old files there cause weird issues.

## Advanced usage

### Testing variants

You may test your program in several various ways depending on how much you entangle your solution to the problem.

1. Basic level - load input, solve, print output; measures: total speed
2. (to be implemented) Measurement tools - you make few additional calls to the algo library; measures: speed of various algorithm parts, algorithm code complexity.

#### Changing solution to allow more precise measurements (to be implemented)

Keep your code compilable with standard commands using `#ifdef ALGME`

### Problem definition structure
The folder/file structure in problems folder represents the primary categorization of each problem. The problem definition with its input/output definition to solve it

* problem - contains the problem statement and input/output definitions
* validator - checks whether the input is correct (mainly for custom made input)
* painter - gets input and should create the picture
* corectness check
    * checker - compares your solution with the referential solution (requires solution)
    * judge - is given your solution and input and decides if it is correct, generally faster to run
* generator - creates testing datasets and their testcases, dataset name corresponds to the generator name
* solution - referential solution which is assumed to be correct

```
<problem_name>
    def.toml
    gen
        <generator 1>.cpp
        <generator 2>.cpp
    val
        <validator 1>.cpp
        <validator 2>.cpp
    jud.cpp (judge, which compares input and user's output)
    chk.cpp (checker, compares referential and user's output)
    sol.cpp (referential solution)
```

Each part can be either a cpp/py/sh file directly, or a directory containing several of such files.

#### Solution
```
my_sol time_result_file < testcase_input > solution_testcase_output
```

#### Generator (gen)
```
gen random_generator_seed dataset_folder
```

#### Validator (val)
```
val < testcase_input
```

#### Judge (jud)
```
jud testcase_input solution_testcase_output
```

#### Checker (chk)
```
chk testcase_correct_output solution_testcase_output
```

#### Referential solution (sol)
```
sol < testcase_input > referential_testcase_output
```

#### Painter (pic)
```
pic testcase_drawing testcase_input testcase_correct_output
```

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


## Browser (work in progress)

This set is bundled with web browser for this repository.
It works by running a backend (python3 django) server which manages files in this repository and provides API to change them.
The frontend (react) then hooks into this api, and displays the result.

Setup by installing *python3* and *python's django* package.

```bash
apt install python3 python3-pip
pip3 install django
```

Start it with the following command, which will give you further instructions.

```bash
todo ...
```

