#!/usr/bin/env python3
# if possible keep this file under 1000 lines

# option to define dataset size ?
# list problem command ?
# repositories with problems ?
# static dataset ?
# simplification of testcases to find small bad testcase ?

import os, sys, argparse, logging, glob, subprocess, random, re, hashlib
from os.path import * # frequent functions: join, exists, dirname, realpath, etc.

parser = argparse.ArgumentParser(description='Test algorithm implementations against problem definitions')
parser.add_argument('-P', '--problem', dest='problem_id', help='problem definition to be run')
parser.add_argument('-S', '--solution', dest='solution', nargs='+', help='user\'s files with his own solutions to the problem')
parser.add_argument('-D', '--dataset', dest='dataset_regex', const='test', action='store_const', help='a dataset of testcases which should be run')
parser.add_argument('-T', '--testcase', dest='testcase_regex', const='test', action='store_const', help='testcase which should be run')
parser.add_argument('-s', '--scan', dest='scan', action='store_true', help='scan current folder for files solving the problem')
parser.add_argument('-q', '--quiet', dest='logging_level', const=60, action='store_const', help='no output will be shown')
parser.add_argument('-v', '--verbose', dest='logging_level', const=logging.INFO, action='store_const', help='more detailed info about testing shown')
parser.add_argument('-d', '--debug', dest='logging_level', const=logging.DEBUG, action='store_const', help='very detailed messages of script\'s inner workings')

cflags=['-O2','-g','-std=c++17','-lm','-pedantic','-DALGME']
ext='.cpp'
script_path = dirname(realpath(__file__))
working_directory = os.getcwd()
algo_config_folder = join(script_path, '.config')
def_file = 'def.toml'
problem_search_location = realpath(join(script_path, '..', 'acm-problems/problems'))
statistics_file_name = 'time.cls'

def main():
    setup_logging()
    args = parser.parse_args()
    if args.logging_level: logger.setLevel(args.logging_level)
    configure()
    logger.debug('SCRIPT FOLDER: ' + script_path)
    logger.debug('WORKING DIRECTORY: ' + working_directory)
    logger.debug('arguments: ' + str(sys.argv))

    # translate the problem_id into the location of the problem definition
    if args.problem_id is None:
        print('Problem ID was not supplied!')
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
        # should not be a problem when debugging the problem definition with only referential solution
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
    judge = get_file_or_folder(problem_folder, 'jud')
    # referential solution used to produce correct output to compare with
    referential_solution = get_file_or_folder(problem_folder, 'sol')
    # compares one solution against referential solution if it is correct
    checker = get_file_or_folder(problem_folder, 'chk')

    logger.info('This problem has:')
    if generators: logger.info('generators: ' + str(len(generators)))
    if validators: logger.info('validators: ' + str(len(validators)))
    if judge: logger.info('judges: ' + str(len(judge)))
    if referential_solution: logger.info('referential_solutions: ' + str(len(referential_solution)))
    if checker: logger.info('checkers: ' + str(len(checker)))

    mechanism = determine_checking_mechanism(judge, checker, referential_solution)
    if not mechanism:
        logger.error('There is no checking mechanism')
        logger.error('Create either judge or checker (with referential solution)')
        return 0
    logger.info('The checking mechanism is: ' + mechanism)
    datasets = [Dataset(g) for g in generators]
    if args.dataset_regex:
        datasets = [d for d in datasets if re.search(args.dataset_regex, d.name)]
    random.seed()
    global seed
    seed = random.randint(0,1e12)
    logger.info('Seed: ' + str(seed))
    for dataset in datasets:
        # todo input flag to force dataset generation
        # todo hash problem definition, if changed -> generate dataset again
        dataset.generate()
        dataset.get_testcases(args.testcase_regex)
        logger.debug('generator_file output folder: ' + dataset.data_folder)

    if validators:
        for validator in validators:
            if not validator.compile():
                return 1
        logger.info('Testing validity of testcases')
        for dataset in datasets:
            for testcase in dataset.testcases:
                if validators:
                    for validator in validators:
                        if validator.run([], testcase.input) != 0:
                            logger.error('Testcase ' + dataset.name + "/" + testcase.name + ' is INVALID, according to validator ' + validator.name)
                            return 1
        logger.info('All testcases were validated successfully')

    logger.info('Running test on solutions')
    for dataset in datasets:
        logger.info('Dataset ' + dataset.name)
        for testcase in dataset.testcases:
            logger.info('Testcase: ' + testcase.name)
            for solution in solutions:
                # todo proper folder and file names
                solution_out_dir=join(dataset.data_folder, 'sol', solution.name)
                os.makedirs(solution_out_dir, exist_ok=True)
                solution_testcase_out=join(solution_out_dir, testcase.name)
                time_result_file=join(solution_out_dir, statistics_file_name)
                # todo check the error output for other lines than time
                solution.run([])
                # output=$(/usr/bin/time -f '%U' "$executable" < "$testcase.input" > "$solution_testcase_out" 2>"$time_result_file")
                # time_result="$(cat "$time_result_file")"
                # todo get result of the program
                # result="$?"
                if result != 0:
                    logger.info('The program returned ' + result + ' and output >>>')
                    subprocess.run(['cat', solution_testcase_out])
                    logger.info('<<<')
                    continue
                result=88
                if mechanism == 'judge':
                    pass
                    # output=$("$judge" "$testcase.input" "$solution_testcase_out")
                    # result="$?"
                elif mechanism == 'checker':
                    pass
                    # todo if testcase.correct_output does not exist
                    # "$referential_solution" < "$testcase.input" > "$testcase_out"
                    # output=$("$checker" "$testcase_out" "$solution_testcase_out")
                    # result="$?"
                else:
                    logger.error('invalid checking mechanism')
                    continue
                if result == 0:
                    logger.warning('OK')
                elif result == 1:
                    logger.error('WRONG ANSWER')
                elif result == 2:
                    logger.error('PRESENTATION ERROR')
                elif result == 88:
                    logger.error('invocation failed')
                else:
                    logger.error('result gave invalid return code: ' + result)
                # todo
                print("$executable_name: $result_str ($time_result)")
                if result != 0:
                    bad_files[executable_name].append(testcase.name)
                    logger.info('Input:')
                    logger.info(testcase.input)
                    logger.info('Output:')
                    logger.info(solution_testcase_out)
                if output != '':
                    print(output)
    print('Summary')
    for executable in executables:
        executable_name = ''
        print(executable_name)
        if len(bad_files[executable_name]) != 0:
            print('Errors in ' + str(bad_files[executable_name]))
        else:
            print('OK')

