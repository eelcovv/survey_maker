# -*- coding: utf-8 -*-
from pathlib import Path

from cbs_utils.misc import get_logger
from survey_maker.survey_document import SurveyDocument

try:
    from survey_maker import __version__
except ModuleNotFoundError:
    __version__ = "unknown"

__author__ = "Eelco van Vliet"
__copyright__ = "CBS"
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
                 n_compile=1,
                 silent=True,
                 compiler="xelatex",
                 clean=True,
                 survey_version=None,
                 colorize_questions=None,
                 review_references=False,
                 use_cbs_font=True
                 ):

        logger.info("Starting Survey Maker")

        self.output_directory = Path(output_directory)

        self.output_file = self.output_directory / output_file

        self.document = SurveyDocument(
            questionnaire=questionnaire,
            title=preamble.get("title"),
            author=preamble.get("author"),
            survey_version=survey_version,
            info_items=info_items,
            colorize_questions=colorize_questions,
            review_references=review_references,
            use_cbs_font=use_cbs_font
        )

        if pdf:
            # create the pdf file for this document
            for cnt in range(n_compile):
                # in case the --twice comment line option is given, n_compile = 2, such that we
                # can correctly create the labels in one go
                clean_latex = clean
                if clean and n_compile == 2 and cnt == 0:
                    # in case we want to clean the latex file, but compile two times (because the
                    # twice argument is given, do not clean the first time, so that we can get the
                    # labels right
                    clean_latex = False

                self.document.generate_pdf(filepath=self.output_file.name,
                                           clean_tex=False,
                                           clean=clean_latex,
                                           compiler=compiler,
                                           silent=silent
                                           )
        else:
            # only create the tex document without compiling the source
            self.document.generate_tex(filepath=self.output_file.name)
