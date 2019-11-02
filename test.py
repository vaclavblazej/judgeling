#!/usr/bin/env python3
import unittest, subprocess


def run(args=[], input_file=None, output_file=None, timeout=None):
    in_file = None
    if input_file: in_file = open(input_file)
    out_file = None
    if output_file: out_file = open(output_file, 'w')
    p = subprocess.Popen([self.exe] + args, stdin=in_file, stdout=out_file)
    p.wait()
    if out_file: out_file.flush()
    return p.returncode


class TestCall(unittest.TestCase):

    def test_sum(self):
        self.assertEqual(sum([1, 2, 3]), 6, "Should be 6")

    def test_sum_tuple(self):
        self.assertEqual(sum((1, 2, 2)), 6, "Should be 6")


if __name__ == '__main__':
    unittest.main()

