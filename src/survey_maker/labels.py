""" Deze module bevat een klasse om alle labels op te slaan """
LANGUAGES = ("dutch", "english")


class DocumentLabels:
    def __init__(self, language):
        self.language = language

        self.toelichting_vragen = None
        self.toelichting_kleuren = None
        self.default_choices = None
        self.modules_vragenlijst = None
        self.ga_naar = None
        self.vraag = None
        self.module = None
        self.module_sectie = None
        self.globaal_aantal_vragen = None
        self.aantal_vragen_per_module = None
        self.vragen_alleen_main = None
        self.alle_vragen = None
        self.modules = None
        self.category = None
        self.aantal = None

        if self.language == "dutch":
            self.set_labels_dutch()
        elif self.language == "english":
            self.set_labels_english()
        else:
            raise AssertionError(f"Language must be one of {LANGUAGES}")

    def set_labels_dutch(self):
        self.toelichting_vragen = "Toelichting vragen"
        self.toelichting_kleuren = "Toelichting kleuren"
        self.modules_vragenlijst = "Modules Vragenlijst"
        self.default_choices = ["Ja", "Nee"]
        self.ga_naar = "Ga naar"
        self.vraag = "vraag naar"
        self.module = "module"
        self.module_sectie = "module sectie"
        self.globaal_aantal_vragen = "Globaal aantal vragen"
        self.aantal_vragen_per_module = "Aantal vragen per module"
        self.vragen_alleen_main = "Vragen alleen main"
        self.alle_vragen = "Alle vragen"
        self.modules = "Modules"
        self.category = "Categorie"
        self.aantal = "Aantal"

    def set_labels_english(self):
        self.toelichting_vragen = "Explanation questions"
        self.toelichting_kleuren = "Explanation colours"
        self.default_choices = ["Yes", "No"]
        self.modules_vragenlijst = "Modules Questionnaire"
        self.ga_naar = "Go to"
        self.vraag = "question"
        self.module = "module"
        self.module_sectie = "module section"
        self.globaal_aantal_vragen = "Overall number of questions"
        self.aantal_vragen_per_module = "Number of questions per module"
        self.vragen_alleen_main = "Questions Main only"
        self.alle_vragen = "All questions"
        self.modules = "Modules"
        self.category = "Category"
        self.aantal = "Number"
