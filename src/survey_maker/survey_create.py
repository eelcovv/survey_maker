"""
Utility to create a survey

Usage:
    python survey_maker.py survey_settings.yml [--debug]

"""

import argparse
import collections
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml
import yamlloader

from survey_maker.engine import SurveyMaker
from survey_maker.utils import Chdir

try:
    from survey_maker import __version__
except ModuleNotFoundError:
    __version__ = "unknown"

logger = logging.getLogger()


def _parse_the_command_line_arguments(args):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # parse the command line to set some options2
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    parser = argparse.ArgumentParser(description='Create a survey  from a yaml file',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # set the verbosity level command line arguments
    # mandatory arguments
    parser.add_argument("survey_settings", action="store",
                        help="The yaml survey input file")
    parser.add_argument("--version", help="Show the current version", action="version",
                        version=f"{__version__}")
    parser.add_argument('-d', '--debug', help="Print lots of debugging statements",
                        action="store_const", dest="log_level", const=logging.DEBUG,
                        default=logging.INFO)
    parser.add_argument('-v', '--verbose', help="Be verbose", action="store_const",
                        dest="log_level", const=logging.INFO)
    parser.add_argument('--use_latexmk', help="Use latexmk to compile", action="store_true",
                        default=True)
    parser.add_argument('--not_latexmk', help="Do not use latexmk to compile",
                        action="store_false", dest='use_latexmk')
    parser.add_argument('--compiler', help="Compiler to use", default="xelatex")
    parser.add_argument('--compiler_args', help="Compiler arguments")
    parser.add_argument('--no_silent', help="Do not suppress the latex output",
                        action="store_false", dest="silent")
    parser.add_argument('--silent', help="Suppress the latex output",
                        action="store_true", default=True)
    parser.add_argument('-q', '--quiet', help="Be quiet: no output", action="store_const",
                        dest="log_level", const=logging.WARNING)
    parser.add_argument("--write_log_to_file", action="store_true",
                        help="Write the logging information to file")
    parser.add_argument("--log_file_base", default="log", help="Default name of the logging output")
    parser.add_argument('--log_file_debug', help="Be very verbose to file", action="store_const",
                        dest="log_level_file", const=logging.DEBUG)
    parser.add_argument('--log_file_verbose', help="Be verbose to file", action="store_const",
                        dest="log_level_file", const=logging.INFO, default=logging.INFO)
    parser.add_argument('--log_file_quiet', help="Be quiet: no output to file",
                        action="store_const", dest="log_level_file", const=logging.WARNING)
    parser.add_argument("--pdf", action="store_true", help="Create the pdf output", default=True)
    parser.add_argument("--no_pdf", action="store_false", help="Do not create the pdf output",
                        dest="pdf")
    parser.add_argument("--twice", action="store_true", help="Compile two times for the labels")
    parser.add_argument("--clean", action="store_true",
                        help="Clean the latex temp files after processing")
    parser.add_argument("--no_clean", action="store_false", dest="clean",
                        help="Do not clean the latex temp files after processing")
    parser.add_argument("--review_references", action="store_true",
                        help="Add the references to the original questions for review purpose only")
    parser.add_argument("--prune_colors", action="store_true",
                        help="Only add the questions of the defined colors")
    parser.add_argument("--dvz_references", action="store_true", help="Add the remarks to DVZ")
    parser.add_argument("--use_cbs_font", action="store_true", default=True,
                        help="Use the cbs font to allow for the euro symbol")
    parser.add_argument("--no_use_cbs_font", action="store_false", dest="use_cbs_font",
                        help="Do not use the cbs font to allow for the euro symbol")
    parser.add_argument("--draft", action="store_true",
                        help="Add a draft stamp to the document. Doesn not work at cbs yet")
    parser.add_argument("--color",
                        help="Define the key of the colorize items which should be treated as"
                             "main color. If this is not given, the first item is taken")
    parser.add_argument("--no_color",
                        help="Turn of the color  defined by this key")
    parser.add_argument("--no_git_branch", action="store_true",
                        help="Do not add the git branch name to the version")
    parser.add_argument("--no_git_version", action="store_true",
                        help="Do not use the git version name to the version")
    parser.add_argument("--no_date", action="store_true",
                        help="Do not add a date to the document")
    parser.add_argument("--english", action="store_true",
                        help="Use English defaults")
    parser.add_argument("--no_author", action="store_true",
                        help="Do not print out the author in the pdf file")

    # parse the command line
    parsed_arguments = parser.parse_args(args)

    return parsed_arguments, parser


def get_version(default_version=None):
    """
    Get the current git version of this questionnaire

    Returns
    -------
    str:
        current git version
    """
    process = subprocess.Popen(["git", "describe", "--tags"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stat1, stat2 = process.communicate()
    if stat1.decode() == "":
        logger.info("No git version found in questionnaire folder. Is it under git control?")
        survey_version = default_version
        logger.info("Overruling with version in yaml file: {}".format(survey_version))
    else:
        survey_version = stat1.decode().strip()
        logger.info("Survey version found: {}".format(stat1.decode()))

    return survey_version


def get_branch(default_branch=None):
    """
    Get the current git version of this questionary

    Parameters
    ----------
    default_branch: str
        De default naam die we aan het branch geven als we niks kunnen vinden

    Returns
    -------
    str:
        current branch version
    """
    process = subprocess.Popen(["git", "branch", "--no-color"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stat1, stat2 = process.communicate()
    git_branch = stat1.decode().strip()
    branch_list = git_branch.split("\n")

    survey_branch = default_branch

    if not branch_list:
        logger.info("No git version found in questionnaire folder. Is it under git control?")
        logger.info("Overruling with version in yaml file: {}".format(survey_branch))
    else:
        for branch in branch_list:
            # deze regex matcht de actieve branch (met de * voor de branch naam)
            match = re.match("\*\s(.*)", branch)
            if bool(match):
                survey_branch = match.group(1)
                break

    return survey_branch


def reorganize_colors(colorize_questions, main_color):
    """
    Change the order of the colors

    :param colorize_questions: OrderedDict
    :param main_color: Name of the main color
    :return: New OrderedDict
    """
    new_colorize_order = collections.OrderedDict()
    try:
        color_properties = colorize_questions[main_color]
    except KeyError:
        raise ValueError("Color '{}' was not defined in the colorize properties.\nPlease pick "
                         "one of: {}".format(main_color, list(colorize_questions.keys())))
    else:
        logger.debug("Adding colorize {}".format(main_color))
        new_colorize_order[main_color] = color_properties
        new_colorize_order[main_color]["add_this"] = True
        new_colorize_order[main_color]["apply_color"] = True
        for color_key, color_properties in colorize_questions.items():
            if color_key == main_color:
                continue
            else:
                logger.debug("Adding colorize {}".format(color_key))
                new_colorize_order[color_key] = color_properties

    return new_colorize_order


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "%(levelname)-8s [%(filename)s:%(lineno)4d] %(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args_in):
    args, parser = _parse_the_command_line_arguments(args_in)

    setup_logging(loglevel=args.log_level)

    script_name = os.path.basename(sys.argv[0])
    start_time = pd.Timestamp.now()
    message = "Start {script} (v: {version}) at {start_time}:\n{cmd}".format(script=script_name,
                                                                             version=__version__,
                                                                             start_time=start_time,
                                                                             cmd=sys.argv[:])
    logger.info(message)
    # read the yaml file and put the whole structure into a dictionary: *settings*
    logger.info("Reading settings file {}".format(args.survey_settings))
    logger.debug("Current location: {}".format(os.getcwd()))
    with open(args.survey_settings, "r", encoding="utf-8") as stream:
        settings = yaml.load(stream=stream, Loader=yamlloader.ordereddict.CLoader)

    general = settings["general"]
    working_directory = general.get("working_directory", ".")
    output_directory = general.get("output_directory", ".")
    preamble = general["preamble"]
    colorize_questions = general.get("colorize_questions")

    if colorize_questions is not None and args.color is not None:
        logger.info("Setting {} as main color".format(args.color))
        colorize_questions = reorganize_colors(colorize_questions, args.color)

    if colorize_questions is not None and args.no_color is not None:
        try:
            colorize_questions[args.no_color]["add_this"] = False
        except KeyError as err:
            logger.warning(f"Could not find definition of color you are trying to turn of: "
                           f"{args.no_color}")
            raise KeyError(err)

    hyphenation = general.get("hyphenation")

    info_items = general.get("info")
    info_items_per_color = general.get("info_per_color")

    questionnaire = settings["questionnaire"]

    summary = general.get("summary")
    if summary is not None:
        add_summary = summary.get("add_this", True)
        summary_title = summary["title"]
    else:
        add_summary = False
        summary_title = None

    output_file = os.path.splitext(args.survey_settings)[0]

    compiler_args = None
    if args.use_latexmk:
        compiler = "latexmk"
        if args.compiler == "xelatex":
            compiler_args = ["-xelatex"]

    else:
        compiler = args.compiler

    n_compile = 1
    if args.twice:
        if args.use_latexmk:
            logger.warning("Twice is not used for latexmk compiler")
        else:
            n_compile = 2

    # create the KvKUrl object, but first move to the working directory, so everything we do
    # is with respect to this directory
    with Chdir(working_directory) as _:
        # make the directories in case they do not exist yet
        Path(output_directory).mkdir(exist_ok=True)

        if not args.no_git_version:
            survey_version = preamble.get("version")
            if survey_version is None:
                survey_version = get_version()
        else:
            survey_version = None

        if not args.no_git_branch:
            # first choice: get the branch name from the input file
            survey_branch = preamble.get("branch")
            if survey_branch is None:
                # no branch name in input file, try to get it from the git repo
                survey_branch = get_branch()
            if survey_branch is not None:
                # underscores give problems in latex, so replace with dash
                survey_branch = survey_branch.replace("_", "")
                # only add the branch name if we have o ne
                output_file = "_".join([output_file, re.sub("-.*", "", survey_branch)])
                if survey_version is not None:
                    survey_version = survey_branch + "-" + survey_version

        if survey_version is not None:
            version = re.sub("^-", "", re.sub(survey_branch, "", survey_version))
            output_file = "_".join([output_file, "v" + re.sub("-.*", "", version)])

        if not args.no_date:
            date = preamble.get("date")
        else:
            # in case the no that option is given, do not add a date
            date = ""

        if args.review_references:
            output_file += "_review"

        if args.dvz_references:
            output_file += "_dvz"

        if args.color:
            output_file += ("_" + args.color)

        # create the object and do your thing
        SurveyMaker(
            output_directory=output_directory,
            output_file=output_file,
            questionnaire=questionnaire,
            hyphenation=hyphenation,
            preamble=preamble,
            pdf=args.pdf,
            info_items=info_items,
            info_items_per_color=info_items_per_color,
            compiler=compiler,
            compiler_args=compiler_args,
            n_compile=n_compile,
            silent=args.silent,
            clean=args.clean,
            survey_version=survey_version,
            survey_date=date,
            colorize_questions=colorize_questions,
            review_references=args.review_references,
            dvz_references=args.dvz_references,
            prune_colors=args.prune_colors,
            use_cbs_font=args.use_cbs_font,
            draft=args.draft,
            add_summary=add_summary,
            summary_title=summary_title,
            english=args.english,
            no_author=args.no_author

        )
        logger.info("Done. Goodbye...")


def _run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == '__main__':
    _run()
