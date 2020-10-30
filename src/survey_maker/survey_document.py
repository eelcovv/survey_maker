# -*- coding: utf-8 -*-
import collections
import string
import time

from pylatex import (Document, Section, Command)
from pylatex.package import Package
from pylatex.utils import NoEscape

from cbs_utils.misc import get_logger
from survey_maker.latex_classes import *

QUESTION_TYPES = ["quantity", "choices", "group", "textbox", "range", "rangegroup"]
SPECIAL_KEYS = ("fontsize", "above")

COUNT_QUST_KEY = "questions"
COUNT_MODULES_KEY = "modules"
COUNT_QUST_TOTAL_KEY = "questions_incl_choices"

DVZ_KEY = "dvz"

logger = get_logger(__name__)


class SurveyDocument(Document):
    """
    Create the preamble of the latex document and add all the module

    Parameters
    ----------
    title: str
        Title of the survey. Default = "Default Title"
    author: str
        Author of the survey. Default = "TheAuthor"
    survey_version: str
        Add a version to the document. Default = None (no version added)
    survey_date: str
        Date added to the document
    hyphenation: list
        List of string with hyphenations imposed in LaTeX
    document_options:  list or None
        Add these option the the sdaps class
    questionnaire: dict
        Dictionary with the total questionnaire contents as obtained from the yaml file
    info_items: dict or None
        Add some information to the seconds page of the questionnaire
    global_label_width: str
        Global settings of the width of all the labels
    global_box_width: str
        Global settings of the width of all the boxes
    colorize_questions: dict
        Give the colorize options
    add_summary: bool
        If true, add a summary add the end of the questionnaire
    summary_title: str
        The title of the summary added at the end of the questionnaire
    review_references: bool
        If true, add a link to all the references of the questions
    use_cbs_font: bool
        Use the CBS font instead of the default font
    draft: bool
        If true, add a draft stamp
    """

    def __init__(self,
                 title="Default Title",
                 author="TheAuthor",
                 survey_version=None,
                 survey_date=None,
                 hyphenation=None,
                 document_options=None,
                 questionnaire=None,
                 info_items=None,
                 global_label_width="2.8cm",
                 global_box_width="4",
                 colorize_questions=None,
                 add_summary=True,
                 summary_title="Summary",
                 review_references=False,
                 dvz_references=False,
                 use_cbs_font=True,
                 draft=False
                 ):

        if document_options is None:
            # take the default options if they are not passed to the class
            document_options = ["dutch", "final", "oneside", "a4paper"]

        # with this trick we can preceed the documentclass command with the PassOptionsToPackage
        # command such that we can add some more color definitions to xcolor.
        # The construciton with scrlfile replacing the srcpage2 is needed because scrpage2 is
        # obsoleter and not include in the miktex distribution anymore.
        # also de expression RequirePackage{ifpdf} are include to suppressed all the warnings
        command = Command(r"PassOptionsToPackage{dvipsnames,usenames}{xcolor}"
                          r"\RequirePackage{scrlfile}"
                          r"\ReplacePackage{scrpage2}{scrlayer-scrpage}"
                          r"\RequirePackage{ifpdf}"
                          r"\RequirePackage{ifluatex}"
                          r"\documentclass",
                          options=document_options,
                          arguments=["sdaps"])
        # noinspection PyTypeChecker
        super().__init__(documentclass=command, inputenc=None, fontenc=None)

        # lastpage and fontenc are defined twice. Remove them from the preamble
        self.remove_packages(['lastpage'])

        self.add_summary = add_summary
        self.summary_title = summary_title
        self.review_references = review_references
        self.dvz_references = dvz_references

        # this part comes from the cbsreport class to make sure we have the same font
        # more importantly, under windows it allows to have a proper euro font
        if use_cbs_font:
            ligatures = NoEscape(r"Ligatures={Common,TeX}")
            numbers = NoEscape(r"Numbers={Lining}")
            scale = NoEscape(r"Scale=MatchLowercase")
            self.preamble.append(Package("fontspec"))
            self.preamble.append(Command("setmainfont", "Calibri",
                                         options=[ligatures, numbers]))
            self.preamble.append(Command("setmonofont", "Consolas",
                                         options=[ligatures, scale]))
            self.preamble.append(Command("setsansfont", "Cambria", options=[ligatures]))
            self.preamble.append(Command(r"newfontfamily\serif", "Cambria"))

        if draft:
            self.preamble.append(Package("background"))
            self.preamble.append(Command("backgroundsetup", NoEscape(
                r"position=current page.north west,"
                r"angle=0,"
                r"nodeanchor=north west,"
                r"vshift=-2 mm,"
                r"hshift=2 mm,"
                r"opacity=1,"
                r"scale=3,"
                r"contents=Draft")))

        if hyphenation is not None:
            word_list = NoEscape(" ".join(hyphenation))
            self.preamble.append(Command("hyphenation", word_list))

        date_and_version = ""
        if survey_date != "":
            if survey_date is None:
                date_and_version += "{}\\\\".format(NoEscape(r"\today"))
            else:
                date_and_version += "{}\\\\".format(survey_date)

        if survey_version is not None:
            date_and_version += "{}".format(survey_version)

        self.preamble.append(Command("title", title))
        self.preamble.append(Command("author", NoEscape(author)))
        self.preamble.append(Command("date", NoEscape(date_and_version)))
        self.preamble.append(Package("booktabs"))
        self.preamble.append(Package("tocloft"))
        self.preamble.append(Command("makeatletter"))
        if survey_version is not None:
            self.preamble.append(
                Command("chead[]", NoEscape(r"\@title\\Version {}".format(survey_version))))
        else:
            self.preamble.append(Command("chead[]", NoEscape(r"\@title")))
        self.preamble.append(
            Command(r"newcommand{\sectionwithlabel}[2]",
                    NoEscape(r"\phantomsection #1\def\@currentlabel{\unexpanded{#1}}\label{#2}")))

        self.preamble.append(Command("makeatother"))
        self.preamble.append(Command(r"newcommand\supscript[1]", NoEscape(r"{$^{\textrm{#1}}$}")))
        self.preamble.append(Command(r"newcommand\subscript[1]", NoEscape(r"{$_{\textrm{#1}}$}")))
        self.preamble.append(Command(r"newcommand\explanation[1]",
                                     NoEscape(r"\newline\footnotesize{\emph{#1}}")))

        # the filbreak makes sure that you do net get a lonely header at the bottom of the page
        section_str = r"\filbreak{\sectionwithlabel{\textbf{#1}}{#2}}"
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
            # the colorize keys are stored in a dictionary
            self.colorize_properties = colorize_questions
        else:
            self.colorize_properties = dict()

        self.preamble.append(Command(
            # this line changes the title of the table of contents
            NoEscape(r"addto\captionsdutch{\renewcommand{\contentsname}{\Large\textbf{"
                     r"Modules Vragenlijst}}}")))

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

        # these attributes get the properties of the first colorize item
        self.colorize_key = None
        self.colorize_label = None
        self.colorline = None
        self.colorize_color = None

        # initialise the counter with one counter for the total already
        init_count = {COUNT_MODULES_KEY: 0,
                      COUNT_QUST_KEY: 0,
                      COUNT_QUST_TOTAL_KEY: 0}
        self.counts = collections.Counter(init_count)
        self.counts_per_module = collections.OrderedDict()

        self.create_color_latex_command()

        # create the questionnaire environment and add all the modules with their questions
        with self.create(Questionnaire(options="noinfo")):

            # we can start with a info block in case that is given in the *general* section of
            # the yaml file
            if info_items is not None:
                self.append(VSpace(NoEscape(r"\parskip")))
                self.append(ModuleSection([NoEscape("Toelichting vragen"), "toelichting"]))
                self.add_info(info_items, fontsize="normalsize")

            # write the explanations per colorize item
            self.write_colorize_explanation()

            # always add a Data information
            self.append(AddInfo(arguments=["Date", time.strftime("%d.%m.%Y")]))

            # now add all the modules with questions
            self.add_all_modules()

            self.make_report()

    def remove_packages(self, packages_to_exclude: list):
        """ remove the packages in *package_to_exclude* from the preamble """
        package_to_remove = list()
        for package in self.packages:
            arguments = package.arguments._positional_args
            if arguments[0] in packages_to_exclude:
                package_to_remove.append(package)
        self.packages = self.packages.difference(package_to_remove)

    def write_colorize_explanation(self):
        """ Get the explanation field of all colorize items and add to the list of items """

        if self.colorize_properties is not None:
            have_any_color = False
            for col_key, col_prop in self.colorize_properties.items():
                if self.process_this_colorize(col_prop):
                    have_any_color = True

            if have_any_color:
                self.append(VSpace(NoEscape(r"\parskip")))
                self.append(ModuleSection([NoEscape("Toelichting kleuren"), "kleuren"]))
                with self.create(Itemize()):
                    for col_key, col_prop in self.colorize_properties.items():
                        if not self.process_this_colorize(col_prop):
                            continue
                        try:
                            explanation = col_prop["explanation"]
                        except KeyError:
                            logger.debug("No explanation added to {}".format(col_key))
                        else:

                            cmd = f"\\color{col_key}" + "{" + explanation + "}"
                            self.write_info(NoEscape(cmd), is_item=True)

    def make_report(self):
        """ Report the counts of the questions """

        if self.add_summary:
            self.append(Command("clearpage"))
            self.append(Command("setcounter", arguments=["secnumdepth", 0]))
            self.append(Section(title=self.summary_title,
                                label=NoEscape(re.sub(r"\s+", "_", self.summary_title).lower())))
            self.create_summary_table()

        logger.info("Counts")
        for key, count in self.counts.items():
            name = self.get_name_of_key(key)
            logger.info("{:20s} : {}".format(name, count))

    def create_summary_table(self):
        """
        Create two latex tables with all the count of the modules and questions
        """

        self.append(ModuleSection([NoEscape("Globaal aantal vragen"), "global"]))
        self.append(Command("newline"))

        with self.create(Tabular(arguments="ll")):
            self.append(Command("toprule"))
            self.append(r"\textbf{Grootheid}&\textbf{Aantal}\\")
            self.append(Command("midrule"))
            for key, count in self.counts.items():
                if key == COUNT_QUST_KEY:
                    # do not report the number of main questions, only including the sub questions
                    continue
                try:
                    col_prop = self.colorize_properties[key]
                except KeyError:
                    subtract_count_from_total = False
                else:
                    # in case the subtract_count_from_total key is defined, report the difference
                    # with the total. Usefull to report to total 'Kleine bedrijven' from the count
                    # of bedrijven where the kleine bedrijven are excluded
                    subtract_count_from_total = col_prop.get("subtract_count_from_total", False)

                if subtract_count_from_total:
                    number = self.counts[COUNT_QUST_TOTAL_KEY] - count
                else:
                    number = count

                name = self.get_name_of_key(key)
                self.append(f"{name} & {number}\\\\")
            self.append(Command("bottomrule"))

        self.append(Command("newline"))

        self.append(ModuleSection([NoEscape("Aantal vragen per module"), "permodule"]))
        self.append(Command("newline"))
        # minus 2 because we do not report the modules and not the main questions
        n_categories = len(list(self.counts.keys())) - 2
        tabular = "l" + "l" * n_categories
        with self.create(Tabular(arguments=tabular)):
            self.append(Command("toprule"))
            header = "\\textbf{Module}"
            for key, cnt in self.counts.items():
                if key in (COUNT_MODULES_KEY, COUNT_QUST_KEY):
                    continue
                name = self.get_name_of_key(key)
                header += (" & " + name)
            header += "\\\\"
            self.append(header)
            self.append(Command("midrule"))
            for key, module_count in self.counts_per_module.items():
                line = "\\ref{" + "{}".format(label_module(key)) + "} "
                line += self.questionnaire[key]["title"]
                for m_key in self.counts.keys():
                    if m_key in (COUNT_MODULES_KEY, COUNT_QUST_KEY):
                        continue

                    try:
                        col_prop = self.colorize_properties[m_key]
                    except KeyError:
                        subtract_count_from_total = False
                    else:
                        subtract_count_from_total = col_prop.get("subtract_count_from_total", False)

                    try:
                        value = module_count[m_key]
                    except KeyError:
                        value = 0

                    if subtract_count_from_total:
                        number = module_count[COUNT_QUST_TOTAL_KEY] - value
                    else:
                        number = value

                    line += (" & " + "{}".format(number))
                line += "\\\\"
                self.append(line)

            self.append(Command("bottomrule"))

    def get_name_of_key(self, key):
        """
        Get the name of the key

        Parameters
        ----------
        key: str
            The key we are dealing with, ie 'questions', 'modules' or 'questions_incl_choices'

        Returns
        -------
        str:
            The name of the quantity belong to the key
        """

        if key == COUNT_QUST_KEY:
            name = "Vragen Alleen Main"
        elif key == COUNT_QUST_TOTAL_KEY:
            name = "Alle Vragen"
        elif key == COUNT_MODULES_KEY:
            name = "Modules"
        else:
            colorize_prop = self.colorize_properties[key]
            try:
                name = colorize_prop["label"]
            except KeyError:
                name = key

        return name

    def create_color_latex_command(self):
        """
        Loop over all the color properties and create the command in latex to make them

        Notes
        -----
        The color properties are stored in an Ordered dict 'self.colorize_properties'. The
        first item in this dict is the main color which is assigned to a question, even of
        more colors are related to the same question
        """

        for col_key, col_prop in self.colorize_properties.items():
            # for each key in the colorize chapter create a latex color command

            if not self.process_this_colorize(col_prop):
                continue

            if re.search("_", col_key):
                raise ValueError("No _ allowed in the color keys")

            if col_key != DVZ_KEY:
                self.counts.update({col_key: 0})

            color_name = col_prop["color"]

            color_command = Command(r"newcommand\color" + col_key + "[1]",
                                    NoEscape(r"{{\color{" + r"{:}".format(color_name) + r"}{#1}}}"))

            if self.colorize_key is None:
                self.colorize_color = color_name
                self.colorize_key = col_key
                self.colorize_label = col_prop.get("label")
                self.colorline = col_prop.get("label")

                # create a new command for setting the color of a single line
                self.preamble.append(Command(r"newcommand\colorline[1]",
                                             NoEscape(r"{{\color{" +
                                                      r"{:}".format(self.colorize_color) +
                                                      r"}{#1}}}")))

                # create a new environment for setting the color in a block
                self.preamble.append(Command(
                    r"newenvironment{colorize}[1][" +
                    color_name +
                    r"]{\medskip\bgroup\color{#1}}{\egroup\medskip}"))

            self.preamble.append(color_command)

    def process_this_colorize(self, color_prop):
        """
        For this colorize properties, check if the add_this flag is there and is false

        Parameters
        ----------
        color_prop: dict
            Properties of the colorize

        Returns
        -------
        bool
            True if we have added this color
        """
        add_this = color_prop.get("add_this")
        if add_this is None:
            add_this = True
        review_only = color_prop.get("review_only", False)
        dvz_only = color_prop.get("dvz_only", False)
        if review_only and not self.review_references:
            # in case we have the review only flag and are not reviewing: do not use this color
            add_this = False
        if dvz_only and not self.dvz_references:
            # in case we have the review only flag and are not reviewing: do not use this color
            add_this = False
        return add_this

    def add_all_modules(self):
        """
        Add all the modules

        Notes
        -----
        * Loop over all the modules of the questionnaire and add the questions per module
        """

        for module_key, module_properties in self.questionnaire.items():
            add_this = module_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skipping section {}".format(module_key))
                continue

            exclude_from_count = module_properties.get("exclude_from_count", False)

            # add one to the counter of the modules
            if not exclude_from_count:
                self.counts.update({"modules": 1})

                # initialise the counter of the questions per module to zero
                init_count = {"questions": 0, "questions_incl_choices": 0}
                self.counts_per_module[module_key] = collections.Counter(init_count)
                for ckey, cprop in self.colorize_properties.items():
                    if cprop.get("add_this", True) and ckey != DVZ_KEY:
                        self.counts_per_module[module_key].update({ckey: 0})

            logger.info("Adding module {}".format(module_key))

            self.append(Command("clearpage"))

            color_key, color_name, goto, label = self.get_colorize_properties(module_properties)

            if color_name is not None:
                with self.create(Colorize(options=color_name)):
                    self.add_module(module_key, module_properties, goto,
                                    module_color_key=color_key,
                                    module_color_name=color_name,
                                    module_color_label=label,
                                    exclude_from_count=exclude_from_count)
            else:
                # if color_name is None no color was found, so report without color
                self.add_module(module_key, module_properties,
                                exclude_from_count=exclude_from_count)

    def get_colorize_properties(self, module_properties):
        """
        Check for all the colorize properties if one of them is added to the module properties

        Parameters
        ----------
        module_properties: dict
            Dictionary with the module properties

        Returns
        -------
        tuple
            (color_name,  goto, label), where color_name is the name of the color beloning to
            the key found in this module, goto is a reference string in case it is defined
            and label a prefix add to the goto
        """

        ckey = None
        color_name = None
        goto = None
        label = None
        for ckey, cprop in self.colorize_properties.items():
            if not self.process_this_colorize(cprop):
                continue
            if module_properties.get(ckey):
                color_name = cprop["color"]
                label = cprop.get("goto_condition_label")

                # we have found the key 'colorize_key' (given in the general section as e.g.
                # "smallcompany". This means the whole module needs to be coloured and also
                # we return the value of small_company. In case this is a string (an not a bool)
                # it is interpreted as a goto reference which needs to be reported.
                goto = module_properties[ckey]
                # stop checking the other keys in case we have found the first
                break

        return ckey, color_name, goto, label

    def add_module(self, module_key, module_properties, goto=None, module_color_key=None,
                   module_color_name=None, module_color_label=None, exclude_from_count=False):
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
            dealing for instance with a module which can be skipped for small companies. In case
            this value is a str, it is interpreted as a goto label
        module_color_key: str
            Name of the key of the color module
        module_color_label: str
            Name of the color label of the module
        module_color_name: str
            Name of the color name of the module
        exclude_from_count: bool
            If True, do not count this module and its questions
        """

        title = module_properties["title"]
        questions = module_properties["questions"]
        info = module_properties.get("info")

        self.append(Section(title=title, label=NoEscape(label_module(module_key))))

        if goto is not None and isinstance(goto, str):
            # A goto string is passed to the module. Prepend a Ga naar label before we start with
            # this module
            if module_color_label is not None:
                if re.match("^mod", goto):
                    # remove all underscores for mod: reference
                    goto = re.sub("_", "", goto)
                ref_str = f"{module_color_label}" + \
                          " $\\rightarrow$ Ga naar \\textbf{\\ref{" + \
                          goto + "}}"
                with self.create(InfoEnvironment()):
                    self.append(Command("normalsize", NoEscape(ref_str)))

        if info is not None:
            # in case a info section is given, at it at the top of the module
            self.add_info(info)

        color_all_in_section = False

        for key, question_properties in questions.items():

            # the filter is a dictionary with properties defining the condition and redirection
            # in case we want to skip to another question for a certain outcome
            filter_prop = question_properties.get("filter")

            increase_counter = question_properties.get("increase_counter")

            # if a section title field is given, start a new section title at this question
            section = question_properties.get("section")
            if section:
                ref_str = None
                color_all_in_section = False
                for ckey, cprop in self.colorize_properties.items():
                    if not self.process_this_colorize(cprop) or module_color_key is not None:
                        continue
                    goto = section.get(ckey)
                    if goto is None:
                        continue
                    color_all_in_section = cprop["color"]
                    label = cprop.get("label")

                    if isinstance(goto, str):
                        if re.match("^mod", goto):
                            # remove all underscores for mod: reference
                            goto = re.sub("_", "", goto)
                        if label is not None:
                            ref_str = f"{label}" + \
                                      " $\\rightarrow$ Ga naar \\textbf{\\ref{" + goto + "}}"
                    break

                title = section["title"]
                title_label = label_module_section(title)
                self.append(VSpace(NoEscape("\parskip")))

                if color_all_in_section:
                    with self.create(Colorize(options=color_all_in_section)):
                        self.append(ModuleSection([NoEscape(title), title_label]))
                        if ref_str is not None:
                            with self.create(InfoEnvironment()):
                                self.append(Command("normalsize", NoEscape(ref_str)))
                else:
                    self.append(ModuleSection([NoEscape(title), title_label]))
                    if ref_str is not None:
                        with self.create(InfoEnvironment()):
                            self.append(Command("emph", NoEscape(ref_str)))

                info = section.get("info")
                if info is not None:
                    self.append(VSpace(NoEscape("\parskip")))
                    if color_all_in_section:
                        with self.create(Colorize(options=color_all_in_section)):
                            self.add_info(info)
                    else:
                        self.add_info(info)

            add_this = question_properties.get("add_this", True)
            if not add_this:
                logger.debug("Skip question {}".format(key))
                continue

            logger.info("Adding question {}".format(key))
            if module_color_key is None:
                color_local, color_key = self.get_color_first_match(question_properties)
            else:
                color_local, color_key = module_color_name, module_color_key
            refers_to_label, refers_to_key = self.get_refers_to_label(question_properties)
            if color_local or color_all_in_section:
                if color_all_in_section:
                    col = color_all_in_section
                else:
                    col = color_local
                with self.create(Colorize(options=col)):
                    n_question = self.add_question(key, question_properties, filter_prop,
                                                   refers_to_label)
            else:
                # there is no local color and no overall section color defined. Write without color
                n_question = self.add_question(key, question_properties, filter_prop,
                                               refers_to_label)

            logger.debug("Count and keys {} {} {}".format(n_question, color_key, refers_to_key))

            # the refers to key may have a count field set to overrule the true
            # count. Check that here, and if so, impose it
            try:
                count = question_properties[refers_to_key]["count"]
            except (KeyError, TypeError):
                # if count was not set, just continue
                logger.debug("Keeping count: {} ".format(n_question))
            else:
                logger.info("Changing count: {} -> {}".format(n_question, count))
                n_question = count

            if not exclude_from_count:
                self.counts.update({COUNT_QUST_KEY: 1})
                self.counts_per_module[module_key].update({COUNT_QUST_KEY: 1})

                self.counts.update({"questions_incl_choices": n_question})
                self.counts_per_module[module_key].update({"questions_incl_choices": n_question})

                if color_local is not None and color_key != DVZ_KEY :
                    self.counts.update({color_key: n_question})
                    self.counts_per_module[module_key].update({color_key: n_question})
                if refers_to_label is not None and refers_to_key != color_key:
                    self.counts.update({refers_to_key: n_question})
                    self.counts_per_module[module_key].update({refers_to_key: n_question})

                if increase_counter is not None:
                    # this allow to increase the counter of one extra feature in case the
                    # 'increase_counter' key is defined in a question
                    self.counts.update({COUNT_QUST_TOTAL_KEY: 1})
                    self.counts_per_module[module_key].update({COUNT_QUST_TOTAL_KEY: 1})
                    self.counts.update({increase_counter: 1})
                    self.counts_per_module[module_key].update({increase_counter: 1})

    def get_refers_to_label(self, question_properties):
        """
        Get the refers to label in case we have it defined and the color as well

        Parameters
        ----------
        question_properties: dict
            Dictionary with the question properties

        Returns
        -------
        tuple:
            label with the reference and color of the question

        """
        refers_to = None
        ckey = None
        for ckey, cprop in self.colorize_properties.items():
            have_key = question_properties.get(ckey)
            if have_key and isinstance(have_key, dict) and self.process_this_colorize(cprop):
                refers_to = have_key.get("refers_to")
                if refers_to is not None:
                    label = self.colorize_properties[ckey]["label"]
                    cc = "\color{}".format(re.sub("_", "", ckey))
                    ll = "({}: $\\rightarrow$ ".format(label) + "{" + refers_to + "})"
                    refers_to = cc + "{" + ll + "}"
                    break  # stop after the first color you find
        return refers_to, ckey

    def get_color_first_match(self, question_properties):
        """
        Check if one of the keys of the current question matches one of the colorize keys

        Parameters
        ----------
        question_properties: dict
            Dictionary with the question properties

        Returns
        -------
        str:
            None or the name of the matched color
        """
        color = None
        ckey = None
        for ckey, cprop in self.colorize_properties.items():
            have_key = question_properties.get(ckey)
            if have_key and self.process_this_colorize(cprop):
                apply = self.colorize_properties[ckey].get("apply_color", True)
                if apply:
                    color = self.colorize_properties[ckey]["color"]
                else:
                    color = "black"
                break  # stop after the first color you find
        return color, ckey

    def add_question(self, key, question_properties, filter_prop=None, refers_to_label=None):
        """
        Add the current question to the document

        Parameters
        ----------
        key: str
            Unique name of the question
        question_properties: dict
            All question properties
        filter_prop: dict
            In case this is a filter question, add the filter properties
        refers_to_label: str or None
            In case defined, the give the label of the reference to the original eurostat question

        Returns
        -------
        int:
            Count of questions

        """

        question = question_properties["question"]
        question_type = question_properties.get("type", "quantity")
        info = question_properties.get("info")
        dvz = question_properties.get("dvz")
        if info:
            above = info.get("above", False)
        else:
            above = False

        if question_type not in QUESTION_TYPES:
            logger.info("question type {} not yet implemented. Skipping".format(question_type))
            return

        if self.review_references and refers_to_label:
            match = re.search("(explanation.*$)", question)
            if bool(match):
                expl = match.group(1)
                question = re.sub(expl, "", question)
            else:
                expl = None
            question += " \emph{" + refers_to_label + "}"
            if expl:
                question += ("\\" + expl)

        n_questions = 1

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
                n_questions = self.add_quantity_question(key, quantity_label, box_width=box_width,
                                                         filter_properties=filter_prop)
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
            groups = question_properties.get("groups", ["Ja", "Nee"])
            choice_lines = question_properties["choicelines"]
            with self.create(ChoiceGroupQuestion(arguments=NoEscape(question))):
                if info is not None and above:
                    self.add_info(info)
                n_questions = self.add_choice_group_question(key, groups, choice_lines, group_width,
                                                             filter_prop)
        elif question_type == "textbox":
            text_width = question_properties.get("textbox", "1cm")
            if info is not None and above:
                self.add_info(info)
            self.add_textbox_question(key, question, text_width)
        elif question_type == "range":
            range_items = question_properties["range_labels"]
            if info is not None and above:
                self.add_info(info)
            self.add_range_question(key, question, range_items)
        elif question_type == "rangegroup":
            question_lines = question_properties["question_lines"]
            range_labels = question_properties["range_labels"]

            with self.create(ChoiceRangeGroupQuestion(arguments=NoEscape(question))):
                if info is not None and above:
                    self.add_info(info)
                n_questions = self.add_range_group_question(question_lines=question_lines,
                                                            range_items=range_labels)
        else:
            raise AssertionError("question type not known. Check if type of question {} is one of "
                                 "the following: {} ".format(key, QUESTION_TYPES))

        if info is not None and not above:
            self.add_info(info)

        if dvz is not None and self.dvz_references:
            dvz_col_prop = self.colorize_properties["dvz"]
            dvz_color = dvz_col_prop["color"]
            with self.create(Colorize(options=dvz_color)):
                self.add_info(dvz)

        return n_questions

    def add_range_group_question(self, question_lines, range_items):

        items = list()
        for cnt, item in enumerate(range_items):
            if cnt == 2:
                logger.warning("Only two range items allowed")
                break
            items.append(NoEscape(item))

        n_questions = 0

        for cnt, line in enumerate(question_lines):
            char = string.ascii_lowercase[cnt] + ")"
            if re.search("colorline", line):
                # in case we color the line, do the same for the character
                char = "\colorline{" + char + "}"
            line_with_char = "\\textbf{" + char + "} " + line

            args = [NoEscape(line_with_char)] + items
            self.append(MarkLine(args))
            n_questions += 1

        return n_questions

    def add_range_question(self, key, question, range_items):
        """
        Add a range question

        Parameters
        ----------
        key: str
            Unique key of the question
        question: str
            The question
        range_items:
            list of strings to mark the lower and upper range
        """
        single_mark_arguments = [NoEscape(question)]
        for cnt, item in enumerate(range_items):
            if cnt == 2:
                logger.warning("Only two range items allowed")
                break
            single_mark_arguments.append(NoEscape(item))

        self.append(SingleMark(arguments=single_mark_arguments))

        self.append(Command("label", NoEscape(label_question(key))))

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
        """
        Add a group choice question
        """

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

        n_questions = 0

        for cnt, line in enumerate(choice_lines):
            char = string.ascii_lowercase[cnt] + ")"
            if re.search("colorline", line):
                # in case we color the line, do the same for the character
                char = "\colorline{" + char + "}"
            line_with_char = "\\textbf{" + char + "} " + line
            self.append(ChoiceLine(NoEscape(line_with_char)))
            n_questions += 1

        self.append(Command("label", NoEscape(label_question(key))))

        if n_questions == 0:
            n_questions = 1

        return n_questions

    def add_info(self, info, fontsize="footnotesize", color=None):
        """
        Add a info block with a nested block it bullet points

        Parameters
        ----------
        info: dict
            A dictionary with the information to add to the info block. See *write_info* for
            a description of the dictionary
        """

        if color is None:
            with self.create(InfoEnvironment()):
                self.write_info(info, fontsize=fontsize)
        else:
            with self.create(Colorize(options=color)):
                with self.create(InfoEnvironment()):
                    self.write_info(info, fontsize=fontsize)
        self.append(VSpace(NoEscape("\parskip")))

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
            If true,  strings are items of a itemize environment and need a item command

        Notes
        -----
        The *info* dictionary has the following format::

            info:
              fontsize: this field is used to set the font size of the info block. Default is footnotesize
              title: The title added outside the itemize block
              items: # either a list or a dict can follow the items.
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

        The routine below is recursively calling itself so that in the items can be nested
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
                    category = None

                # rmove all _ as they are not allowed in latex
                if ref_cat != "quest":
                    goto = re.sub("_", "", goto)

                if category is not None:
                    redirect_str = "$\\rightarrow$ Ga naar " + category + " \\ref{" + goto + "}"
                else:
                    # in case we can not find a sensible fit, add the whole goto string
                    redirect_str = "$\\rightarrow$ Ga naar " + goto

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
                              box_width=4, filter_properties=None):
        """
        A a question with a quantity answer to the document

        Parameters
        ----------
        key: str
            Name of the key
        quantity_label: str or list
            Name of the quantity label. Can also be a list
        label_width: int
            Width of the label
        box_width: float
            Width of the box around the label
        filter_properties: dict
            Dict containing the properties of the filter

        Returns
        -------
        int:
            Number of questions

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

        n_questions = 0
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
            n_questions += 1

        if n_questions == 0:
            n_questions = 1

        self.append(Command("label", NoEscape(label_question(key))))

        if filter_properties is not None:
            condition = filter_properties["condition"]
            redirection_str = self.get_redirection_string_for_filter(filter_properties)
            self.add_info(condition + redirection_str)

        return n_questions
