from pylatex import Document, Section, Subsection, Command
from pylatex.utils import italic, NoEscape
import os
import re
import sys
from pathlib import Path

from survey_maker.document import SurveyDocument

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
                 questionnaire=None,
                 preamble=None,
                 info_items=None,
                 pdf=False,
                 n_compile=1
                 ):

        logger.info("Starting Survey Maker")

        self.output_directory = Path(output_directory)

        self.output_file = self.output_directory / output_file

        self.document = SurveyDocument(
            questionnaire=questionnaire,
            title=preamble.get("title"),
            author=preamble.get("author"),
            version=preamble.get("version"),
            info_items=info_items
        )

        if pdf:
            for cnt in range(n_compile):
                if n_compile == 2 and cnt == 0:
                    clean = False
                else:
                    clean = True

                self.document.generate_pdf(filepath=self.output_file.name,
                                           clean_tex=False,
                                           clean=clean,
                                           compiler="xelatex",
                                           silent=False
                                           )
        else:
            self.document.generate_tex(filepath=self.output_file.name)

