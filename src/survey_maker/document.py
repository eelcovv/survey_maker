from pylatex.base_classes import Environment, CommandBase
from pylatex.package import Package
from pylatex import Document, Section, Subsection, Command
from pylatex.utils import italic, NoEscape
import time
import re

from cbs_utils.misc import get_logger

QUESTION_TYPES = ["quantity", "percentage"]

logger = get_logger(__name__)


def label_question(key):
    """
    Create a label to use for referring to a question

    Parameters
    ----------
    key: str
        Name of the label

    Returns
    -------
    str:
        quest:key
    """
    return ":".join(["quest", key])


def label_module(key):
    """
    Create a label to use for referring to a module

    Parameters
    ----------
    key: str
        Name of the label

    Returns
    -------
    str:
        mod:key, where all the _ are removed from the key as this is also done by Label
    """
    return re.sub("_", "", ":".join(["mod", key]))


class Itemize(Environment):
    escape = False
    content_separator = "\n"


class InfoItems(Environment):
    _latex_name = "info"


class Questionnaire(Environment):
    """
    The main environment questionnairy which encapsulates all the questions
    """
    _latex_name = "questionnaire"
    escape = False
    content_separator = "\n"


class QuantityQuestion(Environment):
    _latex_name = "markgroup"
    escape = False
    content_separator = "\n"


class ChoiseItemText(CommandBase):
    _latex_name = "choiceitemtext"
    escape = False
    content_separator = "\n"


class AddInfo(CommandBase):
    _latex_name = "addinfo"


class SurveyDocument(Document):
    def __init__(self,
                 title="Default Title",
                 author="TheAuthor",
                 date=NoEscape(r"\today"),
                 version=1.0,
                 document_options=None,
                 questionnaire=None,
                 info_items=None
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

            if info_items is not None:
                self.add_info_items(info_items)

            self.append(AddInfo(arguments=["Date", time.strftime("%d.%m.%Y")]))

            self.add_all_modules()

    def add_info_items(self, information):
        with self.create(InfoItems()):
            if isinstance(information, list) :
                with self.create(Itemize()):
                    for item in information:
                        self.append(Command("item", NoEscape(item)))
            else:
                self.append(Command("footnotesize", NoEscape(information)))

    def add_all_modules(self):

        for module_key, module_properties in self.questionnaire.items():
            add_this = module_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skipping section {}".format(module_key))
                continue

            logger.info("Adding section {}".format(module_key))

            self.add_module(module_key, module_properties)

    def add_module(self, module_key, module_properties):

        label = module_properties["label"]
        questions = module_properties["questions"]
        info = module_properties.get("info")

        self.append(Section(title=label, label=NoEscape(label_module(module_key))))

        if info is not None:
            self.add_info_items(information=info)

        for key, question_properties in questions.items():
            add_this = question_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skip question {}".format(key))

            logger.info("Adding question {}".format(key))

            self.add_question(key, question_properties)

    def add_question(self, key, question_properties):

        question = question_properties["label"]
        question_type = question_properties.get("type", "quantity")

        if question_type not in QUESTION_TYPES:
            logger.info("question type {} not yet implemented. Skipping".format(question_type))
            return

        if question_type == "quantity":
            quantity_label = question_properties.get("quantity_label", "Aantal") + ":"
            with self.create(QuantityQuestion(arguments=NoEscape(question))):
                self.add_quantity_question(key, quantity_label)
        elif question_type == "percentage":
            logger.info("Adding a quantity percentage")
        else:
            raise AssertionError("question type not known. This should not happen")

    def add_quantity_question(self, key=None, quantity_label=None):
        logger.debug("Adding a quantity question")

        self.append(ChoiseItemText(arguments=["1.2em", 4, quantity_label]))
        self.append(Command("label", NoEscape(label_question(key))))

    def add_percentage_question(self):
        logger.debug("Adding a percentage question")


