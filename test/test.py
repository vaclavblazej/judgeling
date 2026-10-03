#!/usr/bin/env python3
import os
import subprocess
import sys
import unittest

sys.path.append(os.path.abspath("../src"))
import judgeling

script = "../src/judgeling.py"


def run(args=[], input_file=None, output_file=None, error_file=None, timeout=None):
    in_file = None
    if input_file:
        in_file = open(input_file)
    else:
        in_file = subprocess.DEVNULL
    out_file = None
    if output_file:
        out_file = open(output_file, "w")
    else:
        out_file = subprocess.DEVNULL
    err_file = None
    if error_file:
        err_file = open(error_file, "w")
    else:
        err_file = subprocess.DEVNULL
    p = subprocess.Popen([script] + args, stdin=in_file, stdout=out_file, stderr=err_file)
    p.wait()
    if out_file and out_file != subprocess.DEVNULL:
        out_file.flush()
    if err_file and err_file != subprocess.DEVNULL:
        err_file.flush()
    return p.returncode


def run_capturing_stderr(args=None):
    """Like run(), but also returns the combined stderr (where judgeling's log messages go)."""
    p = subprocess.run(
        [script] + (args or []),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return p.returncode, p.stderr


class TestCall(unittest.TestCase):
    # == return codes ================================================================

    def test_return_codes_are_zero_no_param(self):
        self.assertEqual(run(), judgeling.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_verbose(self):
        self.assertEqual(run(["-v"]), judgeling.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_debug(self):
        self.assertEqual(run(["-d"]), judgeling.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_quiet(self):
        self.assertEqual(run(["-q"]), judgeling.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_help(self):
        self.assertEqual(run(["-h"]), judgeling.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_version(self):
        self.assertEqual(run(["--version"]), judgeling.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_correct_problem(self):
        self.assertEqual(run(["-P", "example"]), judgeling.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_correct_problem_with_solution(self):
        self.assertEqual(
            run(["-P", "example", "-S", "example/sol/ref_library_sort.cpp", "-q"]),
            judgeling.SUCCESSFULL_EXECUTION,
        )

    def test_return_codes_are_zero_with_testcase_filter(self):
        # narrows the run down to a single testcase, exercising the -T regex path
        self.assertEqual(
            run(
                [
                    "-P",
                    "example",
                    "-S",
                    "example/sol/ref_library_sort.cpp",
                    "-T",
                    "001",
                    "-q",
                ]
            ),
            judgeling.SUCCESSFULL_EXECUTION,
        )

    def test_dataset_regex_filters_generators(self):
        # exercises the -D regex path; test/example has two generators ("small" and
        # "tiny"), so filtering to "tiny" must run that dataset and skip the other
        return_code, stderr = run_capturing_stderr(
            [
                "-P",
                "example",
                "-S",
                "example/sol/ref_library_sort.cpp",
                "-D",
                "tiny",
            ]
        )
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        self.assertIn("Dataset tiny", stderr)
        self.assertNotIn("Dataset small", stderr)

    def test_return_codes_are_zero_manual_input(self):
        # exercises the --input path, which bypasses generators entirely
        self.assertEqual(
            run(
                [
                    "-P",
                    "example",
                    "-S",
                    "example/sol/ref_library_sort.cpp",
                    "--input",
                    "fixtures/manual_input.in",
                    "-q",
                ]
            ),
            judgeling.SUCCESSFULL_EXECUTION,
        )

    def test_java_solution_is_compiled_and_run(self):
        # exercises the compiled-language "run"/"artifact" template path (javac + java -cp)
        return_code, stderr = run_capturing_stderr(["-P", "example", "-S", "fixtures/CorrectSolution.java", "-v"])
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        self.assertNotIn("WA", stderr)

    def test_second_run_skips_compilation_due_to_cache(self):
        # first run populates the source-hash cache
        self.assertEqual(
            run(["-P", "example", "-S", "example/sol/ref_library_sort.cpp", "-q"]),
            judgeling.SUCCESSFULL_EXECUTION,
        )
        return_code, stderr = run_capturing_stderr(["-P", "example", "-S", "example/sol/ref_library_sort.cpp", "-v"])
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        self.assertIn("Skipped compilation", stderr)

    def test_bad_argument_return_code_bad_argument(self):
        self.assertEqual(run(["-bad_arg"]), judgeling.INVALID_ARGUMENT)

    def test_bad_argument_return_code_incorrect_problem(self):
        self.assertEqual(run(["-P", "non_existant"]), judgeling.USER_ERROR)

    def test_bad_argument_return_code_nonexistent_solution_file(self):
        self.assertEqual(
            run(["-P", "example", "-S", "example/sol/does_not_exist.cpp"]),
            judgeling.USER_ERROR,
        )

    def test_problem_error_when_no_checking_mechanism(self):
        # a problem with no generator/judge/checker/referential solution can't be checked at all
        self.assertEqual(
            run(
                [
                    "-P",
                    "fixtures/no_checker_problem",
                    "-S",
                    "fixtures/wrong_solution.cpp",
                    "-q",
                ]
            ),
            judgeling.PROBLEM_ERROR,
        )

    def test_bad_invocation_from_broken_checker_is_problem_error(self):
        # a checker that always signals bad invocation (return code 43) must not be
        # mistaken for a valid WA/PE/RE/TLE result
        self.assertEqual(
            run(
                [
                    "-P",
                    "fixtures/broken_checker_problem",
                    "-S",
                    "example/sol/ref_library_sort.cpp",
                    "-q",
                ]
            ),
            judgeling.PROBLEM_ERROR,
        )

    def test_generator_failure_is_problem_error(self):
        # a generator that exits nonzero must not be treated as producing an empty dataset
        self.assertEqual(
            run(
                [
                    "-P",
                    "fixtures/broken_generator_problem",
                    "-S",
                    "fixtures/wrong_solution.cpp",
                    "-q",
                ]
            ),
            judgeling.PROBLEM_ERROR,
        )

    def test_invalid_manual_input_is_rejected_by_validator(self):
        # exercises validate_testcases()'s failure path via test/example's val.cpp
        # --input copies its file into example's shared .tmp/data/_manual folder and never
        # removes it, so clean up afterwards to avoid polluting other manual-input tests
        try:
            self.assertEqual(
                run(
                    [
                        "-P",
                        "example",
                        "-S",
                        "example/sol/ref_library_sort.cpp",
                        "--input",
                        "fixtures/invalid_manual_input.in",
                        "-q",
                    ]
                ),
                judgeling.USER_ERROR,
            )
        finally:
            copied_file = "example/.tmp/data/_manual/invalid_manual_input.in"
            if os.path.exists(copied_file):
                os.remove(copied_file)

    # == correctness detection =======================================================

    def test_wrong_solution_is_reported_as_wrong_answer(self):
        return_code, stderr = run_capturing_stderr(["-P", "example", "-S", "fixtures/wrong_solution.cpp"])
        # judgeling's exit code does not reflect per-testcase results (see summary), only the
        # run's own completion, so a wrong solution still exits successfully...
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        # ...but the checker must have actually caught the wrong answer along the way.
        self.assertIn("WA", stderr)

    def test_runtime_error_is_reported(self):
        return_code, stderr = run_capturing_stderr(["-P", "example", "-S", "fixtures/re_solution.cpp"])
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        self.assertIn("RE", stderr)

    def test_timelimit_exceeded_is_reported(self):
        # fixtures/judge_only_problem overrides time_limit_seconds down to 3s so this
        # test doesn't have to wait out test/example's default 30s
        return_code, stderr = run_capturing_stderr(["-P", "fixtures/judge_only_problem", "-S", "fixtures/tle_solution.cpp"])
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        self.assertIn("TLE", stderr)

    # == checking mechanisms ==========================================================

    def test_judge_mechanism_accepts_correct_solution(self):
        # fixtures/judge_only_problem has a judge but no checker/referential solution,
        # so determine_checking_mechanism() must resolve to Mechanism.judge
        return_code, stderr = run_capturing_stderr(
            [
                "-P",
                "fixtures/judge_only_problem",
                "-S",
                "example/sol/ref_library_sort.cpp",
            ]
        )
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        self.assertNotIn("WA", stderr)

    def test_judge_mechanism_flags_wrong_solution(self):
        return_code, stderr = run_capturing_stderr(["-P", "fixtures/judge_only_problem", "-S", "fixtures/wrong_solution.cpp"])
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        self.assertIn("WA", stderr)

    def test_cross_check_mechanism_flags_wrong_solution(self):
        # fixtures/cross_check_problem has a checker but no referential solution, so with
        # two -S solutions determine_checking_mechanism() must resolve to cross_check;
        # the correct solution must be listed first, since main() picks the first -S
        # solution as the ad-hoc reference
        return_code, stderr = run_capturing_stderr(
            [
                "-P",
                "fixtures/cross_check_problem",
                "-S",
                "example/sol/ref_library_sort.cpp",
                "fixtures/wrong_solution.cpp",
            ]
        )
        self.assertEqual(return_code, judgeling.SUCCESSFULL_EXECUTION)
        self.assertIn("Picked solution", stderr)
        self.assertIn("WA", stderr)

    # == return codes ================================================================


if __name__ == "__main__":
    unittest.main()
