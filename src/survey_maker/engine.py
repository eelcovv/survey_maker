# -*- coding: utf-8 -*-
from pathlib import Path
from shutil import copy2
from pkgutil import get_data

from cbs_utils.misc import get_logger
from survey_maker.survey_document import SurveyDocument

try:
    from survey_maker import __version__
except ModuleNotFoundError:
    __version__ = "unknown"

TEX_STY_FILES = ["sdaps.cls", "code128.tex"]

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
                 hyphenation=None,
                 preamble=None,
                 info_items=None,
                 pdf=False,
                 n_compile=1,
                 silent=True,
                 compiler="xelatex",
                 clean=True,
                 survey_version=None,
                 survey_date=None,
                 colorize_questions=None,
                 review_references=False,
                 use_cbs_font=True,
                 draft=False,
                 add_summary=True,
                 summary_title="Summary"
                 ):

        logger.info("Starting Survey Maker")
        logger.debug("With debugging on")

        self.output_directory = Path(output_directory)

        self.output_file = self.output_directory / output_file

        for sty_file in TEX_STY_FILES:
            dest_style_file = self.output_directory / sty_file
            if not dest_style_file.exists():
                logger.info(f"Copying tex style file {sty_file} to {dest_style_file}")
                data = get_data("survey_maker", sty_file)
                with open(dest_style_file, "wb") as fp:
                    fp.write(data)
            else:
                logger.debug("Latex sty {} already present in {}".format(sty_file, dest_style_file))

        self.document = SurveyDocument(
            questionnaire=questionnaire,
            title=preamble.get("title"),
            author=preamble.get("author"),
            hyphenation=hyphenation,
            survey_version=survey_version,
            survey_date=survey_date,
            info_items=info_items,
            colorize_questions=colorize_questions,
            review_references=review_references,
            use_cbs_font=use_cbs_font,
            draft=draft,
            add_summary=add_summary,
            summary_title=summary_title
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

                logger.info("Writing Survey to {}.pdf ({}/{})".format(
                    self.output_file.name, cnt + 1, n_compile))

                self.document.generate_pdf(filepath=self.output_file.name,
                                           clean_tex=False,
                                           clean=clean_latex,
                                           compiler=compiler,
                                           silent=silent
                                           )
        else:
            logger.info("Writing Survey to {}.tex".format(self.output_file.name))
            # only create the tex document without compiling the source
            self.document.generate_tex(filepath=self.output_file.name)
