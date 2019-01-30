============
SurveyMaker
============


SurveyMaker kan gebruikt worden om een vragen lijst te bouwen


Omschrijving
============

SurveyMaker is een Python script om vragenlijst te maken. Hiertoe kan de
vragenlijst in een Yaml-file ingevoerd worden. SurveyMaker zal deze in een
PDF-document omzetten

Gebruik
=======

De vragenlijst wordt in een yaml file gestopt met een voorgeschreven format.
Met het volgende commando kan daar een PDF van gemaakt worden::

  >>> survey_maker vragenlijst.yml

Het beste werkt dit al de vragenlijst in een git repository staat met een
branch naam als jaartal waarop de enquête slaat. In dat geval zal de volgende
pdf file gegegeneerd worden *vragenlijst_branchnaam.pdf*, waarbij *branchnaam* bijvoorbeeld
*2018* is. In deze volgende presentatie worden wat meer details gegeven over het
gebruik van git:

Presentatie SurveyMaker :download:`presentations/presentatie_survey_maker_intro.pdf`

Omschrijving Yaml-file
======================

De meeste beknopt vorm van een input file ziet er als volgt uit::

    # inhoud van small_example.yml
    general:                            # dit hoofdstuk bevat alle generiek instellingen
      preamble:                         # preamble slaat op alles wat in de Latex preamble komt
        title: Gewetensvragen           # hooftitle van vragenlijst
        author: Eelco van Vliet         # Auteur van vragen lijst
    questionnaire:                      # het hoofdstuk 'questionnaire' bevat alle modules
      inleiding_gewetensvragen:         # Dit is module A
        title: Module gewetensvragen    # Hier wordt de title van module A gegeven
        questions:                      # in dit hoofdstuk staan alle vragen van module A
          welke_het_liefst:             # De eerste vraag van module A
            question: Welk programma heeft jou voorkeur voor de volgende taken?
            type: group                 # De vraag (gegeven met 'question' is van het type 'group'
            groups:                     # Onder 'groups' worden de keuzes gegevens die rechts komen
            - \LaTeX
            - LibreOffice
            - Microsoft Word
            choicelines:                # Choice lines zijn de regels waarvoor we kiezen uit groups
            - Generieke tekstlayout
            - Documenten met formules
            - Het maken van vragenlijsten

De PDF file compileren we met het volgende commando::

    >>> survey_maker small_example.yml --twice --clean

We geven nu de optie --twice en --clean mee. De eerste optie is nodig om de inhoudsopgave goed te
krijgen (dit is iets van Latex: je moet twee keer compileren als je voor het eerst de inhoudsopgave
wil maken; iedere volgende keer hoeft maar 1 keer gecompileerd te worden). De tweede opties gooit
alle intermediate Latex files weg als het script klaar is.

De resulteren PDF file kan hier geopend worden :download:`examples/small_example_master.pdf`. Het
stuk met de vraag ziet er als volgt uit





Note
====

This project has been set up using PyScaffold 3.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
