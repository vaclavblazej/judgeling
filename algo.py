#!/usr/bin/env python3
# Keep this program in a single file with at most 1000 lines for the sake of simplicity.

# This script provides a testing interface for solutions to problems which are defined in standard format.

import argparse
import enum
import glob
import hashlib
import itertools
import json
import logging
import os
import random
import re
import shlex
import shutil
import subprocess
import sys

# unix specific, for measuring time, see https://stackoverflow.com/questions/16701310/get-how-much-time-python-subprocess-spends/16701365
import resource

from os.path import join, dirname, realpath, basename, exists

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1 # argument format is fine, but content is wrong
PROBLEM_ERROR = 2 # content of problem definition is wrong
INVALID_ARGUMENT = 129 # argument format is wrong

VERBOSE_LEVEL = 15
QUIET_LEVEL = 60

class ArgumentParser(argparse.ArgumentParser): # bad argument exit code override
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(INVALID_ARGUMENT, '%s: error: %s\n' % (self.prog, message))

parser = ArgumentParser(
        description='Test algorithm implementations on problem definitions',
        epilog='Confront documentation of this script for examples and usage of various concepts.'
        )
parser.add_argument('--version', dest='version', action='store_true', help='prints out version information')
parser.add_argument('-P', '--problem', dest='problem_query', help='problem definition to be run')
parser.add_argument('-S', '--solution', dest='solution', nargs='+', help='user\'s files with his own solutions to the problem')
parser.add_argument('-D', '--dataset', dest='dataset_regex', help='filter used datasets using regex')
parser.add_argument('-T', '--testcase', dest='testcase_regex', help='filter used testcases using regex')
parser.add_argument('--seed', dest='seed', help='provide a rng seed for dataset generators')
parser.add_argument('--draw', dest='draw', action='store_true', help='creates drawings of testcases using pic program')
parser.add_argument('--input', dest='input', nargs='+', help='supplies input data files manually')
parser.add_argument('-g', '--force-gen', dest='force_generation', action='store_true', help='force the data generators to run again')
parser.add_argument('-q', '--quiet', dest='logging_level', const=QUIET_LEVEL, action='store_const', help='no output will be shown')
parser.add_argument('-v', '--verbose', dest='logging_level', const=VERBOSE_LEVEL, action='store_const', help='more detailed info about testing shown')
parser.add_argument('-d', '--debug', dest='logging_level', const=logging.DEBUG, action='store_const', help='very detailed messages of script\'s inner workings')

conf = { 'logging_level': logging.INFO, } # logging is set up before config loads
script_path = dirname(realpath(__file__))
working_directory = os.getcwd()
global_config_folder = join(script_path, 'config.json')
local_config_folder = join(script_path, 'config_local.json')
problem_search_location = realpath(join(script_path, '..', 'acm-problems/problems'))
version = '0.1.5'

# == Main Logic ==================================================================

