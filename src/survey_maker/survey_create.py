# -*- coding: utf-8 -*-
"""
Utility to create a survey

Usage:
    python survey_maker.py survey_settings.yml [--debug]

"""

import sys

import argparse
import logging
import os
import pandas as pd
import re
import subprocess
import yaml
import yamlloader
import collections

from cbs_utils.misc import (create_logger, merge_loggers, Chdir, make_directory)
from survey_maker.engine import SurveyMaker

try:
    from survey_maker import __version__
except ModuleNotFoundError:
    __version__ = "unknown"

# set up global logger
logger: logging.Logger = None


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
    parser.add_argument('--no_silent', help="Do not suppress the latex output",
                        action="store_false", dest="silent")
    parser.add_argument('--silent', help="Suppress the latex output",
                        action="store_true", default=True)
    parser.add_argument('-q', '--quiet', help="Be quiet: no output", action="store_const",
                        dest="log_level", const=logging.WARNING)
    parser.add_argument("--write_log_to_file", action="store_true",
                        help="Write the logging information to file")
    parser.add_argument("--log_file_base", default="log", help="Default name of the logging output")
    parser.add_argument('--log_file_verbose', help="Be verbose to file", action="store_const",
                        dest="log_level_file", const=logging.INFO)
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
    parser.add_argument("--use_cbs_font", action="store_true", default=True,
                        help="Use the cbs font to allow for the euro symbol")
    parser.add_argument("--no_use_cbs_font", action="store_false", dest="use_cbs_font",
                        help="Do not use the cbs font to allow for the euro symbol")
    parser.add_argument("--draft", action="store_true",
                        help="Add a draft stamp to the document. Doesn not work at cbs yet")
    parser.add_argument("--color",
                        help="Define the key of the colorize items which should be treated as"
                             "main color. If this is not given, the first item is taken")

    # parse the command line
    parsed_arguments = parser.parse_args(args)

    return parsed_arguments, parser


def setup_logging(write_log_to_file=False,
                  log_file_base="log",
                  log_level_file=logging.INFO,
                  log_level=None,
                  ):
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Initialise the logging system
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if write_log_to_file:
        # http://stackoverflow.com/questions/29087297/
        # is-there-a-way-to-change-the-filemode-for-a-logger-object-that-is-not-configured
        sys.stderr = open(log_file_base + ".err", 'w')
    else:
        log_file_base = None

    _logger = create_logger(file_log_level=log_level_file,
                            console_log_level=log_level,
                            log_file=log_file_base)

    # with this call we merge the settings of our logger with the logger in the cbs_utils logger
    # so we can control the output
    merge_loggers(_logger, "cbs_utils")
    merge_loggers(_logger, "survey_maker.engine")
    merge_loggers(_logger, "survey_maker.survey_document")

    _logger.info("{:10s}: {}".format("Running", sys.argv))
    _logger.info("{:10s}: {}".format("Version", __version__))
    _logger.info("{:10s}: {}".format("Directory", os.getcwd()))
    _logger.debug("Debug message")

    return _logger


def get_version(preamble):
    """
    Get the current git version of this questionary

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
        survey_version = preamble.get("version", "Unknown")
        logger.info("Overruling with version in yaml file: {}".format(survey_version))
    else:
        survey_version = stat1.decode().strip()
        logger.info("Survey version found: {}".format(stat1.decode()))

    return survey_version


def get_branch(preamble):
    """
    Get the current git version of this questionary

    Returns
    -------
    str:
        current git version
    """
    process = subprocess.Popen(["git", "branch", "--no-color"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stat1, stat2 = process.communicate()
    git_branch = stat1.decode().strip()
    branch_list = git_branch.split("\n")

    survey_branch = preamble.get("version", "Unknown")

    if not branch_list:
        logger.info("No git version found in questionnaire folder. Is it under git control?")
        logger.info("Overruling with version in yaml file: {}".format(survey_branch))
    else:
        for branch in branch_list:
            match = re.match("\*\s(.*)", branch)
            if bool(match):
                survey_branch = match.group(1)
                break

    return survey_branch


def reorganize_colors(colorize_questions, main_color):
    """
    Change the order of the colors

    :param colorize_questions: OrderDitc
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


def main(args_in):
    args, parser = _parse_the_command_line_arguments(args_in)

    # with the global statement line we make sure to change the global variable at the top
    # when setting up the logger
    global logger
    logger = setup_logging(
        write_log_to_file=args.write_log_to_file,
        log_file_base=args.log_file_base,
        log_level_file=args.log_level_file,
        log_level=args.log_level,
    )

    script_name = os.path.basename(sys.argv[0])
    start_time = pd.to_datetime("now")
    message = "Start {script} (v: {version}) at {start_time}:\n{cmd}".format(script=script_name,
                                                                             version=__version__,
                                                                             start_time=start_time,
                                                                             cmd=sys.argv[:])
    logger.info(message)
    # read the yaml file and put the whole structure into a dictionary: *settings*
    logger.info("Reading settings file {}".format(args.survey_settings))
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

    hyphenation = general.get("hyphenation")

    info_items = general.get("info")

    questionnaire = settings["questionnaire"]

    summary = general.get("summary")
    if summary is not None:
        add_summary = summary.get("add_this", True)
        summary_title = summary["title"]
    else:
        add_summary = False
        summary_title = None

    output_file = os.path.splitext(args.survey_settings)[0]

    if args.twice:
        n_compile = 2
    else:
        n_compile = 1

    # create the KvKUrl object, but first move to the workding directory, so everything we do
    # is with respect to this directory
    with Chdir(working_directory) as _:
        # make the directories in case they do not exist yet
        make_directory(output_directory)

        # survey_version = get_version(preamble)
        survey_branch = get_branch(preamble)
        survey_version = get_version(preamble)
        survey_version = survey_branch + "-" + survey_version

        output_file = "_".join([output_file, re.sub("-.*", "", survey_branch)])

        if args.review_references:
            output_file += "_review"

        if args.color:
            output_file += ("_" + args.color)

        # create the object and do you thing
        SurveyMaker(
            output_directory=output_directory,
            output_file=output_file,
            questionnaire=questionnaire,
            hyphenation=hyphenation,
            preamble=preamble,
            pdf=args.pdf,
            info_items=info_items,
            n_compile=n_compile,
            silent=args.silent,
            clean=args.clean,
            survey_version=survey_version,
            colorize_questions=colorize_questions,
            review_references=args.review_references,
            use_cbs_font=args.use_cbs_font,
            draft=args.draft,
            add_summary=add_summary,
            summary_title=summary_title
        )
        logger.info("Done. Goodbye...")


def _run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == '__main__':
    _run()
