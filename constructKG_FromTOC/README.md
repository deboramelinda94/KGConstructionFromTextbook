Entity Extraction from table of content (TOC) of textbook

In order to construct knowledge graph (KG) from textbook, the initial KG should be constructed before the entity from the textbook is added as well as become the backbone for the KG. In addition, the entity that is extracted from the TOC later can be used for paragraph summarization.

The dataset is a textbook whose title is "Data Structures and Algorithms in Python" Utilize NLTK library to get the part of speech tagging (POS tagging) and to do word tokenization

Characteristic of entity in TOC:
1.Noun phrase
2.Adjactive phrase
3.Verb phrase (Gerund and past participle verb)

Algorithm Input: Table of content of textbook Output: list of entity

1.Create list of python syntax (Due to the selected dataset, the python syntax may become the entity in TOC, ignore this step if the selected textbook is different)
2.Remove determiner (e.g. "the", "a", "an")
3.Separate conjunction and coma in the TOC in order to get the individual topic
4.Filter the noun phrase, adjective phrase, and verb phrase using NLTK pos_tag library
5.Store the filtered phrase to list