def main():
    setup_logging()
    conf.update(load_configuration(global_config_folder))
    conf.update(load_configuration(local_config_folder))
    global args
    args = parser.parse_args()
    if args.logging_level: conf['logging_level'] = args.logging_level
    logger.setLevel(conf['logging_level'])
    logger.debug('Configuration: {}'.format(str(conf)))
    logger.debug('Script folder: {}'.format(uv(script_path)))
    logger.debug('Working directory: {}'.format(uv(working_directory)))
    logger.debug('Arguments: {}'.format(str(sys.argv)))

    if args.version:
        print('algo version ' + version)
        return SUCCESSFULL_EXECUTION

    problem_query = args.problem_query
    # default problem folder is the current working directory (default help command would have to be disabled)
    # if problem_query is None and exists(join(working_directory, conf['def_file'])):
    #     problem_query = working_directory
    if problem_query is None:
        logger.error('Problem ID was not supplied! Add -P <problem location/id> argument.')
        return SUCCESSFULL_EXECUTION

    problem_folder = find_problem_folder(problem_query)
    if not problem_folder:
        logger.error('Unable to locate the problem definition file for ' + uv(problem_query))
        return USER_ERROR
    problem_def_path = join(problem_folder, conf['def_file'])
    if not exists(problem_def_path):
        logger.warning('Problem found locally, but is missing a definition file: ' + uv(problem_folder))

    global data_path, build_path
    data_path = join(problem_folder, conf['problem_tmp_folder'], 'data')
    build_path = join(problem_folder, conf['problem_tmp_folder'], 'build')
    logger.debug('PROBLEM DIRECTORY: ' + problem_folder)
    logger.debug('DATA PATH: ' + data_path)
    logger.debug('BUILD PATH: ' + build_path)

    solutions = []
    if args.solution:
        for arg_sol in args.solution:
            solution_path = join(working_directory, arg_sol)
            if exists(solution_path):
                solutions.append(Solution(solution_path))
            else:
                logger.error('Supplied solution file does not exist: ' + uv(solution_path))
                return USER_ERROR

    if len(solutions) == 0:
        if exists(problem_def_path):
            logger.verbose('Problem information contained in: ' + problem_def_path)
            print_file_contents(problem_def_path)
        logger.info('To test your solution, add -S <solution_file> to the arguments.')
        return SUCCESSFULL_EXECUTION

    for solution in solutions:
        solution.compile()

    project_config_folder = join(problem_folder, '.algo_config.json')
    conf.update(load_configuration(project_config_folder))

    file_structure = conf['file_structure']
    generator_files = get_file_or_folder(problem_folder, file_structure['generator'])
    generators = None
    if generator_files: generators = [Generator(g.source_file) for g in generator_files]
    validators = get_file_or_folder(problem_folder, file_structure['validator'])
    painters = get_file_or_folder(problem_folder, file_structure['painter'])
    judges = get_file_or_folder(problem_folder, file_structure['judge'])
    raw_ref_solutions = get_file_or_folder(problem_folder, file_structure['solution'])
    if raw_ref_solutions:
        referential_solutions = [Solution(x.source_file) for x in raw_ref_solutions]
    else:
        referential_solutions = None
    # compares one solution against referential solution if it is correct
    checkers = get_file_or_folder(problem_folder, file_structure['checker'])

    logger.verbose('This problem has:')
    if generators: logger.verbose('Generators: ' + str(len(generators)))
    if validators: logger.verbose('Validators: ' + str(len(validators)))
    if painters: logger.verbose('Painters: ' + str(len(painters)))
    if judges: logger.verbose('Judges: ' + str(len(judges)))
    if referential_solutions: logger.verbose('Referential solutions: ' + str(len(referential_solutions)))
    if checkers: logger.verbose('Checkers: ' + str(len(checkers)))

    mechanism = determine_checking_mechanism(judges, checkers, referential_solutions, solutions)
    if not mechanism:
        logger.critical('There is no checking mechanism!')
        logger.critical('This is an issue with the problem definition, contact the author.')
        logger.critical('To fix this: create either a "judge" or "checker and referential solution"')
        return PROBLEM_ERROR
    logger.verbose('The checking mechanism is: ' + uv(mechanism.name))

    random.seed()
    global seed
    seed = 0
    if args.seed: seed = args.seed
    logger.verbose('Seed: ' + str(seed))

    manual_input_files = args.input
    if manual_input_files:
        logger.verbose('Following inputs were supplied: ' + uv(manual_input_files))
        manual_input_folder = join(data_path, conf['manual_testcases_folder_name'])
        os.makedirs(manual_input_folder, exist_ok=True)
        for manual_input_file in manual_input_files:
            if exists(manual_input_file):
                shutil.copy(manual_input_file, join(manual_input_folder, basename(manual_input_file)))
            else:
                logger.error('Supplied input file ' + uv(manual_input_file) + ' could not be found')
        datasets = [Dataset(manual_input_folder)]
    else:
        if not args.force_generation and args.dataset_regex:
            generators = [g for g in generators if re.search(args.dataset_regex, g.name)]
        for generator in generators:
            logger.debug('Generator output folder: ' + generator.data_folder)
            if generator.generate() != 0:
                logger.critical('Problem dataset generator ' + uv(generator.name) + ' has trouble running, contact the problem setter about this issue.')
                return PROBLEM_ERROR

        datasets = [Dataset(g.data_folder) for g in generators]
        if args.dataset_regex:
            datasets = [d for d in datasets if re.search(args.dataset_regex, d.name)]

    for dataset in datasets:
        dataset.get_testcases(args.testcase_regex)

    if not validate_testcases(validators, datasets):
        return USER_ERROR

    if mechanism == Mechanism.judge:
        if judges:
            for judge in judges:
                judge.compile()
    elif mechanism in [Mechanism.checker, Mechanism.cross_check]:
        if mechanism == Mechanism.cross_check:
            referential_solutions = solutions[:1]
            solutions = solutions[1:]
            logger.info('Picked solution ' + uv(referential_solutions[0].name) + ' as a referential solution')
        logger.info('Running referential solution to get referential outputs')
        for ref in referential_solutions: ref.compile()
        for checker in checkers: checker.compile()
        for dataset in datasets:
            logger.info('Dataset ' + dataset.name)
            for testcase in dataset.testcases:
                logger.info('Testcase: ' + uv(testcase.name))
                referential_solutions[0].run([], testcase.input, testcase.correct_output)
        solutions.extend(referential_solutions)
        logger.info('Referential outputs obtained succesfully')

    if painters:
        if args.draw:
            painter = painters[0]
            painter.compile()
            logger.info('Drawing testcases')
            paint_outfile=os.devnull
            if conf['logging_level'] <= VERBOSE_LEVEL: paint_outfile=None
            for testcase in list(itertools.chain(*[dataset.testcases for dataset in datasets])):
                logger.info('Drawing testcase ' + testcase.dataset.name + '/' + testcase.name)
                if painter.run([testcase.drawing, testcase.input, testcase.correct_output], None, paint_outfile) != 0:
                    logger.error('Unable to draw testcase ' + uv(testcase.input) + ', interrupting drawing.')
                    break;
        else:
            logger.info('Available painter, add --draw flag to allow painter to draw testcases (can take a long time).')

    logger.info('Running datasets on solutions')
    for dataset in datasets:
        logger.info('Dataset ' + dataset.name)
        for solution in solutions: solution.disqualified = False
        for testcase in dataset.testcases:
            viable_solutions = [s for s in solutions if not s.disqualified]
            if len(viable_solutions) == 0:
                logger.info('All solutions were disqualified, skipping rest of testcases for this dataset.')
                break
            logger.info('Testcase: ' + uv(testcase.name))
            for solution in viable_solutions:
                solution_out_dir = join(dataset.data_folder, 'sol', solution.name)
                os.makedirs(solution_out_dir, exist_ok=True)
                solution_testcase_out = join(solution_out_dir, testcase.name + conf['out_ext'])
                time_result_file = join(solution_out_dir, conf['statistics_file_name'])
                result = Result.DEFAULT_FLAG
                try:
                    solution.timer.start()
                    return_code = solution.run([time_result_file], testcase.input, solution_testcase_out, conf['time_limit_seconds'])
                    solution.timer.stop()
                    if return_code != 0:
                        logger.info('The program returned ' + uv(return_code) + ' (should return 0), and output >>>')
                        print_file_contents(solution_testcase_out)
                        logger.info('<<<')
                        result = Result.RUNTIME_ERROR
                        solution.disqualified = True
                except subprocess.TimeoutExpired as ex:
                    solution.timer.stop()
                    result = Result.TIMELIMIT_EXCEEDED
                    solution.disqualified = True
                if result == Result.DEFAULT_FLAG:
                    if mechanism == Mechanism.judge:
                        result_num = judges[0].run([testcase.input, solution_testcase_out])
                    elif mechanism in [Mechanism.checker,Mechanism.cross_check]:
                        result_num = checkers[0].run([testcase.correct_output, solution_testcase_out])
                    result = Result.from_num(result_num)
                if result == Result.OK:
                    logger.verbose(solution.name + " OK")
                elif result in [Result.WRONG_ANSWER, Result.PRESENTATION_ERROR, Result.RUNTIME_ERROR, Result.TIMELIMIT_EXCEEDED]:
                    logger.error(solution.name + " " + result.short_string)
                elif result == Result.BAD_INVOCATION:
                    logger.critical('The testing program returned a code for bad invocation. This means algo did not manage to run this program correctly. ' + uv(mechanism) + ' is probably writen incorrectly. If you think this is not the case, contact algo developers.')
                    return PROBLEM_ERROR
                else:
                    logger.error(uv(mechanism.name) + ' gave an invalid return code: ' + str(result))
                    return PROBLEM_ERROR
                if result != Result.OK:
                    # todo split results depending on retun code, and report correct error messages in summary
                    solution.bad_testcases.append(BadTestResult(testcase, result))
                    logger.info('Input:')
                    print_file_contents(testcase.input)
                    logger.info('Output:')
                    print_file_contents(solution_testcase_out)
                    if mechanism in [Mechanism.checker, Mechanism.cross_check]:
                        logger.info('Referential output:')
                        print_file_contents(testcase.correct_output)
    logger.info('Summary')
    for solution in solutions:
        res_string = ''
        if len(solution.bad_testcases) != 0:
            res_string = 'Errors in ' + (' '.join([x.str() for x in solution.bad_testcases]))
        else:
            res_string = 'OK'
        logger.info(solution.name + ' (time ' + str(round(solution.timer.get_total(), 3)) + 's, max ' + str(round(solution.timer.get_max(), 3)) + 's): ' + res_string)
    return SUCCESSFULL_EXECUTION

