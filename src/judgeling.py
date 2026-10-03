#!/usr/bin/env python3
# Keep this program in a single file with at most 1000 lines for the sake of simplicity.

# Minimalistic tool to manage problem packages for competitive programming.

import contextlib
import enum
import hashlib
import importlib.metadata
import itertools
import json
import logging
import os

# unix specific, for measuring time, see https://stackoverflow.com/questions/16701310/get-how-much-time-python-subprocess-spends/16701365
import resource
import shlex
import shutil
import subprocess
import tomllib
from argparse import ArgumentParser
from glob import glob
from os.path import basename, dirname, exists, join, realpath, splitext
from re import search
from sys import argv, exit, stderr
from typing import Any, cast

SUCCESSFULL_EXECUTION = 0
USER_ERROR = 1  # argument format is fine, but content is wrong
PROBLEM_ERROR = 2  # content of problem definition is wrong
INVALID_ARGUMENT = 129  # argument format is wrong

VERBOSE_LEVEL = 15
QUIET_LEVEL = 60


class JudgelingException(Exception):
    """Raised for expected failure conditions the tool detects in its own logic (as opposed to subprocess errors)."""


class VerboseLogger(logging.Logger):
    """Logger with an extra VERBOSE level sitting between INFO and DEBUG."""

    def verbose(self, message: object, *args: object, **kws: Any) -> None:
        if self.isEnabledFor(VERBOSE_LEVEL):
            self._log(VERBOSE_LEVEL, message, args, **kws)


logging.setLoggerClass(VerboseLogger)
logger: VerboseLogger = cast(VerboseLogger, logging.getLogger("judgeling"))  # handlers/level configured in setup_logging()


class JudgelingArgumentParser(ArgumentParser):
    """ArgumentParser that exits with INVALID_ARGUMENT instead of argparse's default exit code on a parse error."""

    def error(self, message):
        self.print_usage(stderr)
        self.exit(INVALID_ARGUMENT, f"{self.prog}: error: {message}\n")


parser = JudgelingArgumentParser(
    description="Test algorithm implementations on problem definitions",
    epilog="Confront documentation of this script for examples and usage of various concepts.",
)
# help as '-h' and '--help' is added by default
parser.add_argument("-V", "--version", dest="version", action="store_true", help="print out the version")
parser.add_argument("-P", "--problem", dest="problem_query", help="problem definition to be run")
parser.add_argument("-S", "--solution", dest="solution", nargs="+", help="user's files with his own solutions to the problem")
parser.add_argument("-D", "--dataset", dest="dataset_regex", help="filter used datasets using regex")
parser.add_argument("-T", "--testcase", dest="testcase_regex", help="filter used testcases using regex")
parser.add_argument("--seed", dest="seed", help="provide a rng seed for dataset generators")
parser.add_argument("--draw", dest="draw", action="store_true", help="create drawings of testcases using the pic program")
parser.add_argument("--input", dest="input", nargs="+", help="supply input data files manually")
parser.add_argument("-g", "--force-gen", dest="force_generation", action="store_true", help="force the data generators to run again")
parser.add_argument("-q", "--quiet", dest="logging_level", const=QUIET_LEVEL, action="store_const", help="no logging will be shown")
parser.add_argument("-v", "--verbose", dest="logging_level", const=VERBOSE_LEVEL, action="store_const", help="more detailed info about testing")
parser.add_argument("-d", "--debug", dest="logging_level", const=logging.DEBUG, action="store_const", help="very detailed logging of script's inner workings")

conf: dict[str, Any] = {
    "logging_level": logging.INFO,
}  # logging is set up before config loads
script_path = dirname(realpath(__file__))
project_root = dirname(script_path)  # repo root; judgeling.py lives in src/
working_directory = os.getcwd()
global_config_folder = join(project_root, "config.json")
local_config_folder = join(project_root, "config_local.json")
problem_search_location = realpath(join(project_root, "..", "acm-problems/problems"))

# == Main Logic ==================================================================


