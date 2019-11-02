#!/usr/bin/env python3
# if possible, keep this file under 1000 lines

# option to define dataset size ?
# list problem command ?
# repositories with problems ?
# static dataset ?
# simplification of testcases to find small bad testcase ?

import os, sys, argparse, logging, glob, subprocess, random, re, hashlib
import resource # unix specific, for measuring time, see https://stackoverflow.com/questions/16701310/get-how-much-time-python-subprocess-spends/16701365
from os.path import * # frequent functions: join, exists, dirname, realpath, etc.

VERBOSE_LEVEL = 15
ALL_LEVEL = 60
parser = argparse.ArgumentParser(description='Test algorithm implementations against problem definitions')
parser.add_argument('-P', '--problem', dest='problem_id', help='problem definition to be run')
parser.add_argument('-S', '--solution', dest='solution', nargs='+', help='user\'s files with his own solutions to the problem')
parser.add_argument('-D', '--dataset', dest='dataset_regex', help='a dataset of testcases which should be run')
parser.add_argument('-T', '--testcase', dest='testcase_regex', help='testcase which should be run')
parser.add_argument('-s', '--scan', dest='scan', action='store_true', help='scan current folder for files solving the problem')
parser.add_argument('-q', '--quiet', dest='logging_level', const=ALL_LEVEL, action='store_const', help='no output will be shown')
parser.add_argument('-v', '--verbose', dest='logging_level', const=VERBOSE_LEVEL, action='store_const', help='more detailed info about testing shown')
parser.add_argument('-d', '--debug', dest='logging_level', const=logging.DEBUG, action='store_const', help='very detailed messages of script\'s inner workings')
parser.add_argument('--version', dest='version', action='store_true', help='prints out version information')

preprocessor_flag='ALGME'
cflags=['-O2', '-g', '-std=c++17', '-lm', '-pedantic', '-D'+preprocessor_flag]
ext='.cpp'
script_path = dirname(realpath(__file__))
working_directory = os.getcwd()
algo_config_folder = join(script_path, '.config')
def_file = 'def.toml'
problem_search_location = realpath(join(script_path, '..', 'acm-problems/problems'))
statistics_file_name = 'time.cls'
version = '0.1.0'

# == Main Logic ==================================================================

