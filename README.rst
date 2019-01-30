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
pdf file gegegeneerd worden::

    vragenlijst_branchnaam.pdf

In deze volgende presentatie worden wat meer details gegeven over het
gebruik van git:

Presentatie Introductie SurveyMaker :download: `docs/presentations/presentatie_survey_maker_intro
.pdf`


Note
====

This project has been set up using PyScaffold 3.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