def main() -> int:
    setup_logging()
    conf.update(load_configuration(global_config_folder))
    conf.update(load_configuration(local_config_folder))
    global args
    args = parser.parse_args()
    if args.logging_level:
        conf["logging_level"] = args.logging_level
    logger.setLevel(conf["logging_level"])
    logger.debug(f"Configuration: {conf}")
    logger.debug(f"Script folder: {quote(script_path)}")
    logger.debug(f"Working directory: {quote(working_directory)}")
    logger.debug(f"Arguments: {argv}")

    if args.version:
        print("judgeling version " + get_version())
        return SUCCESSFULL_EXECUTION

    problem_query = args.problem_query
    # default problem folder is the current working directory (default help command would have to be disabled)
    if problem_query is None and exists(join(working_directory, conf["def_file"])):
        problem_query = working_directory
    if problem_query is None:
        logger.error("Problem ID was not supplied! Add -P <problem location/id> argument.")
        return SUCCESSFULL_EXECUTION

    problem_folder = find_problem_folder(problem_query)
    if not problem_folder:
        logger.error("Unable to locate the problem definition file for " + quote(problem_query))
        return USER_ERROR
    problem_def_path = join(problem_folder, conf["def_file"])
    if not exists(problem_def_path):
        logger.warning("Problem found locally, but is missing a definition file: " + quote(problem_folder))

    global data_path, build_path
    data_path = join(problem_folder, conf["problem_tmp_folder"], "data")
    build_path = join(problem_folder, conf["problem_tmp_folder"], "build")
    logger.debug("PROBLEM DIRECTORY: " + problem_folder)
    logger.debug("DATA PATH: " + data_path)
    logger.debug("BUILD PATH: " + build_path)

    project_config_folder = join(problem_folder, ".judgeling_config.json")
    conf.update(load_configuration(project_config_folder))

    solutions = []
    for arg_sol in args.solution or []:
        solution_path = join(working_directory, arg_sol)
        if exists(solution_path):
            solutions.append(Solution(solution_path))
        else:
            logger.error("Supplied solution file does not exist: " + quote(solution_path))
            return USER_ERROR

    if not solutions:
        if exists(problem_def_path):
            logger.verbose("Problem information contained in: " + problem_def_path)
            print_file_contents(problem_def_path)
        logger.info("To test your solution, add -S <solution_file> to the arguments.")
        return SUCCESSFULL_EXECUTION

    for solution in solutions:
        solution.compile()

    file_structure = conf["file_structure"]
    generators = get_file_or_folder(problem_folder, file_structure["generator"], Generator)
    validators = get_file_or_folder(problem_folder, file_structure["validator"])
    painters = get_file_or_folder(problem_folder, file_structure["painter"])
    judges = get_file_or_folder(problem_folder, file_structure["judge"])
    referential_solutions = get_file_or_folder(problem_folder, file_structure["solution"], Solution)
    # compares one solution against referential solution if it is correct
    checkers = get_file_or_folder(problem_folder, file_structure["checker"])

    logger.verbose("This problem has:")
    if generators:
        logger.verbose("Generators: " + str(len(generators)))
    if validators:
        logger.verbose("Validators: " + str(len(validators)))
    if painters:
        logger.verbose("Painters: " + str(len(painters)))
    if judges:
        logger.verbose("Judges: " + str(len(judges)))
    if referential_solutions:
        logger.verbose("Referential solutions: " + str(len(referential_solutions)))
    if checkers:
        logger.verbose("Checkers: " + str(len(checkers)))

    mechanism = determine_checking_mechanism(judges, checkers, referential_solutions, solutions)
    if not mechanism:
        logger.critical("There is no checking mechanism!")
        logger.critical("This is an issue with the problem definition, contact the author.")
        logger.critical('To fix this: create either a "judge" or "checker and referential solution"')
        return PROBLEM_ERROR
    logger.verbose("The checking mechanism is: " + quote(mechanism.name))

    global seed
    seed = 0
    if args.seed:
        seed = args.seed
    logger.verbose("Seed: " + str(seed))

    manual_input_files = args.input
    if manual_input_files:
        logger.verbose("Following inputs were supplied: " + quote(manual_input_files))
        manual_input_folder = join(data_path, conf["manual_testcases_folder_name"])
        os.makedirs(manual_input_folder, exist_ok=True)
        for manual_input_file in manual_input_files:
            if exists(manual_input_file):
                shutil.copy(
                    manual_input_file,
                    join(manual_input_folder, basename(manual_input_file)),
                )
            else:
                logger.error("Supplied input file " + quote(manual_input_file) + " could not be found")
        datasets = [Dataset(manual_input_folder)]
    else:
        if args.dataset_regex:
            generators = [g for g in generators if search(args.dataset_regex, g.name)]
        for generator in generators:
            logger.debug("Generator output folder: " + generator.data_folder)
            if generator.generate() != 0:
                logger.critical("Problem dataset generator " + quote(generator.name) + " has trouble running, contact the problem setter about this issue.")
                return PROBLEM_ERROR

        datasets = [Dataset(g.data_folder) for g in generators]
        if args.dataset_regex:
            datasets = [d for d in datasets if search(args.dataset_regex, d.name)]

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
            logger.info("Picked solution " + quote(referential_solutions[0].name) + " as a referential solution")
        logger.info("Running referential solution to get referential outputs")
        for ref in referential_solutions:
            ref.compile()
        for checker in checkers:
            checker.compile()
        for dataset in datasets:
            logger.info("Dataset " + dataset.name)
            for testcase in dataset.testcases:
                logger.info("Testcase: " + quote(testcase.name))
                referential_solutions[0].run([], testcase.input, testcase.correct_output)
        solutions.extend(referential_solutions)
        logger.info("Referential outputs obtained succesfully")

    if painters:
        if args.draw:
            painter = painters[0]
            painter.compile()
            logger.info("Drawing testcases")
            paint_outfile = os.devnull
            if conf["logging_level"] <= VERBOSE_LEVEL:
                paint_outfile = None
            for testcase in list(itertools.chain(*[dataset.testcases for dataset in datasets])):
                logger.info("Drawing testcase " + testcase.dataset.name + "/" + testcase.name)
                if (
                    painter.run(
                        [testcase.drawing, testcase.input, testcase.correct_output],
                        None,
                        paint_outfile,
                    )
                    != 0
                ):
                    logger.error("Unable to draw testcase " + quote(testcase.input) + ", interrupting drawing.")
                    break
        else:
            logger.info("Available painter, add --draw flag to allow painter to draw testcases (can take a long time).")

    logger.info("Running datasets on solutions")
    for dataset in datasets:
        logger.info("Dataset " + dataset.name)
        for solution in solutions:
            solution.disqualified = False
        for testcase in dataset.testcases:
            viable_solutions = [s for s in solutions if not s.disqualified]
            if len(viable_solutions) == 0:
                logger.info("All solutions were disqualified, skipping rest of testcases for this dataset.")
                break
            logger.info("Testcase: " + quote(testcase.name))
            for solution in viable_solutions:
                solution_out_dir = join(dataset.data_folder, "sol", solution.name)
                os.makedirs(solution_out_dir, exist_ok=True)
                solution_testcase_out = join(solution_out_dir, testcase.name + conf["out_ext"])
                time_result_file = join(solution_out_dir, conf["statistics_file_name"])
                result = Result.DEFAULT_FLAG
                try:
                    solution.timer.start()
                    return_code = solution.run(
                        [time_result_file],
                        testcase.input,
                        solution_testcase_out,
                        conf["time_limit_seconds"],
                    )
                    solution.timer.stop()
                    if return_code != 0:
                        logger.info("The program returned " + quote(return_code) + " (should return 0), and output >>>")
                        print_file_contents(solution_testcase_out)
                        logger.info("<<<")
                        result = Result.RUNTIME_ERROR
                        solution.disqualified = True
                except subprocess.TimeoutExpired:
                    solution.timer.stop()
                    result = Result.TIMELIMIT_EXCEEDED
                    solution.disqualified = True
                if result == Result.DEFAULT_FLAG:
                    result_num = Result.BAD_INVOCATION.num  # defensive default; every real mechanism overrides it below
                    if mechanism == Mechanism.judge:
                        result_num = judges[0].run([testcase.input, solution_testcase_out])
                    elif mechanism in [Mechanism.checker, Mechanism.cross_check]:
                        result_num = checkers[0].run([testcase.correct_output, solution_testcase_out])
                    result = Result.from_num(result_num)
                if result == Result.OK:
                    logger.verbose(solution.name + " OK")
                elif result in [
                    Result.WRONG_ANSWER,
                    Result.PRESENTATION_ERROR,
                    Result.RUNTIME_ERROR,
                    Result.TIMELIMIT_EXCEEDED,
                ]:
                    logger.error(solution.name + " " + result.short_string)
                elif result == Result.BAD_INVOCATION:
                    logger.critical("The testing program returned a code for bad invocation. This means judgeling did not manage to run this program correctly. " + quote(mechanism) + " is probably writen incorrectly. If you think this is not the case, contact judgeling developers.")
                    return PROBLEM_ERROR
                else:
                    logger.error(quote(mechanism.name) + " gave an invalid return code: " + str(result))
                    return PROBLEM_ERROR
                if result != Result.OK:
                    # todo split results depending on retun code, and report correct error messages in summary
                    solution.bad_testcases.append(BadTestResult(testcase, result))
                    logger.info("Input:")
                    print_file_contents(testcase.input)
                    logger.info("Output:")
                    print_file_contents(solution_testcase_out)
                    if mechanism in [Mechanism.checker, Mechanism.cross_check]:
                        logger.info("Referential output:")
                        print_file_contents(testcase.correct_output)
    logger.info("Summary")
    for solution in solutions:
        res_string = ""
        if len(solution.bad_testcases) != 0:
            res_string = "Errors in " + (" ".join([x.str() for x in solution.bad_testcases]))
        else:
            res_string = "OK"
        logger.info(solution.name + " (time " + str(round(solution.timer.get_total(), 3)) + "s, max " + str(round(solution.timer.get_max(), 3)) + "s): " + res_string)
    return SUCCESSFULL_EXECUTION