def main():
    setup_logging()
    args = parser.parse_args()
    if not args.logging_level: 
        args.logging_level = logging.INFO
    if args.logging_level: logger.setLevel(args.logging_level)
    configure()
    # todo print configuration
    logger.debug('SCRIPT FOLDER: ' + script_path)
    logger.debug('WORKING DIRECTORY: ' + working_directory)
    logger.debug('arguments: ' + str(sys.argv))

    if args.version:
        print('algo version ' + version)
        return 0

    if args.problem_id is None:
        logger.error('Problem ID was not supplied!')
        return 0
    problem_def_path = find_problem(args.problem_id)
    if not problem_def_path:
        logger.error('Unable to locate the problem definition file!')
        return 1
    problem_folder = dirname(problem_def_path)
    global data_path, build_path
    data_path=join(problem_folder, ".tmp", "data")
    build_path=join(problem_folder, ".tmp", "build")

    # if no testing will take place, print the problem, input, and output definition, and exit

    logger.debug('PROBLEM PATH: ' + problem_def_path)
    logger.debug("DATA PATH: " + data_path)
    logger.debug("BUILD PATH: " + build_path)

    solutions = []
    if args.solution:
        for arg_sol in args.solution:
            solution_path = join(working_directory, arg_sol)
            if exists(solution_path):
                solutions.append(Solution(solution_path))
            else:
                logger.error('supplied solution was not found')
                logger.error('solution path ' + solution_path)
                return 1

    if args.scan:
        logger.info('Searching for solutions; the ' + args.problem_id + ' is solved in:')
        problem_flag = 'solves ' + args.problem_id
        found = []
        for cpp_file_path in glob.glob('*.cpp', recursive=True):
            with open(cpp_file_path) as cpp_file:
                if problem_flag in cpp_file.read():
                    found.append(cpp_file_path)
        logger.info('scan for ' + problem_flag + ' found ' + str(len(found)) + ' solutions')
        solutions.extend([Solution(f) for f in found])
    if len(solutions) == 0:
        # not having a solution should not be an issue when debugging the problem definition with only referential solution
        logger.error('You supplied no solution for problem ' + args.problem_id)
        return 1

    for solution in solutions:
        if not solution.compile():
            logger.error('Compilation of a solution ' + solution.name + ' was not succesful')
            return 1

    # prepare code correctness checking mechanism variables
    # generates input datasets
    generators = get_file_or_folder(problem_folder, 'gen')
    # gets the input and determines if it matches the problem definition
    validators = get_file_or_folder(problem_folder, 'val')
    # gets the input and contestant's output and checks that the output is correct
    judges = get_file_or_folder(problem_folder, 'jud')
    # referential solution used to produce correct output to compare with
    referential_solutions = get_file_or_folder(problem_folder, 'sol')
    # compares one solution against referential solution if it is correct
    checkers = get_file_or_folder(problem_folder, 'chk')

    logger.verbose('This problem has:')
    if generators: logger.verbose('generators: ' + str(len(generators)))
    if validators: logger.verbose('validators: ' + str(len(validators)))
    if judges: logger.verbose('judges: ' + str(len(judges)))
    if referential_solutions: logger.verbose('referential_solutions: ' + str(len(referential_solutions)))
    if checkers: logger.verbose('checkers: ' + str(len(checkers)))

    mechanism = determine_checking_mechanism(judges, checkers, referential_solutions)
    if not mechanism:
        logger.error('There is no checking mechanism')
        logger.error('Create either judge or checker (with referential solution)')
        return 1
    logger.verbose('The checking mechanism is: ' + mechanism)

    datasets = [Dataset(g) for g in generators]
    if args.dataset_regex:
        datasets = [d for d in datasets if re.search(args.dataset_regex, d.name)]
    random.seed()
    global seed
    seed = random.randint(0,1e12)
    logger.verbose('Seed: ' + str(seed))
    for dataset in datasets:
        # todo input flag to force dataset generation
        # todo hash problem definition, if changed -> generate dataset again
        dataset.generate()
        dataset.get_testcases(args.testcase_regex)
        logger.debug('generator_file output folder: ' + dataset.data_folder)

    if judges:
        for judge in judges:
            judge.compile()

    if not validate_testcases(validators, datasets):
        return 1

    logger.info('Running datasets on solutions')
    for dataset in datasets:
        logger.info('Dataset ' + dataset.name)
        for testcase in dataset.testcases:
            logger.info('Testcase: ' + testcase.name)
            for solution in solutions:
                solution_out_dir = join(dataset.data_folder, 'sol', solution.name)
                os.makedirs(solution_out_dir, exist_ok=True)
                solution_testcase_out = join(solution_out_dir, testcase.name + '.out')
                time_result_file = join(solution_out_dir, statistics_file_name)
                time_limit_seconds = 10
                # todo add precise time measurements
                solution.timer.start()
                if solution.run([], testcase.input, solution_testcase_out, time_limit_seconds) != 0:
                    logger.info('The program returned ' + result + ' and output >>>')
                    subprocess.run(['cat', solution_testcase_out])
                    logger.info('<<<')
                    solution.timer.stop()
                    continue
                solution.timer.stop()
                result = 88
                if mechanism == 'judge':
                    judge = judges[0]
                    result = judge.run([testcase.input, solution_testcase_out])
                elif mechanism == 'checker':
                    checker = checkers[0]
                    if not testcase.correct_output:
                        referential_solutions[0].run([], testcase.input, testcase.correct_output)
                    result = checker.run([], testcase.correct_output, solution_testcase_out)
                else:
                    logger.error('invalid checking mechanism')
                    continue
                if result == 0:
                    logger.verbose('OK')
                elif result == 1:
                    logger.error('WRONG ANSWER')
                elif result == 2:
                    logger.error('PRESENTATION ERROR')
                elif result == 88:
                    logger.error('invocation failed')
                else:
                    logger.error('Result gave an invalid return code: ' + str(result))
                if result != 0:
                    solution.bad_testcases.append(dataset.name + '/' + testcase.name)
                    logger.info('Input:')
                    print_file_contents(testcase.input)
                    logger.info('Output:')
                    print_file_contents(solution_testcase_out)
    logger.info('Summary')
    for solution in solutions:
        res_string = ''
        if len(solution.bad_testcases) != 0:
            res_string = 'Errors in ' + str(solution.bad_testcases)
        else:
            res_string = 'OK'
        logger.info(solution.name + " (" + str(round(solution.timer.get_total(), 3)) + "s): " + res_string)

# == Structure ===================================================================

class Program:
    def __init__(self, source_file):
        self.source_file = source_file
        self.name = bare_filename(source_file)
    def compile(self):
        self.exe = compile_src(self.source_file, build_path)
        # todo check is compilation went ok, if not stop the program execution and raise error
        return True
    def run(self, args=[], input_file=None, output_file=None, timeout=None):
        logger.debug('running: ' + self.name)
        in_file = None
        if input_file: in_file = open(input_file)
        out_file = None
        if output_file: out_file = open(output_file, 'w')
        # todo timeout
        p = subprocess.Popen([self.exe] + args, stdin=in_file, stdout=out_file)
        p.wait()
        if out_file: out_file.flush()
        logger.debug('program run returns: ' + str(p.returncode))
        return p.returncode

class Solution(Program):
    def __init__(self, solution_file):
        super().__init__(solution_file)
        self.bad_testcases = []
        self.timer = Timer()

class Testcase:
    def __init__(self, testcase_input_file, dataset):
        self.input = testcase_input_file
        self.dataset = dataset
        self.name = bare_filename(self.input)
        self.correct_output = join(dirname(testcase_input_file), self.name, '.out')
        self.valid = True

    def test(self, input_file):
        pass

