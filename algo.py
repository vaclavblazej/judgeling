#!/usr/bin/env python3
# if possible, keep this file under 1000 lines

# get datasets from folder names in .tmp/data/
# allow input files or folders to be passed via arguments
# add precise time measurements
# allow cross checking of user's solutions
# enable generator to supply inputs without saving them
# option to define dataset size ?
# repositories with problems ?
# static dataset ?
# simplification of testcases to find small bad testcase ?
# scan for solutions ?
# add command to generate problem definition scaffolding ?

import os, sys, argparse, logging, glob, subprocess, random, re, hashlib, json, shutil, itertools
import resource # unix specific, for measuring time, see https://stackoverflow.com/questions/16701310/get-how-much-time-python-subprocess-spends/16701365
from os.path import * # frequent functions: join, exists, dirname, realpath, etc.

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1
PROBLEM_ERROR = 2

OK = 0
WRONG_ANSWER = 1
PRESENTATION_ERROR = 2
TIMELIMIT_EXCEEDED = 3
RUNTIME_ERROR = 4
BAD_INVOCATION = 43
DEFAULT_FLAG = 88

VERBOSE_LEVEL = 15
QUIET_LEVEL = 60
parser = argparse.ArgumentParser(description='Test algorithm implementations against problem definitions')
parser.add_argument('-P', '--problem', dest='problem_id', help='problem definition to be run')
parser.add_argument('-S', '--solution', dest='solution', nargs='+', help='user\'s files with his own solutions to the problem')
parser.add_argument('-D', '--dataset', dest='dataset_regex', help='a dataset of testcases which should be run')
parser.add_argument('-T', '--testcase', dest='testcase_regex', help='testcase which should be run')
# parser.add_argument('-s', '--scan', dest='scan', action='store_true', help='scan current folder for files solving the problem')
parser.add_argument('--seed', dest='seed', help='provide a fixed seed for the random data generation')
parser.add_argument('--draw', dest='draw', action='store_true', help='will draw testcases using pic program')
parser.add_argument('--input', dest='input', nargs='+', help='supplies the input data as list of files')
# parser.add_argument('--regenerate', dest='regenerate', action='store_true', help='force the generators to run again')
parser.add_argument('-q', '--quiet', dest='logging_level', const=QUIET_LEVEL, action='store_const', help='no output will be shown')
parser.add_argument('-v', '--verbose', dest='logging_level', const=VERBOSE_LEVEL, action='store_const', help='more detailed info about testing shown')
parser.add_argument('-d', '--debug', dest='logging_level', const=logging.DEBUG, action='store_const', help='very detailed messages of script\'s inner workings')
parser.add_argument('--version', dest='version', action='store_true', help='prints out version information')

conf = { 'logging_level': logging.INFO, }
script_path = dirname(realpath(__file__))
working_directory = os.getcwd()
global_config_folder = join(script_path, 'config.json')
local_config_folder = join(script_path, 'config_local.json')
problem_search_location = realpath(join(script_path, '..', 'acm-problems/problems'))
version = '0.1.1'

# == Main Logic ==================================================================

