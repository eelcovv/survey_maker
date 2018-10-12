"""
Utility to create a survey

Usage:
    python survey_maker.py survey_settings.yml [--debug]

"""

import argparse
import logging
import os
import platform
import sys

import pandas as pd
import yaml
import yamlloader

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
                        version="{}\nPart of kvk_url_finder version {}".format(
                            os.path.basename(__file__), __version__))
    parser.add_argument('-d', '--debug', help="Print lots of debugging statements",
                        action="store_const", dest="log_level", const=logging.DEBUG,
                        default=logging.INFO)
    parser.add_argument('-v', '--verbose', help="Be verbose", action="store_const",
                        dest="log_level", const=logging.INFO)
    parser.add_argument('--no_silent',  help="Do not suppress the latex output",
                        action="store_false", dest="silent")
    parser.add_argument('--silent',  help="Suppress the latex output",
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
    parser.add_argument("--update_sql_tables", action="store_true",
                        help="Reread the csv file with urls/addresses and update the tables ")
    parser.add_argument("--force_process", action="store_true",
                        help="Force to process company table, even if they have been marked "
                             "as processes")
    parser.add_argument("--pdf", action="store_true", help="Create the pdf output")
    parser.add_argument("--twice", action="store_true", help="Compile two times for the labels")
    parser.add_argument("--clean", action="store_true",
                        help="Clean the latex temp files after processing")
    parser.add_argument("--no_clean", action="store_false",  dest="clean",
                        help="Do not clean the latex temp files after processing")

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
    merge_loggers(_logger, "survey_maker.document")

    _logger.info("{:10s}: {}".format("Running", sys.argv))
    _logger.info("{:10s}: {}".format("Version", __version__))
    _logger.info("{:10s}: {}".format("Directory", os.getcwd()))
    _logger.debug("Debug message")

    return _logger


def main(args_in):
    args, parser = _parse_the_command_line_arguments(args_in)

    # with the global statement line we make sure to change the global variable at the top
    # when settin gup the logger
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
    with open(args.survey_settings, "r") as stream:
        settings = yaml.load(stream=stream, Loader=yamlloader.ordereddict.CLoader)

    general = settings["general"]
    working_directory = general["working_directory"]
    output_directory = general["output_directory"]
    preamble = general["preamble"]

    info_items = general.get("info")

    questionnaire = settings["questionnaire"]

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

        # create the object and do you thing
        SurveyMaker(
            output_directory=output_directory,
            output_file=output_file,
            questionnaire=questionnaire,
            preamble=preamble,
            pdf=args.pdf,
            info_items=info_items,
            n_compile=n_compile,
            silent=args.silent,
            clean=args.clean
        )


def _run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == '__main__':
    _run()