def get_version() -> str:
    try:
        version = importlib.metadata.version("judgeling")  # installed
    except importlib.metadata.PackageNotFoundError:
        # not installed
        try:
            with open(join(project_root, "pyproject.toml"), "rb") as pyproject_file:  # read from repo
                version = tomllib.load(pyproject_file)["project"]["version"]
        except OSError, tomllib.TOMLDecodeError, KeyError:
            version = "unknown"
    try:
        source_hash = hash_file(realpath(__file__))[:8]  # ties the version to the exact running source
    except OSError:
        source_hash = "unknown"
    return version + "+" + source_hash


# == Formatting ==================================================================


def quote(to_print: object) -> str:
    return "“" + str(to_print) + "”"  # requires UTF-8


# == Structure ===================================================================


class Program:
    """A runnable source file: compiles it (if needed) and executes it with optional I/O redirection and a timeout."""

    def __init__(self, source_file: str):
        self.source_file = source_file
        self.name = bare_filename(source_file)

    def compile(self) -> None:
        self.exe: list[str] = compile_src(self.source_file, build_path)

    def run(
        self,
        args: list[str] | None = None,
        input_file: str | None = None,
        output_file: str | None = None,
        timeout: float | None = None,
    ) -> int:
        if args is None:
            args = []
        command = self.exe + args
        logger.debug("Running: " + quote(self.name) + ", arguments: " + str(command))
        if input_file:
            logger.debug("Input: " + input_file)
        if output_file:
            logger.debug("Output: " + output_file)
        if timeout:
            logger.debug("Timeout: " + str(timeout))
        with (
            open(input_file) if input_file else contextlib.nullcontext() as in_file,
            open(output_file, "w") if output_file else contextlib.nullcontext() as out_file,
        ):
            p = subprocess.Popen(command, stdin=in_file, stdout=out_file)
            try:
                p.wait(timeout)
            except subprocess.TimeoutExpired:
                p.kill()
                raise
            if out_file:
                out_file.flush()
        logger.debug("Program run returns: " + str(p.returncode))
        return p.returncode