def main():
    configure()
    args = parser.parse_args()
    setup_logging()
    if args.logging_level: conf['logging_level'] = args.logging_level
    logger.setLevel(conf['logging_level'])
    logger.debug('Configuration: ' + str(conf))
    logger.debug('Script folder: ' + script_path)
    logger.debug('Working directory: ' + working_directory)
    logger.debug('Arguments: ' + str(sys.argv))

    if args.version:
        print('algo version ' + version)
        return SUCCESSFULL_EXECUTION

    # fix problem_id for cases when it is defined in argument by local path
    problem_id = args.problem_id
    if problem_id is None:
        logger.error('Problem ID was not supplied! Add -P <problem_id> argument.')
        return SUCCESSFULL_EXECUTION

    problem_folder = find_problem_folder(problem_id)
    if not problem_folder:
        logger.error('Unable to locate the problem definition file for "' + problem_id + '"')
        return USER_ERROR
    problem_def_path = join(problem_folder, conf['def_file'])
    if not exists(problem_def_path):
        logger.warning('Problem found locally, but is missing a definition file: "' + problem_folder + '"')

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
                logger.error('Supplied solution file does not exist: "' + solution_path + '"')
                return USER_ERROR

    # if args.scan:
        # logger.info('Searching for solutions; the ' + problem_id + ' is solved in:')
        # problem_flag = 'solves ' + problem_id
        # found = []
        # for cpp_file_path in glob.glob('*' + conf['ext'], recursive=True):
            # with open(cpp_file_path) as cpp_file:
                # if problem_flag in cpp_file.read():
                    # found.append(cpp_file_path)
        # logger.info('Scan for ' + problem_flag + ' found ' + str(len(found)) + ' solutions')
        # solutions.extend([Solution(f) for f in found])
    if len(solutions) == 0:
        logger.verbose('Problem information contained in: ' + problem_def_path)
        print_file_contents(problem_def_path)
        logger.info('To test your solution, add -S <solution_file> to the arguments.')
        return SUCCESSFULL_EXECUTION

    for solution in solutions:
        solution.compile()

    # generates input datasets
    generators = get_file_or_folder(problem_folder, 'gen')
    if generators: generators = [Generator(g.source_file) for g in generators]
    # gets the input and determines if it matches the problem definition
    validators = get_file_or_folder(problem_folder, 'val')
    # creates visual representation of inputs
    painters = get_file_or_folder(problem_folder, 'pic')
    # gets the input and contestant's output and checks that the output is correct
    judges = get_file_or_folder(problem_folder, 'jud')
    # referential solution used to produce correct output to compare with
    raw_ref_solutions = get_file_or_folder(problem_folder, 'sol')
    if raw_ref_solutions:
        referential_solutions = [Solution(x.source_file) for x in raw_ref_solutions]
    else:
        referential_solutions = None
    # compares one solution against referential solution if it is correct
    checkers = get_file_or_folder(problem_folder, 'chk')

    logger.verbose('This problem has:')
    if generators: logger.verbose('Generators: ' + str(len(generators)))
    if validators: logger.verbose('Validators: ' + str(len(validators)))
    if painters: logger.verbose('Painters: ' + str(len(painters)))
    if judges: logger.verbose('Judges: ' + str(len(judges)))
    if referential_solutions: logger.verbose('Referential solutions: ' + str(len(referential_solutions)))
    if checkers: logger.verbose('Checkers: ' + str(len(checkers)))

    mechanism = determine_checking_mechanism(judges, checkers, referential_solutions)
    if not mechanism:
        logger.critical('There is no checking mechanism!')
        logger.critical('This is an issue with the problem definition, contact the author.')
        logger.critical('To fix this: create either a "judge" or "checker and referential solution"')
        return PROBLEM_ERROR
    logger.verbose('The checking mechanism is: ' + mechanism)

    random.seed()
    global seed
    seed = 0
    if args.seed: seed = args.seed
    logger.verbose('Seed: ' + str(seed))

    for generator in generators:
        # todo input flag to force dataset generation
        # todo hash problem definition, if changed -> generate dataset again
        # when should we regenerate inputs ? -- generator changed, different seed ?
        logger.debug('Generator output folder: ' + generator.data_folder)
        if generator.generate() != 0:
            logger.critical('Problem dataset generator "' + generator.name + '" has trouble running, contact the problem setter about this issue.')
            return PROBLEM_ERROR

    datasets = [Dataset(g.data_folder) for g in generators]
    if args.dataset_regex:
        datasets = [d for d in datasets if re.search(args.dataset_regex, d.name)]
    for dataset in datasets:
        dataset.get_testcases(args.testcase_regex)

    if not validate_testcases(validators, datasets):
        return USER_ERROR

    if mechanism == 'judge' and judges:
        for judge in judges:
            judge.compile()

    if mechanism == 'checker':
        logger.info('Running the referential solution to get referential outputs')
        for ref in referential_solutions: ref.compile()
        for checker in checkers: checker.compile()
        for dataset in datasets:
            for testcase in dataset.testcases:
                logger.info('running reference ' + testcase.input)
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
                    logger.error('Unable to draw testcase "' + testcase.input + '", interrupting drawing.')
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
            logger.info('Testcase: "' + testcase.name + '"')
            for solution in viable_solutions:
                solution_out_dir = join(dataset.data_folder, 'sol', solution.name)
                os.makedirs(solution_out_dir, exist_ok=True)
                solution_testcase_out = join(solution_out_dir, testcase.name + conf['out_ext'])
                time_result_file = join(solution_out_dir, conf['statistics_file_name'])
                result = DEFAULT_FLAG
                try:
                    solution.timer.start()
                    return_code = solution.run([time_result_file], testcase.input, solution_testcase_out, conf['time_limit_seconds'])
                    solution.timer.stop()
                    if return_code != 0:
                        logger.info('The program returned "' + str(return_code) + '", and output >>>')
                        print_file_contents(solution_testcase_out)
                        logger.info('<<<')
                        result = RUNTIME_ERROR
                        solution.disqualified = True
                except subprocess.TimeoutExpired as ex:
                    solution.timer.stop()
                    result = TIMELIMIT_EXCEEDED
                    solution.disqualified = True
                if result == DEFAULT_FLAG:
                    if mechanism == 'judge':
                        result = judges[0].run([testcase.input, solution_testcase_out])
                    elif mechanism == 'checker':
                        result = checkers[0].run([testcase.correct_output, solution_testcase_out])
                if result == OK:
                    logger.verbose('OK')
                elif result == WRONG_ANSWER:
                    logger.error('WRONG ANSWER')
                elif result == PRESENTATION_ERROR:
                    logger.error('PRESENTATION ERROR')
                elif result == RUNTIME_ERROR:
                    logger.error('RUNTIME ERROR')
                elif result == TIMELIMIT_EXCEEDED:
                    logger.error('TIMELIMIT EXCEEDED')
                elif result == BAD_INVOCATION:
                    logger.critical('The testing program returned a code for bad invocation. This means algo did not manage to run this program correctly. "' + mechanism + '" is probably writen incorrectly. If you think this is not the case, contact algo developers.')
                    return PROBLEM_ERROR
                else:
                    logger.error('"' + mechanism + '" gave an invalid return code: "' + str(result) + '"')
                    return PROBLEM_ERROR
                if result != OK:
                    # todo split results depending on retun code, and report correct error messages in summary
                    solution.bad_testcases.append(BadTestResult(testcase, result))
                    logger.info('Input:')
                    print_file_contents(testcase.input)
                    logger.info('Output:')
                    print_file_contents(solution_testcase_out)
                    if mechanism == 'checker':
                        logger.info('Referential output:')
                        print_file_contents(testcase.correct_output)
    logger.info('Summary')
    for solution in solutions:
        res_string = ''
        if len(solution.bad_testcases) != 0:
            err_str = ' '.join([x.str() for x in solution.bad_testcases])
            res_string = 'Errors in ' + err_str
        else:
            res_string = 'OK'
        logger.info(solution.name + ' (time ' + str(round(solution.timer.get_total(), 3)) + 's, max ' + str(round(solution.timer.get_max(), 3)) + 's): ' + res_string)

