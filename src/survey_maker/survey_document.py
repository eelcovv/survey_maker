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
        mod:key, where all the underscores are removed from the key as this is also done by Label
    """
    return re.sub("_", "", ":".join(["mod", key]))


class Itemize(Environment):
    escape = False
    content_separator = "\n"


class InfoEnvironment(Environment):
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
                 info_items=None,
                 global_label_width="2.8cm",
                 global_box_width="4"
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

        self.global_label_width = global_label_width
        self.global_box_width = global_box_width

        with self.create(Questionnaire(options="noinfo")):

            if info_items is not None:
                self.add_info_items(info_items)

            self.append(AddInfo(arguments=["Date", time.strftime("%d.%m.%Y")]))

            self.add_all_modules()

    def add_info_items(self, information):
        """
        Add a list of items as a bullet list to the document

        Parameters
        ----------
        information: str or list
            In case it is a string, add just a text, if it is a list, add a bullet list
        """
        with self.create(InfoEnvironment()):
            if isinstance(information, list):
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
                continue

            logger.info("Adding question {}".format(key))

            self.add_question(key, question_properties)

    def add_question(self, key, question_properties):

        question = question_properties["label"]
        question_type = question_properties.get("type", "quantity")
        info = question_properties.get("info")

        if question_type not in QUESTION_TYPES:
            logger.info("question type {} not yet implemented. Skipping".format(question_type))
            return

        if question_type == "quantity":
            quantity_label = question_properties.get("quantity_label", "Aantal") + ":"
            label_width = question_properties.get("label_width", self.global_label_width)
            box_width = question_properties.get("box_width", self.global_box_width)
            with self.create(QuantityQuestion(arguments=NoEscape(question))):
                self.add_quantity_question(key,
                                           quantity_label,
                                           label_width=label_width,
                                           box_width=box_width)
        elif question_type == "percentage":
            logger.info("Adding a quantity percentage")
        else:
            raise AssertionError("question type not known. This should not happen")

        if info is not None:
            self.add_info(info)

    def add_info(self, info, fontsize="footnotesize"):

        with self.create(InfoEnvironment()):
            self.write_info(info, fontsize)

    def write_info(self, info, fontsize="footnotesize", is_item=False):
        """
        A recursive method to create a nested block of text with itemizes

        Parameters
        ----------
        info: OrderDict
            A dictionary with the information we want to add to a info block
        fontsize: str
            The size of the font
        is_item: bool
            If true,  strings are items of a itemize environment and need a ítem command

        The *info* dictionary has the following format::

            info:
              fontsize: this field is not plotted by used to set the font size of the info block
              title: The title added outside the itemize block
              items: # either a list of a dict can follow the items.
                wel:
                  title: The first item in our main bullet list
                  items:
                  - subitem11 # these items are added as a list
                  - subitem12
                niet:
                  title: The second item in our main bullet list
                  items:
                  - subitem21
                  - subitem22

        So the *info* is the main dictionary which is passed to the routine. Then, a *title* is
        plotted above the main itemize block. Then we can add the items, which can be again a
        dictionary with a title, and a new item field containing a list.

        The routine below is recursively calling itself so that in principle the items can be
        nested
        """

        try:
            # in case
            fsize = info["fontsize"]
        except (KeyError, TypeError):
            fsize = fontsize

        if isinstance(info, str):
            # info is a string. Create a plot command
            text = Command(fontsize, NoEscape(info))
            if is_item:
                # in case the *is_item* flag is true, preprend
                self.append(Command("item", text))
            else:
                # it is not a item, which is only the case for the first title string
                self.append(text)
        elif isinstance(info, dict):
            # we have a dict, loop over its keys and make a recursive call for each item
            for key, value in info.items():
                if key == "title":
                    # we the key is a title field. Create a entry for this by recursively calling
                    # this function again. If this is the first entry, is_item is false and
                    # therefore the title is put outside the itemize block without a item
                    self.write_info(value, is_item=is_item, fontsize=fsize)
                    # after the first call, the is_item flag is set to true, which means that all
                    # the other titles are preceded with the \items
                    is_item = True
                elif key == "items":
                    # if we find a items key, open a new itemize block add call this function
                    # recursively with the list or dict
                    with self.create(Itemize()):
                        self.write_info(value, is_item=True, fontsize=fsize)
                elif key == "fontsize":
                    # skip the fontsize key field
                    continue
                else:
                    # the other values  are just added the the cursive call
                    self.write_info(value, is_item=is_item, fontsize=fsize)
        elif isinstance(info, list):
            # we have a list. Just added all the items to the itemize environment
            for item in info:
                self.write_info(item, is_item=True, fontsize=fsize)
        else:
            raise AssertionError("Only valid for str, dict or list")

    def add_quantity_question(self, key=None, quantity_label=None, label_width=None,
                              box_width=4):
        logger.debug("Adding a quantity question")

        if label_width is None:
            label = quantity_label
        else:
            label = "\\parbox{" + label_width + "}{" + quantity_label + "}"

        self.append(ChoiseItemText(arguments=["1.2em", box_width, NoEscape(label)]))
        self.append(Command("label", NoEscape(label_question(key))))

    def add_percentage_question(self):
        logger.debug("Adding a percentage question")