# == Formatting ==================================================================

def uv(to_print):
    return '"' + str(to_print) + '"'

# == Structure ===================================================================

class Program:
    def __init__(self, source_file:str):
        self.source_file = source_file
        self.name = bare_filename(source_file)
    def compile(self):
        self.exe = compile_src(self.source_file, build_path)
    def run(self, args=[], input_file=None, output_file=None, timeout=None):
        logger.debug('Running: ' + uv(self.name) + ', arguments: ' + str([self.exe] + args))
        if input_file: logger.debug('Input: ' + input_file)
        if output_file: logger.debug('Output: ' + output_file)
        if timeout: logger.debug('Timeout: ' + str(timeout))
        in_file = None
        if input_file: in_file = open(input_file)
        out_file = None
        if output_file: out_file = open(output_file, 'w')
        p = subprocess.Popen([self.exe] + args, stdin=in_file, stdout=out_file)
        try:
            p.wait(timeout)
        except subprocess.TimeoutExpired as ex:
            p.kill()
            raise ex
        if out_file: out_file.flush()
        logger.debug('Program run returns: ' + str(p.returncode))
        return p.returncode

class Solution(Program):
    def __init__(self, solution_file:str):
        super().__init__(solution_file)
        self.bad_testcases = []
        self.timer = Timer()
        self.disqualified = False

