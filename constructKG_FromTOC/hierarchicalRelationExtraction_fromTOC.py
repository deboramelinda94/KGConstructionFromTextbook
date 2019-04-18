from neo4j.v1 import GraphDatabase
from nltk.tokenize import word_tokenize
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer
import re

lemmatizer = WordNetLemmatizer()
#connect Neo4j Database
driver = GraphDatabase.driver("bolt://localhost:7687", auth=(username, password))
stemmer = SnowballStemmer("english")

def getSeparateLevel(chapterNumberName):
    modulDiction = {}      
    clueDiction = {}   
    unitDiction = {}
  
    for k,v in chapterNumberName.items(): 
        if re.search('^[1-9]*$', k): #no full stop --> module
            modulDiction[k] = v
            
        elif re.search('^\d+\.\d*$', k): #one full stop --> clue
            clueDiction[k] = v
            
        elif re.search('^\d+\.\d+\.\d*$', k): #two full stop --> unit
            unitDiction[k] = v
   
    return [modulDiction, clueDiction, unitDiction]
   
def addNewEntity(tx, id, occ, name, typeEntity, alias = None): 
    name = name.lower()
    mention = word_tokenize(name)
    stems = [stemmer.stem(token) for token in mention]   
    
    resStem = ""
    if len(stems) > 1:
        resStem = "','".join(stems)
    else:
        resStem = stems[0]
    resStem = "'" + resStem + "'"
    
    if alias == None:
        alias = name
        
    query = "MERGE (a:" + typeEntity +"{id:'" + str(id) + "', occurrence:" + str(occ) + ", Name:'" \
                + name + "', stem:[" + resStem + "]" \
                + ", alias:'" + alias +"'})"

    tx.run(query)
    
def createRelation(tx, presentClass, presentId, upperClass, upperName ,relType):
    query = "Match (a:" + presentClass + "{id:'" + presentId + "'}), " \
            + "(b:" + upperClass + "{Name:'" + upperName + "'})" \
            + "MERGE (a)-[:" + relType + "]->(b)" 
    tx.run(query)

def linkUpperClass(tx, id, occ, name, presentClass, upperClass, chUpper = None, relType = None):
    mentionToken = word_tokenize(name)
    mentionToken = [lemmatizer.lemmatize(item, 'n') for item in mentionToken]
    name = ' '.join(mentionToken)
    stemCan = [stemmer.stem(token) for token in mentionToken]
    
    if len(stemCan) > 1:
        stemCan = "','".join(stemCan)
    else:
        stemCan = stemCan[0]
    stemCan = "'" + stemCan + "'"
    
    query = "Match (n:" + upperClass +") WHERE ANY ( x IN [" + stemCan + "] WHERE x in n.stem ) \
    return DISTINCT n.Name as subject"
    #check whether the entity in upper class contain any word from the new entity
    result = tx.run(query)
    
    maxSameWord = 0
    listSameWord = []
    upperName = ""
    for res in result:
        entityToken = word_tokenize(res["subject"])
        tempSameWord = list(set(mentionToken).intersection(set(entityToken)))
        #get the identical word between the new entity and the entity in the upper class
        if len(tempSameWord) > maxSameWord:
            maxSameWord = len(tempSameWord)
            listSameWord = tempSameWord
            upperName = res["subject"]
    
    #if there is identical word, remove that word from the new entity to make alias
    if maxSameWord > 0:
        for item in listSameWord:
            mentionToken.remove(item)
        
        alias = ' '.join(mentionToken)
        addNewEntity(tx, id, occ, name, presentClass, alias)
       
    else:
        #there is no similar words with the upper class' entity, no alias attribute
        addNewEntity(tx, id, occ, name, presentClass)
          
    query = "Match (n:" + upperClass + "{id:'" + chUpper + "', occurrence:1}) return n.Name" 
    result = tx.run(query)
    chName = result.single()[0]
    createRelation(tx, presentClass, id, upperClass, chName, relType)
            
def runEachLevel(levelDiction, levelName, upperLevelName, upperChNum):
    levelkeys = list(levelDiction.keys())
    relationName = ""
    
    if upperLevelName == "Module":
        relationName = "Clue_of"
    elif upperLevelName == "Clue":
        relationName = "Unit_of"
    
    for i in range(len(levelkeys)):
        thisKey = levelkeys[i]
        occ = 1

        with driver.session() as session:
            session.write_transaction(linkUpperClass, thisKey, occ, levelDiction[thisKey][0], levelName, \
                                      upperLevelName, upperChNum, relationName)
        
            for j in range(1, len(levelDiction[thisKey])):
                occ += 1
                session.write_transaction(linkUpperClass, thisKey, occ, levelDiction[thisKey][j],  
                                      levelName, upperLevelName, upperChNum, relationName)
            if len(levelDiction[thisKey]) > 0:
                for j in range(0, len(levelDiction[thisKey])-1):
                    session.write_transaction(add_RelNode, thisKey, j+1, j+2, levelName)
    
    for i in range(len(levelkeys)-1):      
        thisLevelKey = levelkeys[i]
        key_next = levelkeys[i+1]
        
        if thisLevelKey[0] == key_next[0]:
            with driver.session() as session:
                session.write_transaction(add_FolNode, thisLevelKey, key_next, levelName)
