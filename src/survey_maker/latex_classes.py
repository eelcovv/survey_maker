"""
Some aid classes and function for the latex environment
"""
import re
from pylatex.base_classes import Environment, CommandBase


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


class ChoiceQuestion(Environment):
    _latex_name = "choicequestion"
    escape = False
    content_separator = "\n"


class ChoiceGroupQuestion(Environment):
    _latex_name = "choicegroup"
    escape = False
    content_separator = "\n"


class ChoiceItemText(CommandBase):
    _latex_name = "choiceitemtext"
    escape = False
    content_separator = "\n"


class ChoiceItem(CommandBase):
    _latex_name = "choiceitem"
    escape = False
    content_separator = "\n"


class ChoiceLine(CommandBase):
    _latex_name = "choiceline"
    escape = False
    content_separator = "\n"


class GroupChoice(CommandBase):
    _latex_name = "groupaddchoice"
    escape = False
    content_separator = "\n"


class AddInfo(CommandBase):
    _latex_name = "addinfo"