# == Structure ===================================================================

class Program:
    def __init__(self, source_file):
        self.source_file = source_file
        self.name = bare_filename(source_file)
    def compile(self):
        self.exe = compile_src(self.source_file, build_path)
    def run(self, args=[], input_file=None, output_file=None, timeout=None):
        logger.debug('Running: "' + self.name + '", arguments: ' + str([self.exe] + args))
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
    def __init__(self, solution_file):
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
        run_return_code = self.run([str(seed), self.data_folder])
        return run_return_code

class Testcase:
    def __init__(self, testcase_input_file, dataset):
        self.input = testcase_input_file
        self.dataset = dataset
        self.name = bare_filename(self.input)
        self.correct_output = join(dirname(testcase_input_file), self.name + conf['out_ext'])
        self.drawing = join(dirname(testcase_input_file), self.name)
        self.valid = True

class Dataset:
    def __init__(self, dataset_folder):
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

class Timer:
    def __init__(self):
        self.total = 0.0
        self.max = 0.0
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
    def __init__(self, testcase, result_code):
        self.testcase = testcase
        self.result_code = result_code
    def str(self):
        additional_str = ''
        if self.result_code == WRONG_ANSWER:
            additional_str = 'WA'
        elif self.result_code == PRESENTATION_ERROR:
            additional_str = 'PE'
        elif self.result_code == RUNTIME_ERROR:
            additional_str = 'RTE'
        elif self.result_code == TIMELIMIT_EXCEEDED:
            additional_str = 'TLE'
        return '[' + self.testcase.dataset.name + '/' + self.testcase.name + ' ' + additional_str + ']'

# == Configuration ===============================================================