class Dataset:
    def __init__(self, generator_program):
        self.generator_program = generator_program
        self.name = generator_program.name
        self.data_folder = join(data_path, self.name)
        self.testcases = None

    def generate(self):
        os.makedirs(self.data_folder, exist_ok = True)
        self.generator_program.compile()
        self.generator_program.run([str(seed), self.data_folder])

    def get_testcases(self, testcase_regex):
        if testcase_regex is None:
            testcase_regex = "*"
        globbed_testcases = list(glob.glob(join(self.data_folder, testcase_regex + '.in')))
        globbed_testcases.sort()
        self.testcases = [Testcase(x, self) for x in globbed_testcases]
        logger.verbose('found ' + str(len(self.testcases)) + ' testcases')

class Timer:
    def __init__(self):
        self.total = 0.0

    def start(self):
        run_info = self.get_info()
        self.start_time = run_info.ru_utime + run_info.ru_stime

    def stop(self):
        run_info = self.get_info()
        self.end_time = run_info.ru_utime + run_info.ru_stime
        self.total += self.end_time - self.start_time

    def get_total(self):
        return self.total

    def get_info(self):
        return resource.getrusage(resource.RUSAGE_CHILDREN)

# == Configuration ===============================================================

def setup_logging():
    # make custom verbose level
    logging.addLevelName(VERBOSE_LEVEL, "VERBOSE")
    def verbose(self, message, *args, **kws):
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)
    logging.Logger.verbose = verbose
    global logger
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def configure():
    if not exists(algo_config_folder):
        os.makedirs(algo_config_folder)

# == File Manipulation ===========================================================

def bare_filename(file_location):
    return basename(file_location).split('.')[0]

def get_file_or_folder(problem_folder, base_name):
    base_file_path = join(problem_folder, base_name + '.cpp')
    base_folder_path = join(problem_folder, base_name)
    if exists(base_file_path):
        return [Program(base_file_path)]
    elif exists(base_folder_path):
        return [Program(x) for x in list(glob.glob(join(base_folder_path, '*.cpp')))]
    return None

def compile_src(src_file, build_path):
    os.makedirs(build_path, exist_ok=True)
    exe_name = bare_filename(src_file) + '.exe'
    exe_file = join(build_path, exe_name)
    logger.verbose('compile ' + basename(src_file) + ' into ' + exe_file)
    res = subprocess.run(['g++'] + cflags + ['-o', exe_file, src_file])
    logger.verbose('compilation return code: ' + str(res.returncode))
    return exe_file

def find_problem(problem_id):
    logger.verbose('PROBLEM ID: ' + problem_id)
    # search in working directory
    location_path = join(working_directory, problem_id)
    definition_path = join(location_path, def_file)
    if exists(location_path) and exists(definition_path):
        logger.debug('problem found locally in ' + location_path)
        return location_path
    # serach in default problem repository location
    repository_path_regex = join(problem_search_location, "**", problem_id, def_file)
    logger.debug('repository_path_regex: ' + repository_path_regex)
    for cpp_file_path in glob.glob(repository_path_regex, recursive=True):
        # todo if found more problem, raise warning or error
        return cpp_file_path
    return None

def print_file_contents(file_name, number_of_lines=20):
    with open(file_name, 'r') as lines:
        c = 1
        for line in lines:
            print(str(c) + ': ' + line[:100])
            if len(line[101:102]):
                print('...<more characters>')
            c+=1
            if c >= number_of_lines:
                print('...<more lines>')
                break

def hash_file(file_location):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    sha1 = hashlib.sha1()
    with open(file_location, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data: break
            sha1.update(data)
    logger.debug('hashed ' + file_location + ' into ' + sha1.hexdigest())
    return sha1.hexdigest()

# == Core Script Logic Chunks ====================================================

def determine_checking_mechanism(judge, checker, referential_solutions):
    mechanism = None
    if judge and len(judge) >= 1:
        mechanism = 'judge'
    elif checker and len(checker) >= 1:
        if referential_solutions is None:
            if len(solutions) == 1:
                logger.warning('This problem has checker but no referential solution. Please consider supplying more than one solution to enalbe cross-validation. The first supplied solution will be assumed to be referential.')
            else:
                # todo if problem has no default solution, pick one of the supplied solutions
                referential_code = solutions[0]
                referential_solutions = ''
                logger.info('Referential solution was chosen to be: ' + referential_solutions)
        mechanism = 'checker'
    return mechanism

def validate_testcases(validators, datasets):
    if validators:
        for validator in validators:
            if not validator.compile():
                return False
        logger.info('Testing validity of testcases')
        for dataset in datasets:
            for testcase in dataset.testcases:
                if validators:
                    for validator in validators:
                        if validator.run([], testcase.input) != 0:
                            logger.error('Testcase ' + dataset.name + "/" + testcase.name + ' is INVALID, according to validator ' + validator.name)
                            return False
        logger.info('All testcases were validated successfully')
    return True

# ================================================================================

if __name__ == "__main__":
    main()