class Solution(Program):
    """A user-submitted program under test: adds timing and a record of testcases it failed, plus disqualification."""

    def __init__(self, solution_file: str):
        super().__init__(solution_file)
        self.bad_testcases = []
        self.timer = Timer()
        self.disqualified = False


class Generator(Program):
    """A dataset generator: produces testcase input files into its own data folder, skipping runs via source-hash caching."""

    def __init__(self, generator_file: str):
        super().__init__(generator_file)
        self.data_folder = join(data_path, self.name)

    def generate(self) -> int:
        os.makedirs(self.data_folder, exist_ok=True)
        self.compile()
        hash_src = HashFile(self.data_folder, self.source_file)
        if not args.force_generation and not hash_src.changed():
            logger.verbose("Skipped generation of " + quote(self.name) + " due to non-changed source file.")
            return 0
        logger.verbose("Removing old testcases of " + quote(self.name))
        for filename in os.listdir(self.data_folder):
            file_location = join(self.data_folder, filename)
            if len(filename) > 3 and filename.endswith(conf["out_ext"]):
                os.remove(file_location)
        hash_src.save()
        run_return_code = self.run([str(seed), self.data_folder])
        return run_return_code


class Testcase:
    """A single generated input file within a dataset, along with the paths of its expected output and drawing."""

    def __init__(self, testcase_input_file: str, dataset: Dataset):
        self.input = testcase_input_file
        self.dataset = dataset
        self.name = bare_filename(self.input)
        self.correct_output = join(dirname(testcase_input_file), self.name + conf["out_ext"])
        self.drawing = join(dirname(testcase_input_file), self.name)
        self.valid = True


