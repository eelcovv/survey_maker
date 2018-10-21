import string
import time

from pylatex import (Document, Section, Command)
from pylatex.package import Package
from pylatex.utils import NoEscape

from cbs_utils.misc import get_logger
from survey_maker.latex_classes import *

QUESTION_TYPES = ["quantity", "choices", "group", "textbox"]
SPECIAL_KEYS = ("fontsize", "above")

logger = get_logger(__name__)


class SurveyDocument(Document):
    def __init__(self,
                 title="Default Title",
                 author="TheAuthor",
                 survey_version=None,
                 date=NoEscape(r"\today"),
                 document_options=None,
                 questionnaire=None,
                 info_items=None,
                 global_label_width="2.8cm",
                 global_box_width="4",
                 colorize_questions=None
                 ):
        if document_options is None:
            # take the default options if they are not passed to the class
            document_options = ["dutch", "final", "oneside", "a4paper"]

        super().__init__(
            documentclass="sdaps",
            document_options=document_options
        )

        self.preamble.append(Command("title", title))
        self.preamble.append(Command("author", "Version: {}".format(survey_version)))
        self.preamble.append(Command("date", date))
        self.preamble.append(Package("color"))
        self.preamble.append(Package("tocloft"))
        self.preamble.append(Command("makeatletter"))
        self.preamble.append(
            Command("chead[]", NoEscape(r"\@title\\Version {}".format(survey_version))))
        self.preamble.append(
            Command(r"newcommand{\sectionwithlabel}[2]",
                    NoEscape(r"\phantomsection #1\def\@currentlabel{\unexpanded{#1}}\label{#2}")))

        self.preamble.append(Command("makeatother"))
        self.preamble.append(Command(r"newcommand\supscript[1]", NoEscape(r"{$^{\textrm{#1}}$}")))
        self.preamble.append(Command(r"newcommand\subscript[1]", NoEscape(r"{$_{\textrm{#1}}$}")))
        self.preamble.append(Command(r"newcommand\explanation[1]",
                                     NoEscape(r"\newline\footnotesize{\emph{#1}}")))

        # the filbreak makes sure that you do net get a loney header at the bottom of the page
        section_str = r"\filbreak{\sectionwithlabel{\textbf{\emph{#1}}}{#2}}"
        self.preamble.append(Command(r"newcommand\modulesection[2]", NoEscape(section_str)))

        self.preamble.append(Command("setcounter{tocdepth}", "1"))
        self.preamble.append(Command(
            NoEscape(r"addto\captionsdutch{\renewcommand{\contentsname}{\Large\textbf{"
                     r"Modules Vragenlijst}}}")))

        self.questionnaire = questionnaire

        self.global_label_width = global_label_width
        self.global_box_width = global_box_width

        self.append(Command("maketitle"))
        self.append(Command("tableofcontents*"))
        self.append(Command("newpage"))
        self.append(Command("appendix"))

        if colorize_questions is not None:
            self.colorize_color = colorize_questions["color"]
            self.colorize_key = colorize_questions["key"]
            self.colorize_label = colorize_questions["label"]
        else:
            self.colorize_color = None
            self.colorize_key = None
            self.colorize_label = None

        self.preamble.append(Command(
            # this line changes the title of the table of contents
            NoEscape(r"addto\captionsdutch{\renewcommand{\contentsname}{\Large\textbf{"
                     r"Modules Vragenlijst}}}")))

        if self.colorize_color:
            self.preamble.append(Command(NoEscape(r"definecolor{cbsblauw}{RGB}{39, 29, 108}")))
            self.preamble.append(Command(NoEscape(r"definecolor{cbslichtblauw}{RGB}{0, 161, 205}")))
            self.preamble.append(Command(NoEscape(r"definecolor{oranje}{RGB}{243, 146, 0}")))
            self.preamble.append(Command(NoEscape(
                r"definecolor{oranjevergrijsd}{RGB}{206, 124, 0}")))
            self.preamble.append(Command(NoEscape(r"definecolor{rood}{RGB}{233, 76, 10}")))
            self.preamble.append(Command(NoEscape(
                r"definecolor{roodvergrijsd}{RGB}{178, 61, 2}")))
            self.preamble.append(Command(NoEscape(
                r"definecolor{codekleur}{RGB}{88, 88, 88}")))

            # create a new command for setting the color of a single line
            self.preamble.append(Command(r"newcommand\colorline[1]",
                                         NoEscape(r"{{\color{" +
                                                  r"{:}".format(self.colorize_color) +
                                                  r"}{#1}}}")))

            # create a new environment for setting the color in a block
            self.preamble.append(Command(
                r"newenvironment{colorize}{\medskip\bgroup\color{" +
                r"{:}".format(self.colorize_color) +
                r"}}{\egroup\medskip}"))

        with self.create(Questionnaire(options="noinfo")):

            # we can start with a info block in case that is given in the *general* section of
            # the yaml file
            if info_items is not None:
                self.add_info(info_items, fontsize="normalsize")

            # always add a Data information
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

            logger.info("Adding module {}".format(module_key))

            self.append(Command("clearpage"))

            if module_properties.get(self.colorize_key):
                # we have found the key 'colorize_key' (given in the general section as e.g.
                # "small_company". This means the whole module needs to be coloured and also
                # we return the value of small_company. In case this is a string (an not a bool)
                # it is interpreted as a goto reference which needs to be reported.
                goto = module_properties[self.colorize_key]
                with self.create(Colorize()):
                    self.add_module(module_key, module_properties, goto)
            else:
                self.add_module(module_key, module_properties)

    def add_module(self, module_key, module_properties, goto=None):
        """
        Add a module to the document

        Parameters
        ----------
        module_key: str
            The name key of the module. For internal use only
        module_properties: dict
            A dictionary with the properties of the module
        goto:  str or bool
            In case goto is not none, we have requested to colorize this module because we are
            dealing for instance with a moduel which can be skipped for small companies. In case
            this value is a str, it is interpreted as a goto label

        """

        title = module_properties["title"]
        questions = module_properties["questions"]
        info = module_properties.get("info")

        self.append(Section(title=title, label=NoEscape(label_module(module_key))))

        if goto is not None and isinstance(goto, str):
            # A goto string is pased to the module. Prepend a Ga naar label before we start with
            # this module
            if self.colorize_label is not None:
                label = self.colorize_label
                if re.match("^mod", goto):
                    # remove all underscores for mod: reference
                    goto = re.sub("_", "", goto)
                ref_str = f"{label}" + " $\\rightarrow$ Ga naar \\ref{" + goto + "}"
                with self.create(InfoEnvironment()):
                    self.append(Command("emph", NoEscape(ref_str)))

        if info is not None:
            # in case a info section is given, at it at the top of the module
            self.add_info(info)

        color_all_in_section = False

        for key, question_properties in questions.items():

            # the filter is a dictionary with properties defining the condition and redirection
            # in case we want to skip to another question for a certain outcome
            filter_prop = question_properties.get("filter")

            # if a sectiontitle field is given, start a new section title at this question
            section = question_properties.get("section")
            if section:
                goto = section.get(self.colorize_key)
                ref_str = None
                if goto is not None:
                    color_all_in_section = True
                    if re.match("^mod", goto):
                        # remove all underscores for mod: reference
                        goto = re.sub("_", "", goto)
                    if isinstance(goto, str) and self.colorize_label is not None:
                        label = self.colorize_label
                        ref_str = f"{label}" + " $\\rightarrow$ Ga naar \\ref{" + goto + "}"
                else:
                    color_all_in_section = False

                title = section["title"]
                title_label = label_module_section(title)
                self.append(VSpace(NoEscape("\parskip")))

                if color_all_in_section:
                    with self.create(Colorize()):
                        self.append(ModuleSection([NoEscape(title), title_label]))
                        if ref_str is not None:
                            with self.create(InfoEnvironment()):
                                self.append(Command("emph", NoEscape(ref_str)))
                else:
                    self.append(ModuleSection([NoEscape(title), title_label]))
                    if ref_str is not None:
                        with self.create(InfoEnvironment()):
                            self.append(Command("emph", NoEscape(ref_str)))

                info = section.get("info")
                if info is not None:
                    self.append(VSpace(NoEscape("\parskip")))
                    if color_all_in_section:
                        with self.create(Colorize()):
                            self.add_info(info)
                    else:
                        self.add_info(info)

            add_this = question_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skip question {}".format(key))
                continue

            logger.info("Adding question {}".format(key))
            if question_properties.get(self.colorize_key) or color_all_in_section:
                with self.create(Colorize()):
                    self.add_question(key, question_properties, filter_prop)
            else:
                self.add_question(key, question_properties, filter_prop)

    def add_question(self, key, question_properties, filter_prop=None):

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

        logger.debug("Checking quantity_type : {}".format(question_type))
        if question_type == "quantity":
            quantity_label = question_properties.get("quantity_label", "")
            if isinstance(quantity_label, str) and quantity_label != "":
                # append a :  in case the label of the quantity is not empty
                quantity_label += ":"
            box_width = question_properties.get("box_width", self.global_box_width)
            with self.create(QuantityQuestion(arguments=NoEscape(question))):
                if info is not None and above:
                    logger.warning("Above option not possible for quantity question! "
                                   "Put this info box below")
                    above = False
                self.add_quantity_question(key, quantity_label, box_width=box_width)
        elif question_type == "choices":
            logger.debug("Adding a choice question")
            choices = question_properties.get("choices")
            number_of_columns = question_properties.get("number_of_columns", 1)
            with self.create(ChoiceQuestion(options=[number_of_columns],
                                            arguments=NoEscape(question))):
                if info is not None and above:
                    self.add_info(info)
                self.add_choice_question(key, choices, filter_prop)
        elif question_type == "group":
            logger.debug("Adding a group question")
            group_width = question_properties.get("group_width")
            groups = question_properties["groups"]
            choice_lines = question_properties["choicelines"]
            with self.create(ChoiceGroupQuestion(arguments=NoEscape(question))):
                if info is not None and above:
                    self.add_info(info)
                self.add_choice_group_question(key, groups, choice_lines, group_width,filter_prop)
        elif question_type == "textbox":
            text_width = question_properties.get("textbox", "1cm")
            if info is not None and above:
                self.add_info(info)
            self.add_textbox_question(key, question, text_width)
        else:
            raise AssertionError("question type not known. Check if type of question {} is one of "
                                 "the following: {} ".format(key, QUESTION_TYPES))

        if info is not None and not above:
            self.add_info(info)

    def add_textbox_question(self, key, question, text_width=None):
        """
        Add a text box with the question

        Parameters
        ----------
        key
        question
        text_width
        """

        self.append(TextBox(arguments=[text_width, NoEscape(question)]))

        self.append(Command("label", NoEscape(label_question(key))))

    def add_choice_group_question(self, key, groups, choice_lines, group_width=None,
                                  filter_prop=None):

        for group in groups:
            if group_width is not None:
                grp = "\parbox{" + "{}".format(group_width) + r"}{\raggedright " + group + "}"
            else:
                grp = group
            self.append(GroupChoice(NoEscape(grp)))

        if filter_prop is not None:
            condition = filter_prop["condition"]
            redirection_str = self.get_redirection_string_for_filter(filter_prop)
            self.add_info(condition + redirection_str)

        for cnt, line in enumerate(choice_lines):
            char = string.ascii_lowercase[cnt] + ")"
            if re.search("colorline", line):
                # in case we color the line, do the same for the character
                char = "\colorline{" + char + "}"
            line_with_char = "\\textbf{" + char + "} " + line
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
        self.append(VSpace(NoEscape("\parskip")))

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

    @staticmethod
    def get_redirection_string_for_filter(filter_prop, choice=None):
        """
        In case we have a choice in the filter prop, return a redirection string

        Parameters
        ----------
        filter_prop
        choice

        Returns
        -------
        str:
            A string to redirect to a new question

        """
        redirect_str = ""
        if filter_prop is not None:
            if filter_prop["condition"] == choice or choice is None:
                goto = filter_prop["goto"]
                ref_cat = goto.split(":")[0]
                if ref_cat == "quest":
                    category = "vraag"
                elif ref_cat == "mod":
                    category = "module"
                elif ref_cat == "modsec":
                    category = "module sectie"
                else:
                    raise  AssertionError("Only quest and mod are implemented")
                redirect_str = "$\\rightarrow$ Ga naar " + category + " \\ref{" + goto + "}"

        return redirect_str

    def add_choice_question(self, key, choices=None, filter_prop=None):
        """
        Add a question with choices

        Parameters
        ----------
        key: str
            Key of the question used to create a unique reference label
        choices: list or None
            If None, assume Nee/Ja.
        filter_prop: dict or None
            If not None, defines the properties to filter a question
        """
        if choices is None:
            choice_labels = ["Ja", "Nee"]
        else:
            choice_labels = choices

        for cnt, choice in enumerate(choice_labels):

            redirection_str = self.get_redirection_string_for_filter(filter_prop, choice)
            ch_str = choice + redirection_str

            self.append(ChoiceItem(NoEscape(ch_str)))

        self.append(Command("label", NoEscape(label_question(key))))

    def add_quantity_question(self, key=None, quantity_label=None, label_width=None,
                              box_width=4):
        """
        A a question with a quantity answer to the document

        Parameters
        ----------
        key: str
        quantity_label: str or list
        label_width: int
        box_width: fliat

        Returns
        -------

        """
        logger.debug("Adding a quantity question")

        if isinstance(quantity_label, str):
            label_list = [quantity_label]
        else:
            label_list = quantity_label

        if label_width is None:
            width = self.global_label_width
        else:
            width = label_width

        for cnt, label in enumerate(label_list):
            if isinstance(quantity_label, list):
                char = string.ascii_lowercase[cnt]
                label_with_char = "\\textbf{" + char + "}) " + label
                # treat as a list of labels
                lbl = "\\parbox{0.92\\textwidth}{" + label_with_char + "}"
            else:
                if label_width is not None:
                    lbl = "\\parbox{" + "{}".format(width) + "}{" + label + "}"
                else:
                    lbl = label

            self.append(ChoiceItemText(arguments=["1.2em", box_width, NoEscape(lbl)]))

        self.append(Command("label", NoEscape(label_question(key))))
