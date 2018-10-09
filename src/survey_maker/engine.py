import os
import re
import sys
from pathlib import Path

import survey_make

from cbs_utils.misc import get_logger

try:
    from survey_maker import __version__
except ModuleNotFoundError:
    __version__ = "unknown"

try:
    # if profile exist, it means we are running kernprof to time all the lines of the functions
    # decorated with #@profile
    # noinspection PyUnboundLocalVariable
    isinstance(profile, object)
except NameError:
    # in case this fails, we add the profile decorator to the builtins such that it does
    # not raise an error.
    import line_profiler
    import builtins

    profile = line_profiler.LineProfiler()
    builtins.__dict__["profile"] = profile

__author__ = "Eelco van Vliet"
__copyright__ = "Eelco van Vliet"
__license__ = "mit"

logger = get_logger(__name__)


class SurveyMaker(object):
    """
    Class to create a survey

    Parameters
    ----------
    """

    def __init__(self,
                 output_directory=None,
                 output_file=None,
                 questionaire=None,
                 questions=None,
                ):

        logger.info("Starting Survey Maker")

        self.output_directory = Path(output_directory)

        self.output_file = self.output_directory / output_file

        self.questionaire = questionaire
        self.questions = questions

        self.document = pl.Document(
            default_filepath=self.output_file.name)

        self.create_latex()

        self.document.generate_tex()

    def create_latex(self):
        """
        Create the latex ouput
        """

        logger.info("Writing survey to {}".format(self.output_file))