class Dataset:
    """A named group of testcases produced by one generator, discovered by globbing its data folder."""

    def __init__(self, dataset_folder: str):
        self.name = basename(dataset_folder)
        self.data_folder = join(data_path, self.name)
        self.testcases: list[Testcase] = []

    def get_testcases(self, testcase_regex: str | None) -> None:
        if testcase_regex is None:
            testcase_regex = "*"
        logger.verbose("Globbing " + self.data_folder)
        globbed_testcases = list(glob(join(self.data_folder, testcase_regex + conf["in_ext"])))
        globbed_testcases.sort()
        self.testcases = [Testcase(x, self) for x in globbed_testcases]
        logger.verbose("Found " + str(len(self.testcases)) + " testcases.")


class HashFile:
    """Tracks a source file's content hash on disk so callers can detect whether it changed since the last run."""

    def __init__(self, hash_dir: str, src_file_location: str):
        self.hash_location = join(hash_dir, bare_filename(src_file_location) + ".hash")
        self.new_src_hash = hash_file(src_file_location)
        self.old_src_hash = retrieve_content(self.hash_location)

    def changed(self) -> bool:
        if not conf["enable_cache"]:
            return True
        return self.new_src_hash != self.old_src_hash

    def save(self) -> None:
        save_content(self.hash_location, self.new_src_hash)


class Timer:
    """Measures a solution's CPU time across runs via RUSAGE_CHILDREN, tracking both total and worst-case time."""

    def __init__(self):
        self.total = 0.0
        self.max = 0.0
        self.start_time = 0.0

    def start(self) -> None:
        run_info = self.get_info()
        self.start_time = run_info.ru_utime + run_info.ru_stime

    def stop(self) -> None:
        run_info = self.get_info()
        self.end_time = run_info.ru_utime + run_info.ru_stime
        self.total += self.end_time - self.start_time
        self.max = max(self.max, self.end_time - self.start_time)

    def get_total(self) -> float:
        return self.total

    def get_max(self) -> float:
        return self.max

    def get_info(self) -> resource.struct_rusage:
        return resource.getrusage(resource.RUSAGE_CHILDREN)


