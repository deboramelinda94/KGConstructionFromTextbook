After the all entities from the TOC are extracted, the next step is to build KG with those entities.

Commonly TOC consist of three level, we refer those level as:
1. Module: node class that refers to the chapter in textbook (e.g. 1 Python Primer)
2. Clue: node class that refers to the subchapter in textbook (e.g. 1.1 Python Overview)
3. Unit: node class that refers to the sub unit of the sub chapter in textbook (e.g. 1.1.1 The Python Interpreter) These hierarchical class is created to simplify the entity searching in the future.

Moreover, the entity from the TOC is connected to other entities from the class itself and the upper class. Those relation are:
1. Clue_of: relation between clue node and module node
2. Unit_of: relation between unit node and clue node
3. Rel_Module: relation between one module node and the next module node
4. Rel_Clue: relation between one clue node and the next clue node
5. Rel_unit: relation between one unit node and the next unit node

The entity and relation is stored in Graph Database, and the Graph database that is selected is Neo4j. Hence, in this process of building hierarchical knowledge graph there are two subprocess which are add new entity and create relation between entities.

Algorithm Input: table of content of textbook Output: constructed KG

1. Group the entity from TOC to module, clue, and unit
2. Create relation between entity in particular class to the entity in the upper class
3. if there are identical words between those two entities, create alias for the new entity with removing the identical words
4. Create relation between one entity to the next entity in the same class