# structure

class Program:
    def __init__(self, source_file):
        self.source_file = source_file
        self.name = bare_filename(source_file)
    def compile(self):
        self.exe = compile_src(self.source_file, build_path)
        # todo check is compilation went ok, if not stop the program execution and raise error
        return True
    def run(self, args=[], input_file=None, output_file=None, timeout=None):
        in_file = None
        if input_file: in_file = open(input_file)
        out_file = None
        if output_file: out_file = open(output_file, 'w')
        p = subprocess.Popen([self.exe] + args, stdin=in_file, stdout=out_file)
        p.wait()
        if out_file: out_file.flush()
        logger.debug('program run returns: ' + str(p.returncode))
        return p.returncode

class Solution(Program):
    def __init__(self, solution_file):
        super().__init__(solution_file)
        self.bad_testcases = []

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
        self.testcases = [Testcase(x, self) for x in list(glob.glob(join(self.data_folder, testcase_regex + '.in')))]
        logger.info('found ' + str(len(self.testcases)) + ' testcases')

# configuration

def setup_logging():
    global logger
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def configure():
    if not exists(algo_config_folder):
        # logger.info('first run configuration')
        os.makedirs(algo_config_folder)

# file manipulation

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
    if exe_name[0] == '_':
        exe_name = 'default.exe'
    exe_file = join(build_path, exe_name)
    logger.info('compile ' + basename(src_file) + ' into ' + exe_file)
    res = subprocess.run(['g++'] + cflags + ['-o', exe_file, src_file])
    logger.info('compilation return code: ' + str(res.returncode))
    return exe_file

def find_problem(problem_id):
    logger.info('PROBLEM ID: ' + problem_id)
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

# core script logic chunks

def determine_checking_mechanism(judge, checker, referential_solution):
    mechanism = None
    if judge and len(judge) >= 1:
        mechanism = 'judge'
    elif checker and len(checker) >= 1:
        if referential_solution is None:
            if len(solutions) == 1:
                logger.info('This problem has checker but no referential solution. Please consider supplying more than one solution to enalbe cross-validation. The first supplied solution will be assumed to be referential.')
            else:
                # todo if problem has no default solution, pick one of the supplied solutions
                referential_code = solutions[0]
                referential_solution = ''
                logger.info('Referential solution was chosen to be: ' + referential_solution)
        mechanism = 'checker'
    return mechanism


if __name__ == "__main__":
    main()

