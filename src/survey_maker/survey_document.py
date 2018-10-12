import string
import time

from cbs_utils.misc import get_logger
from survey_maker.latex_classes import *

QUESTION_TYPES = ["quantity", "choices", "group"]
SPECIAL_KEYS = ("fontsize", "above")

logger = get_logger(__name__)


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

            # we can start with a info block in case that is given in the *general* section of
            # the yaml file
            if info_items is not None:
                self.add_info(info_items, fontsize="normalsize")

            # always add a Data infomation
            self.append(AddInfo(arguments=["Date", time.strftime("%d.%m.%Y")]))

            # now add all the modules with questions
            self.add_all_modules()

    def add_all_modules(self):
        """
        Add all the modules
        """

        for module_key, module_properties in self.questionnaire.items():
            add_this = module_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skipping section {}".format(module_key))
                continue

            logger.info("Adding section {}".format(module_key))

            self.add_module(module_key, module_properties)

    def add_module(self, module_key, module_properties):

        title = module_properties["title"]
        questions = module_properties["questions"]
        info = module_properties.get("info")

        self.append(Section(title=title, label=NoEscape(label_module(module_key))))

        if info is not None:
            # in case a info section is given, at it at the top of the module
            self.add_info(info)

        for key, question_properties in questions.items():
            add_this = question_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skip question {}".format(key))
                continue

            logger.info("Adding question {}".format(key))
            self.add_question(key, question_properties)

    def add_question(self, key, question_properties):

        question = question_properties["question"]
        question_type = question_properties.get("type", "quantity")
        info = question_properties.get("info")
        if info:
            above = info.get("above", False)
        else:
            above = False

        if question_type not in QUESTION_TYPES:
            logger.info("question type {} not yet implemented. Skipping".format(question_type))
            return

        if question_type == "quantity":
            quantity_label = question_properties.get("quantity_label", "")
            if quantity_label != "":
                # append a :  in case the label of the quantity is not empty
                quantity_label += ":"
            label_width = question_properties.get("label_width", self.global_label_width)
            box_width = question_properties.get("box_width", self.global_box_width)
            with self.create(QuantityQuestion(arguments=NoEscape(question))):
                if info is not None and above:
                    self.add_info(info)
                self.add_quantity_question(key,
                                           quantity_label,
                                           label_width=label_width,
                                           box_width=box_width)
        elif question_type == "choices":
            logger.info("Adding a choice question")
            choices = question_properties.get("choices")
            number_of_columns = question_properties.get("number_of_columns", 1)
            with self.create(ChoiceQuestion(options=[number_of_columns],
                                            arguments=NoEscape(question))):
                if info is not None and above:
                    self.add_info(info)
                self.add_choice_question(key, choices)
        elif question_type == "group":
            logger.info("Adding a group question")
            groups = question_properties["groups"]
            choice_lines = question_properties["choicelines"]
            with self.create(ChoiceGroupQuestion(arguments=NoEscape(question))):
                if info is not None and above:
                    self.add_info(info)
                self.add_choice_group_question(key, groups, choice_lines)
        else:
            raise AssertionError("question type not known. Check if type of question {} is one of "
                                 "the following: {} ".format(key, QUESTION_TYPES))

        if info is not None and not above:
            self.add_info(info)

    def add_choice_group_question(self, key, groups, choice_lines):

        for grp in groups:
            self.append(GroupChoice(NoEscape(grp)))

        for cnt, line in enumerate(choice_lines):
            char = string.ascii_lowercase[cnt]
            line_with_char = "\\textbf{" + char + "}) " + line
            self.append(ChoiceLine(NoEscape(line_with_char)))

        self.append(Command("label", NoEscape(label_question(key))))

    def add_info(self, info, fontsize="footnotesize"):
        """
        Add a info block with a nested block it bullet points

        Parameters
        ----------
        info: dict
            A dictionary with the information to add to the info block. See *write_info* for
            a description of the dictionary
        """

        with self.create(InfoEnvironment()):
            self.write_info(info, fontsize=fontsize)

    def write_info(self, info, fontsize="footnotesize", is_item=False, info_above_items=False):
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
                elif key in SPECIAL_KEYS:
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

    def add_choice_question(self, key, choices=None):
        """
        Add a question with choices

        Parameters
        ----------
        key: str
            Key of the question used to create a unique reference label
        choices: list or None
            If None, assume Nee/Ja.
        """
        if choices is None:
            choice_labels = ["Nee", "Ja"]
        else:
            choice_labels = choices

        for choice in choice_labels:
            self.append(ChoiceItem(NoEscape(choice)))

        self.append(Command("label", NoEscape(label_question(key))))

    def add_quantity_question(self, key=None, quantity_label=None, label_width=None,
                              box_width=4):
        """
        A a question with a quantity answer to the document

        Parameters
        ----------
        key: str
        quantity_label: str
        label_width: int
        box_width: fliat

        Returns
        -------

        """
        logger.debug("Adding a quantity question")

        if label_width is None:
            label = quantity_label
        else:
            label = "\\parbox{" + label_width + "}{" + quantity_label + "}"

        self.append(ChoiceItemText(arguments=["1.2em", box_width, NoEscape(label)]))
        self.append(Command("label", NoEscape(label_question(key))))

    def add_percentage_question(self):
        logger.debug("Adding a percentage question")