class Generator(Program):
    def __init__(self, generator_file):
        super().__init__(generator_file)
        self.data_folder = join(data_path, self.name)
    def generate(self):
        os.makedirs(self.data_folder, exist_ok = True)
        self.compile()
        hash_src = HashFile(self.data_folder, self.source_file)
        if not args.force_generation and not hash_src.changed():
            logger.verbose('Skipped generation of ' + uv(self.name) + ' due to non-changed source file.')
            return 0
        logger.verbose('Removing old testcases of ' + uv(self.name))
        for filename in os.listdir(self.data_folder):
            file_location=join(self.data_folder, filename)
            if len(filename)>3 and filename.endswith(conf['out_ext']):
                os.remove(file_location)
        hash_src.save()
        run_return_code = self.run([str(seed), self.data_folder])
        return run_return_code

class Testcase:
    def __init__(self, testcase_input_file:str, dataset:str):
        self.input = testcase_input_file
        self.dataset = dataset
        self.name = bare_filename(self.input)
        self.correct_output = join(dirname(testcase_input_file), self.name + conf['out_ext'])
        self.drawing = join(dirname(testcase_input_file), self.name)
        self.valid = True

class Dataset:
    def __init__(self, dataset_folder:str):
        self.name = basename(dataset_folder)
        self.data_folder = join(data_path, self.name)
        self.testcases = None
    def get_testcases(self, testcase_regex):
        if testcase_regex is None:
            testcase_regex = '*'
        logger.verbose('Globbing ' + self.data_folder)
        globbed_testcases = list(glob.glob(join(self.data_folder, testcase_regex + conf['in_ext'])))
        globbed_testcases.sort()
        self.testcases = [Testcase(x, self) for x in globbed_testcases]
        logger.verbose('Found ' + str(len(self.testcases)) + ' testcases.')

