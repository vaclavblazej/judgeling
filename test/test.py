#!/usr/bin/env python3
import unittest, subprocess
import importlib, sys, os

sys.path.append(os.path.abspath('..'))
import algo

script = '../algo.py'

def run(args=[], input_file=None, output_file=None, error_file=None, timeout=None):
    in_file = None
    if input_file: in_file = open(input_file)
    else: in_file = subprocess.DEVNULL
    out_file = None
    if output_file: out_file = open(output_file, 'w')
    else: out_file = subprocess.DEVNULL
    err_file = None
    if error_file: err_file = open(error_file, 'w')
    else: err_file = subprocess.DEVNULL
    p = subprocess.Popen([script] + args, stdin=in_file, stdout=out_file, stderr=err_file)
    p.wait()
    if out_file and out_file != subprocess.DEVNULL: out_file.flush()
    if err_file and err_file != subprocess.DEVNULL: err_file.flush()
    return p.returncode


class TestCall(unittest.TestCase):

    def test_return_codes_are_zero_no_param(self):
        self.assertEqual(run(), algo.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_verbose(self):
        self.assertEqual(run(['-v']), algo.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_debug(self):
        self.assertEqual(run(['-d']), algo.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_quiet(self):
        self.assertEqual(run(['-q']), algo.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_version(self):
        self.assertEqual(run(['--version']), algo.SUCCESSFULL_EXECUTION)

    def test_return_codes_are_zero_correct_problem(self):
        self.assertEqual(run(['-P', 'example']), algo.SUCCESSFULL_EXECUTION)

    def test_bad_argument_return_code_bad_argument(self):
        self.assertEqual(run(['-bad_arg']), algo.INVALID_ARGUMENT)

    def test_bad_argument_return_code_incorrect_problem(self):
        self.assertEqual(run(['-P', 'non_existant']), algo.USER_ERROR)

if __name__ == '__main__':
    unittest.main()