class BadTestResult:
    """Pairs a testcase with the non-OK Result a solution got on it, for summary reporting."""

    def __init__(self, testcase: Testcase, result: Result):
        self.testcase = testcase
        self.result = result

    def str(self) -> str:
        return "[" + self.testcase.dataset.name + "/" + self.testcase.name + " " + self.result.short_string + "]"


class Mechanism(enum.Enum):
    """The way a problem checks solution output for correctness."""

    judge = "judge"  # it can decide whether the output is correct or not
    checker = "checker"  # have referential solution and the solutions will be compared to it
    cross_check = "cross_check"  # more user's solutions run against each other


class Result(enum.Enum):
    """Outcome of checking a solution's output on one testcase, with its numeric code and long/short display strings."""

    OK = (0, "OK", "OK")
    WRONG_ANSWER = (1, "WRONG ANSWER", "WA")
    PRESENTATION_ERROR = (2, "PRESENTATION ERROR", "PE")
    TIMELIMIT_EXCEEDED = (3, "TIMELIMIT EXCEEDED", "TLE")
    RUNTIME_ERROR = (4, "RUNTIME ERROR", "RE")
    BAD_INVOCATION = (43, "BAD INVOCATION", "BAD")
    DEFAULT_FLAG = (88, "DEFAULT", "DEF")

    def __init__(self, num: int, long_string: str, short_string: str):
        self.num = num
        self.short_string = short_string
        self.long_string = long_string

    @staticmethod
    def from_num(num: int) -> Result | None:
        for result in Result:
            if num == result.num:
                return result
        return None


# == Configuration ===============================================================


def setup_logging() -> None:
    logging.addLevelName(VERBOSE_LEVEL, "VERBOSE")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def load_configuration(config_file_location: str) -> dict[str, Any]:
    logger.verbose(f"load configuration {config_file_location}")
    try:
        with open(config_file_location) as config_file:
            data = json.load(config_file)
    except FileNotFoundError:
        return {}
    return data


# == File Manipulation ===========================================================


def bare_filename(file_location: str) -> str:
    return splitext(basename(file_location))[0]


def file_extension(file_location: str) -> str:
    return splitext(basename(file_location))[1].lstrip(".")


def get_file_or_folder[T: Program](problem_folder: str, base_name: str, class_name: type[T] = Program) -> list[T]:
    for ext in conf["extensions"]:
        base_file_path = join(problem_folder, base_name + ext)
        if exists(base_file_path):
            return [class_name(base_file_path)]
    base_folder_path = join(problem_folder, base_name)
    if exists(base_folder_path):
        res = []
        for ext in conf["extensions"]:
            res.extend([class_name(x) for x in list(glob(join(base_folder_path, "*" + ext)))])
        return res
    return []


def substitute(template: str, substitutions: dict[str, str]) -> str:
    result = template
    for key, value in substitutions.items():
        result = result.replace("{" + key + "}", value)
    return result