class HashFile:
    def __init__(self, hash_dir:str, src_file_location:str):
        self.hash_location = join(hash_dir, bare_filename(src_file_location) + '.hash')
        self.new_src_hash = hash_file(src_file_location)
        self.old_src_hash = retrieve_content(self.hash_location)

    def changed(self) -> bool:
        if not conf['enable_cache']:
            return True
        return self.new_src_hash != self.old_src_hash

    def save(self):
        save_content(self.hash_location, self.new_src_hash)

class Timer:
    def __init__(self):
        self.total = 0.0
        self.max = 0.0
        self.start_time = 0.0

    def start(self):
        run_info = self.get_info()
        self.start_time = run_info.ru_utime + run_info.ru_stime

    def stop(self):
        run_info = self.get_info()
        self.end_time = run_info.ru_utime + run_info.ru_stime
        self.total += self.end_time - self.start_time
        self.max = max(self.max, self.end_time - self.start_time)

    def get_total(self):
        return self.total

    def get_max(self):
        return self.max

    def get_info(self):
        return resource.getrusage(resource.RUSAGE_CHILDREN)

class BadTestResult:
    def __init__(self, testcase, result):
        self.testcase = testcase
        self.result = result

    def str(self):
        return '[' + self.testcase.dataset.name + '/' + self.testcase.name + ' ' + self.result.short_string + ']'

class Mechanism(enum.Enum):
    judge = 'judge' # it can decide whether the output is correct or not
    checker = 'checker' # have referential solution and the output will be compared
    cross_check = 'cross_check' # more user's solutions run against each other

class Result(enum.Enum):
    OK = (0, 'OK', 'OK')
    WRONG_ANSWER = (1, 'WRONG ANSWER', 'WA')
    PRESENTATION_ERROR = (2, 'PRESENTATION ERROR', 'PE')
    TIMELIMIT_EXCEEDED = (3, 'TIMELIMIT EXCEEDED', 'TLE')
    RUNTIME_ERROR = (4, 'RUNTIME ERROR', 'RE')
    BAD_INVOCATION = (43, 'BAD INVOCATION', 'BAD')
    DEFAULT_FLAG = (88, 'DEFAULT', 'DEF')

    def __init__(self, num:int, long_string:str, short_string:str):
        self.num = num
        self.short_string = short_string
        self.long_string = long_string

    @staticmethod
    def from_num(num:int):
        for result in Result:
            if num == result.num:
                return result
        return None

# == Configuration ===============================================================

def setup_logging():
    logging.addLevelName(VERBOSE_LEVEL, 'VERBOSE')
    def verbose(self, message, *args, **kws):
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)
    logging.Logger.verbose = verbose
    global logger
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def load_configuration(config_file_location):
    global logger
    logger.verbose("load configuration {}".format(config_file_location))
    try:
        with open(config_file_location) as config_file:
            data = json.load(config_file)
    except FileNotFoundError:
        return dict()
    return data

# == File Manipulation ===========================================================

def bare_filename(file_location):
    return basename(file_location).split('.')[0]

def file_extension(file_location):
    return basename(file_location).split('.')[1]

def get_file_or_folder(problem_folder, base_name, class_name=Program):
    for ext in conf['extensions']:
        base_file_path = join(problem_folder, base_name + ext)
        if exists(base_file_path):
            return [class_name(base_file_path)]
    base_folder_path = join(problem_folder, base_name)
    if exists(base_folder_path):
        res = []
        for ext in conf['extensions']:
            res.extend([class_name(x) for x in list(glob.glob(join(base_folder_path, '*'+ext)))])
        return res
    return None

