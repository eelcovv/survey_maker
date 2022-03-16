""" Deze module bevat een klasse om alle labels op te slaan """
LANGUAGES = ("dutch", "english")


class DocumentLabels:
    def __init__(self, language):
        self.language = language

        self.toelichting_vragen = None
        self.default_choices = None
        self.modules_vragenlijst = None
        self.ga_naar = None
        self.vraag = None
        self.module = None
        self.module_sectie = None

        if self.language == "dutch":
            self.set_labels_dutch()
        elif self.language == "english":
            self.set_labels_english()
        else:
            raise AssertionError(f"Language must be one of {LANGUAGES}")

    def set_labels_dutch(self):
        self.toelichting_vragen = "Toelichting vragen"
        self.modules_vragenlijst = "Modules Vragenlijst"
        self.default_choices = ["Ja", "Nee"]
        self.ga_naar = "Ga naar"
        self.vraag = "vraag naar"
        self.module = "module"
        self.module_sectie = "module sectie"

    def set_labels_english(self):
        self.toelichting_vragen = "Explanation questions"
        self.default_choices = ["Yes", "No"]
        self.modules_vragenlijst = "Modules Questionnaire"
        self.ga_naar = "Go to"
        self.vraag = "question"
        self.module = "module"
        self.module_sectie = "module section"