def compile_src(src_file: str, build_path: str) -> list[str]:
    extension = file_extension(src_file)
    interpreters = conf["languages"]["interpreted"]
    if extension in interpreters:
        return [interpreters[extension], src_file]

    base_src_name = bare_filename(src_file)
    exe_file = join(build_path, base_src_name + ".exe")
    language = None
    for candidate in conf["languages"]["compiled"]:
        if extension in candidate["extensions"]:
            language = candidate
            break
    if language is None:
        raise JudgelingException("Unknown source extension " + quote(extension) + " for file " + quote(src_file) + ", and so judgeling does not know how to prepare it to be runnable.")

    # "run" and "artifact" let a language compile to something other than a single
    # directly-executable binary (e.g. Java's javac produces a .class run via `java -cp`).
    substitutions = {
        "flag": "JUDGELING",
        "exe": exe_file,
        "source": src_file,
        "build": build_path,
        "class": base_src_name,
    }
    compilation = shlex.split(substitute(language["command"], substitutions))
    run_command = shlex.split(substitute(language["run"], substitutions)) if "run" in language else [exe_file]
    artifact = substitute(language.get("artifact", "{exe}"), substitutions)

    os.makedirs(build_path, exist_ok=True)
    hash_src = HashFile(build_path, src_file)
    if not hash_src.changed() and exists(artifact):
        logger.verbose("Skipped compilation of " + quote(basename(src_file)) + " due to non-changed source file.")
        return run_command
    logger.info("Compiling: " + quote(basename(src_file)))
    logger.verbose("Compile destination: " + quote(artifact))
    res = subprocess.run(compilation, check=False)
    if res.returncode != 0:
        raise JudgelingException(f"Unable to compile source code: {quote(src_file)}")
    logger.verbose("Compilation return code: " + str(res.returncode))
    hash_src.save()
    return run_command


def find_problem_folder(problem_query: str) -> str | None:
    logger.verbose("Problem id: " + quote(problem_query))
    # search in working directory
    location_path = realpath(join(working_directory, problem_query))
    if exists(location_path):
        logger.debug("Problem found locally in " + quote(location_path))
        return location_path
    # search in default problem repository location
    repository_path_regex = join(problem_search_location, "**", problem_query, conf["def_file"])
    logger.debug("Repository path regex: " + quote(repository_path_regex))
    for def_file in glob(repository_path_regex, recursive=True):
        # todo if found more than one problem definition, raise a warning
        return dirname(def_file)
    return None


def print_file_contents(file_name: str, number_of_lines: int = 20) -> None:
    if conf["logging_level"] >= QUIET_LEVEL:
        return
    with open(file_name, "r") as lines:
        count = 1
        for line in lines:
            if len(line[121:122]) == 0:
                print_line = line
            else:
                print_line = line[:100] + "...<more characters>\n"
            count += 1
            print(print_line, end="")
            if count >= number_of_lines:
                print("...<more lines>")
                break


def retrieve_content(file_location: str) -> str | None:
    try:
        with open(file_location, "r") as content_file:
            data = content_file.read()
            return data
    except FileNotFoundError:
        pass
    return None


def save_content(file_location: str, content: str) -> None:
    with open(file_location, "w+") as content_file:
        content_file.write(content)


def hash_file(file_location: str) -> str:
    BUF_SIZE = pow(2, 16)  # reads data in 64kb chunks
    sha1 = hashlib.sha1()
    with open(file_location, "rb") as content_file:
        while True:
            data = content_file.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    logger.debug("Hashed " + quote(file_location) + " into " + quote(sha1.hexdigest()))
    return sha1.hexdigest()


# == Core Script Logic Chunks ====================================================


def determine_checking_mechanism(
    judge: list[Program],
    checker: list[Program],
    referential_solutions: list[Solution],
    solutions: list[Solution],
) -> Mechanism | None:
    if checker:
        if referential_solutions:
            return Mechanism.checker
        if solutions and len(solutions) >= 2:
            return Mechanism.cross_check
    if judge:
        return Mechanism.judge
    return None


def validate_testcases(validators: list[Program], datasets: list[Dataset]) -> bool:
    if validators:
        for validator in validators:
            validator.compile()
        logger.info("Testing validity of testcases")
        for dataset in datasets:
            for testcase in dataset.testcases:
                if validators:
                    for validator in validators:
                        if validator.run([], testcase.input) != 0:
                            logger.error("Testcase " + quote(dataset.name + "/" + testcase.name) + " is INVALID, according to validator " + quote(validator.name))
                            return False
        logger.info("All testcases were validated successfully")
    return True


# == Main invocation =============================================================

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print()
        logger.critical("Manually interrupted!")