def compile_src(src_file, build_path) -> str:
    extension = file_extension(src_file)
    exe_file = None
    if extension in conf['languages']['interpreted']:
        exe_file = src_file
    base_src_name = bare_filename(src_file)
    exe_file = join(build_path, base_src_name + '.exe')
    compilation = []
    for language in conf['languages']['compiled']:
        if extension in language['extensions']:
            compilation_command_string = language['command']
            substitutions = {
                "flag": "algo",
                "exe": exe_file,
                "source": src_file
            }
            for key, value in substitutions.items():
                compilation_command_string = compilation_command_string.replace(key, value)
            compilation = shlex.split(compilation_command_string)
    if extension in ['cpp', 'C', 'c']:
        compilation = ['g++'] + conf['cflags'] + ['-o', exe_file, src_file]
    if len(compilation):
        os.makedirs(build_path, exist_ok=True)
        hash_src = HashFile(build_path, src_file)
        if not hash_src.changed() and exists(exe_file):
            logger.verbose('Skipped compilation of ' + uv(basename(src_file)) + ' due to non-changed source file.')
            return exe_file
        logger.info('Compiling: ' + uv(basename(src_file)))
        logger.verbose('Compile destination: ' + uv(exe_file))
        res = subprocess.run(compilation)
        if res.returncode != 0:
            raise Exception('Unable to compile source code: ' + uv(src_file))
        logger.verbose('Compilation return code: ' + str(res.returncode))
        hash_src.save()
    if not exe_file:
        raise Exception('Unknown source extension ' + uv(extension) + ' for file ' + uv(src_file) + ', and so algo does not know how to prepare it to be runnable.')
    return exe_file

def find_problem_folder(problem_query):
    logger.verbose('Problem id: ' + uv(problem_query))
    # search in working directory
    location_path = realpath(join(working_directory, problem_query))
    if exists(location_path):
        logger.debug('Problem found locally in ' + uv(location_path))
        return location_path
    # search in default problem repository location
    repository_path_regex = join(problem_search_location, '**', problem_query, conf['def_file'])
    logger.debug('Repository path regex: ' + uv(repository_path_regex))
    for def_file in glob.glob(repository_path_regex, recursive=True):
        # todo if found more than one problem definition, raise a warning
        return dirname(def_file)
    return None

def print_file_contents(file_name, number_of_lines=20):
    if conf['logging_level'] >= QUIET_LEVEL:
        return
    with open(file_name, 'r') as lines:
        count = 1
        for line in lines:
            if len(line[121:122]) == 0:
                print_line = line
            else:
                print_line = line[:100] + '...<more characters>\n'
            count += 1
            print(print_line, end='')
            if count >= number_of_lines:
                print('...<more lines>')
                break

def retrieve_content(file_location):
    try:
        with open(file_location, 'r') as content_file:
            data = content_file.read()
            return data
    except FileNotFoundError:
        pass
    return None

def save_content(file_location, content):
    with open(file_location, 'w+') as content_file:
        content_file.write(content)

def hash_file(file_location):
    BUF_SIZE = pow(2, 16) # reads data in 64kb chunks
    sha1 = hashlib.sha1()
    with open(file_location, 'rb') as content_file:
        while True:
            data = content_file.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    logger.debug('Hashed ' + uv(file_location) + ' into ' + uv(sha1.hexdigest()))
    return sha1.hexdigest()

# == Core Script Logic Chunks ====================================================

def determine_checking_mechanism(judge, checker, referential_solutions, solutions):
    if checker and len(checker) >= 1:
        if referential_solutions and len(referential_solutions) >= 1:
            return Mechanism.checker
        if solutions and len(solutions) >= 2:
            return Mechanism.cross_check
    if judge and len(judge) >= 1:
        return Mechanism.judge
    return None

def validate_testcases(validators, datasets):
    if validators:
        for validator in validators:
            validator.compile()
        logger.info('Testing validity of testcases')
        for dataset in datasets:
            for testcase in dataset.testcases:
                if validators:
                    for validator in validators:
                        if validator.run([], testcase.input) != 0:
                            logger.error('Testcase ' + uv(dataset.name + '/' + testcase.name) + ' is INVALID, according to validator ' + uv(validator.name))
                            return False
        logger.info('All testcases were validated successfully')
    return True

# == Main invocation =============================================================

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        logger.critical('Manually interrupted!')
