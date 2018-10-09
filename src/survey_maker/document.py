from pylatex.base_classes import Environment
from pylatex.package import Package
from pylatex import Document, Section, Subsection, Command
from pylatex.utils import italic, NoEscape

import collections

from cbs_utils.misc import get_logger

QUESTION_TYPES = ["quantity", "percentage"]

logger = get_logger(__name__)


class Questionnaire(Environment):
    escape = False
    content_separator = "\n"


class SurveyDocument(Document):
    def __init__(self,
                 title="Default Title",
                 author="TheAuthor",
                 date=NoEscape(r"\today"),
                 version=1.0,
                 document_options=None,
                 questionnaire=None,
                 ):
        if document_options is None:
            # take the default options if they are not passed to the class
            document_options = ["dutch", "final", "oneside", "a4paper"]

        super().__init__(
            documentclass="sdaps",
            document_options=document_options
        )

        self.preamble.append(Command("title", title))
        self.preamble.append(Command("author", author))
        self.preamble.append(Command("date", date))
        self.preamble.append(Command("makeatletter"))
        self.preamble.append(Command("chead[]", NoEscape(r"\@title\\Version {}".format(version))))
        self.preamble.append(Command("makeatother"))
        self.preamble.append(Command(r"renewcommand\thesection", NoEscape(r"\Alph{section}")))

        self.questionnaire = questionnaire

        with self.create(Questionnaire(options="noinfo")):
            self.add_all_modules()

    def add_all_modules(self):

        for module_key, module_properties in self.questionnaire.items():
            add_this = module_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skipping section {}".format(module_key))
                continue

            logger.info("Adding section {}".format(module_key))

            self.add_module(module_properties)

    def add_module(self, module_properties):

        label = module_properties["label"]
        questions = module_properties["questions"]

        self.append(Section(title=label))

        for key, question_properties in questions.items():
            add_this = question_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skip question {}".format(key))

            logger.info("Adding question {}".format(key))

            self.add_question(question_properties)

    def add_question(self, question_properties):

        label = question_properties["label"]
        question_type = question_properties.get("type", "quantity")

        if question_type not in QUESTION_TYPES:
            logger.info("question type {} not yet implemented. Skipping".format(question_type))
            return

        if question_type == "quantity":
            logger.info("Adding a quantity question")
        elif question_type == "percentage":
            logger.info("Adding a quantity percentage")
        else:
            raise AssertionError("question type not known. This should not happen")