def setup_logging():
    logging.addLevelName(VERBOSE_LEVEL, 'VERBOSE')
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
    conf.update(load_configuration(global_config_folder))
    conf.update(load_configuration(local_config_folder))
    return 

def load_configuration(config_file_location):
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

def compile_src(src_file, build_path):
    extension = file_extension(src_file)
    # interpreted languages can be run directly
    if extension == 'py' or extension == 'sh':
        return src_file
    base_src_name = bare_filename(src_file)
    exe_file = join(build_path, base_src_name + '.exe')
    compilation = []
    # cpp-specific compilation
    if extension == 'cpp' or extension == 'C' or extension == 'c':
        compilation = ['g++'] + conf['cflags'] + ['-o', exe_file, src_file]
    # if extension == 'java'
        # compilation = subprocess.run(['javac'] + ['-o', exe_file, src_file])
    if len(compilation):
        os.makedirs(build_path, exist_ok=True)
        hash_location = join(build_path, base_src_name + '.hash')
        new_src_hash = hash_file(src_file)
        old_src_hash = retrieve_content(hash_location)
        if new_src_hash == old_src_hash and exists(exe_file):
            logger.verbose('Skipped compilation of "' + basename(src_file) + '" due to non-changed source file.')
            return exe_file
        logger.info('Compiling: "' + basename(src_file) + '"')
        logger.verbose('Compile destination: "' + exe_file + '"')
        res = subprocess.run(compilation)
        if res.returncode != 0:
            raise Exception('Unable to compile source code: "' + src_file + '"')
        logger.verbose('Compilation return code: ' + str(res.returncode))
        save_content(hash_location, new_src_hash);
        return exe_file
    raise Exception('Unknown source extension "' + extension + '" for file "' + src_file + '", and so algo does not know how to prepare it to be runnable.')

def find_problem_folder(problem_id):
    logger.verbose('Problem id: "' + problem_id + '"')
    # search in working directory
    location_path = realpath(join(working_directory, problem_id))
    if exists(location_path):
        logger.debug('Problem found locally in "' + location_path + '"')
        return location_path
    # search in default problem repository location
    repository_path_regex = join(problem_search_location, '**', problem_id, conf['def_file'])
    logger.debug('Repository path regex: "' + repository_path_regex + '"')
    for def_file in glob.glob(repository_path_regex, recursive=True):
        # todo if found more than one problem definition, raise a warning
        return dirname(def_file)
    return None

def print_file_contents(file_name, number_of_lines=20):
    if conf['logging_level'] >= QUIET_LEVEL:
        return
    with open(file_name, 'r') as lines:
        c = 1
        for line in lines:
            if len(line[121:122]) == 0:
                print_line = line
            else:
                print_line = line[:100] + '...<more characters>\n'
            c += 1
            print(print_line, end='')
            if c >= number_of_lines:
                print('...<more lines>')
                break

def retrieve_content(file_location):
    try:
        with open(file_location, 'r') as f:
            data = f.read()
            return data
    except FileNotFoundError: pass
    return None

def save_content(file_location, content):
    with open(file_location, 'w+') as f:
        f.write(content)

def hash_file(file_location):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    sha1 = hashlib.sha1()
    with open(file_location, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data: break
            sha1.update(data)
    logger.debug('Hashed "' + file_location + '" into "' + sha1.hexdigest() + '"')
    return sha1.hexdigest()

# == Core Script Logic Chunks ====================================================

def determine_checking_mechanism(judge, checker, referential_solutions):
    mechanism = None
    if checker and len(checker) >= 1 and referential_solutions and len(referential_solutions) >= 1:
        # if referential_solutions is None:
            # if len(solutions) == 1:
                # logger.warning('This problem has checker but no referential solution.')
            # else:
                # # todo if problem has no default solution, pick one of the supplied solutions
                # referential_code = solutions[0]
                # referential_solutions = ''
                # logger.info('Referential solution was chosen to be: ' + referential_solutions)
        mechanism = 'checker'
    elif judge and len(judge) >= 1:
        mechanism = 'judge'
    return mechanism

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
                            logger.error('Testcase "' + dataset.name + '/' + testcase.name + '" is INVALID, according to validator "' + validator.name + '"')
                            return False
        logger.info('All testcases were validated successfully')
    return True

# ================================================================================

if __name__ == '__main__':
    main()

