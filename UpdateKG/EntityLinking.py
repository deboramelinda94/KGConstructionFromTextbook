import spacy
import math
from neo4j.v1 import GraphDatabase
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
from conda_build.api import build

lemmatizer = WordNetLemmatizer()
stemmer = SnowballStemmer("english")
driver = GraphDatabase.driver("bolt://localhost:7687", auth=(username, password))
nlp = spacy.load('en_core_web_sm')

    
def referEntity(mentionToken, enCan):
    entityToken = []
    
    if len(enCan) == 0:
        return ""
    elif len(enCan) == 1:
        entityToken = enCan[0]
    else:
        flag = False
        mention = ' '.join(mentionToken)
        if mention in enCan:
            entityToken = mention
            flag = True
        if flag == False:
            dictTerm = {}
            for item in enCan:
                entityToken = nlp(item)
                for et in entityToken:
                    if not et.text in dictTerm:
                        dictTerm[et.text] = 1
                    else:
                        dictTerm[et.text] += 1
                        
            score = 0
            result = ""
            for item in enCan:
                entityToken = nlp(item)
                sum = 0
                mentionTokens = nlp(' '.join(mentionToken))
                
                for mt in mentionTokens:
                    max = 0
                    enMax = ""
                    for et in entityToken:                    
                        if et.text.isalpha() == False: #has character that is not letter
                            break
                        idf = 1 + math.log10(len(enCan)/(1+dictTerm[et.text]))
                        
                        try:
                            s = mt.similarity(et)*idf
                        except:
                            break
                        
                        if s > max:
                            max = s
                            enMax = et.text
                            
                    sum += max
                        
                if sum > score:
                    score = sum
                    result = item
            entityToken = result        
    
    entityToken = word_tokenize(entityToken)
    listInter = list(set(entityToken).intersection(set(mentionToken)))
    ratioSimilar = len(listInter)/len(mentionToken) 
    
    if ratioSimilar > 0.25 or "of" in mentionToken:
        return ' '.join(entityToken)   
    else:
        return ""

def relateEntity(tx, entity1, type1, entity2, type2, relation, chNum=None):
    relation = relation.strip()
    r = relation
    if " " in relation:
        splitSpace = relation.split(" ")
        a = splitSpace[1][0].upper()
        splitSpace[1] = a + splitSpace[1][1:]
        splitSpace[0] = lemmatizer.lemmatize(splitSpace[0], 'v') 
        r = ''.join(splitSpace) 
    else:
        r = lemmatizer.lemmatize(r, 'v') 
    
    Aprop = ""
    Bprop = ""
    if type1 == "detail" and chNum != None:
        Aprop = "a:" + type1 + "{Name:'" + entity1 + "', id:'" + chNum + "'}"
    else:
        Aprop = "a:" + type1 + "{Name:'" + entity1 + "'}" 
    
    if type2 == "detail" and chNum != None:
        Bprop = "b:" + type2 + "{Name:'" + entity2 + "', id:'" + chNum + "'}"
    else:
        Bprop = "b:" + type2 + "{Name:'" + entity2 + "'}" 
    
    query = "match ("+ Aprop +")-[r]-(" + Bprop +") return type(r) as rel"
    flag = True
    result = tx.run(query)
    if len(list(result)) > 0:
        for res in result:
            existRelation = res["rel"]
            relationToken = nlp(relation)
            existToken = nlp(existRelation)
            s = relationToken.similarity(existToken)
            if s > 0.4:
                flag = False
                break

    if flag:
        query = "match ("+ Aprop +"), (" + Bprop +") merge (a)-[:" + r + "]->(b)"
        tx.run(query)
    
def createVirtualNode(tx, name, typeNode):
    query = "MERGE (a:virtual" + typeNode + "{Name:'" + name + "'})"
    tx.run(query)

def findEntity(tx,mention, chNum, typeCh,abb = None):  
    mention = mention.lower()
    mentionToken = word_tokenize(mention)
    mentionToken = [lemmatizer.lemmatize(token, 'n') for token in mentionToken]
    lemmaCan = mentionToken
    if abb != None:
        #stemCan.append(abb)
        lemmaCan
   
    if len(lemmaCan) > 1:
        lemmaCan = "','".join(lemmaCan)
    else:
        lemmaCan = lemmaCan[0]
    lemmaCan = "'" + lemmaCan + "'"
    
    KGLEVEL = ["Title", "Module", "Clue", "Unit"]
    
    query = "Match (n:ACM)<-[r]-(a:ACM) WHERE ANY ( x IN [" + lemmaCan + "] WHERE x in n.lemmas ) \
    return DISTINCT n.Name as subject"
    
    result = tx.run(query)
    enAcm = []
    
    for res in result:
        enAcm.append(res["subject"])
    
    enKG = []
    acrossKG = []
    levelAcross = {}
    levelFound = {}
    startLevel = KGLEVEL.index(typeCh)
    for i in range(startLevel+1):
        splitChPre = chNum.split(".")
        upper = '.'.join(splitChPre[:len(splitChPre)-i+1])
        if KGLEVEL[i] == "Title":
            upper = ""
        elif KGLEVEL[i] == "Module":
            upper = splitChPre[0]
        elif KGLEVEL[i] == "Clue":
            upper = splitChPre[0] + "." + splitChPre[1]
        else:
            upper = '.'.join(splitChPre)

        query = "Match (a:detail) WHERE ANY ( x IN [" + lemmaCan + "] WHERE x in a.lemmas ) \
        and a.typeCh = '"+ KGLEVEL[i] +"' and a.id = '"+ upper +"' return DISTINCT a.Name"  
        result = tx.run(query)
        
        
        for res in result: 
            enKG.append(res["a.Name"])
            levelFound[res["a.Name"]] = "detail"
        
        arrResult = list(result)
        
        if len(arrResult) == 0:
            query = "Match (n:" + KGLEVEL[i] + ")-[r]-(a) WHERE ANY ( x IN [" + lemmaCan + "] WHERE x in n.lemmas ) \
            and n.id = '"+ upper +"' return DISTINCT n.Name" 
            result = tx.run(query)
            
            for res in result: 
                enKG.append(res["n.Name"])
                levelFound[res["n.Name"]] = KGLEVEL[i]
            
            query = "Match (n:" + KGLEVEL[i] + ")-[r]-(a) WHERE ANY ( x IN [" + lemmaCan + "] WHERE x in n.lemmas ) \
            and n.id <> '"+ upper +"' return DISTINCT n.Name, n.id" 
            result = tx.run(query)
            
            for res in result: 
                acrossKG.append(res["n.Name"])
                levelAcross[res["n.Name"]] = KGLEVEL[i]
                
        if len(enKG) > 0:
            break
            
    enAcm = referEntity(mentionToken, enAcm)
    enKG = referEntity(mentionToken, enKG)
    
    if enKG != "" and enAcm != "":
        #mention is exist in both KG and ACM
        createVirtualNode(tx, enAcm, "ACM")
        relateEntity(tx, enKG, levelFound[enKG], enAcm, "virtualACM", "hasLink")
        
        if len(acrossKG) > 0:
            acrossKG = referEntity(mentionToken, acrossKG)
            if acrossKG != "":
                createVirtualNode(tx, acrossKG, levelAcross[acrossKG])
                typeVirtual = "virtual" + levelAcross[acrossKG]
                relateEntity(tx, enKG, levelFound[enKG], acrossKG, typeVirtual, "hasLink")
        
    elif enKG == "" and enAcm != "":
        createVirtualNode(tx, enAcm, "ACM")
        return [enAcm, "virtualACM"]
    elif enKG != "":
        if len(acrossKG) > 0:
            acrossKG = referEntity(mentionToken, acrossKG)
            if acrossKG != "":
                createVirtualNode(tx, acrossKG, levelAcross[acrossKG])
                typeVirtual = "virtual" + levelAcross[acrossKG]
                relateEntity(tx, enKG, levelFound[enKG], acrossKG, typeVirtual, "hasLink")
    
        return [enKG, levelFound[enKG]]
    else:
        findEntity = addNewEntity(tx, mention, chNum, typeCh, abb)
        enKG = findEntity[0]
        levelFound[enKG] = findEntity[1]
    
    
    if len(acrossKG) > 0:
        acrossKG = referEntity(mentionToken, acrossKG)
        if acrossKG != "":
            createVirtualNode(tx, acrossKG, levelAcross[acrossKG])
            typeVirtual = "virtual" + levelAcross[acrossKG]
            relateEntity(tx, enKG, levelFound[enKG], acrossKG, typeVirtual, "hasLink")
        
    return [enKG, levelFound[enKG]]     

def addNewEntity(tx, name, chNum, typeCh, abb=None): 
    name = name.lower()
    mentionToken = word_tokenize(name)
    mentionToken = [lemmatizer.lemmatize(token, 'n') for token in mentionToken]
    name = ' '.join(mentionToken)
    
    resLemma = ""
    if len(mentionToken) > 1:
        resLemma = "','".join(mentionToken)
    else:
        resLemma = mentionToken[0]
    resLemma = "'" + resLemma + "'"
    
    query = "MATCH (a:detail{Name:'" + name + "', id:'" + chNum + "'}) \
            return count(a) as count"
    
    result = tx.run(query)
    count = result.single()[0]
    
    if count == 0:
        if abb == None:       
            query = "MERGE (a:detail{Name:'" + name + "', lemmas:[" + resLemma \
                + "], id:'" + chNum + "',typeCh:'" + typeCh + "',alias:['" + name + "']})"
        else:
            alias = "'" + name + "','" + abb + "'"         
            query = "MERGE (a:detail{Name:'" + name + "', lemmas:[" + resLemma \
                + "], id:'" + chNum + "',typeCh:'" + typeCh + "',alias:[" + alias + "]})"
        
        tx.run(query)
        
    return [name, "detail"]

def relateTOC(tx, name, chNum, typeCh, typeP, levelNode):
    query = "MATCH (a:" + levelNode + "{Name:'" + name +"',id:'"+ chNum + "'}), (b:" \
    + typeCh + "{id:'" + chNum \
    + "'}) MERGE (b)-[:" + typeP + "]->(a)"
    tx.run(query)


def checkRelation(tx, subj, obj, subjLevel, objLevel):
    query = "MATCH (a:"+subjLevel+ "{Name:'" + subj + "'})-[r]-(b:"+objLevel+"{id:'" + obj + "'})"\
    + "return type(r) as rel"
    result = tx.run(query)
    if len(list(result)) > 0:
        return 1
    else:
        return 0
    
def deleteAloneRelation(tx):
    query = "MATCH (a)-[r]-(a) delete r"
    tx.run(query)
    
def linkEntity(subj, predicate, obj, chNum, typeCh, typeP, abbS = None, abbO = None):
    
    with driver.session() as session:
        findSub = session.read_transaction(findEntity,subj, chNum, typeCh, abbS)
        findObj = session.read_transaction(findEntity,obj, chNum, typeCh,abbO)
               
        if findSub != "" and findObj != "":
            sub = findSub[0]
            levelSub = findSub[1]
            ob = findObj[0]
            levelOb = findObj[1]
            
        else:
            if findSub == "":
                findSub = session.read_transaction(addNewEntity, subj, chNum, typeCh, typeP, abbS)
            if findObj == "":
                findObj = session.read_transaction(addNewEntity, obj, chNum, typeCh, typeP, abbO)
            sub = findSub[0]
            levelSub = findSub[1]
            ob = findObj[0]
            levelOb = findObj[1]

        if sub == ob:
            return    
        
        if levelSub == "detail":        
            session.read_transaction(relateTOC, sub, chNum, typeCh, typeP, levelSub)
        elif levelOb == "detail":
            session.read_transaction(relateTOC, ob, chNum, typeCh, typeP, levelOb)
      
        session.read_transaction(relateEntity, sub, levelSub, ob, levelOb, predicate, chNum)
        
        session.read_transaction(deleteAloneRelation)
        

def getNodeChapter(tx, chNum, typeCh, typeNode):
    query = "MATCH (a:" + typeCh +"{id:'" + chNum + "'})-[]->(b:" + typeNode\
    + ")"+ " return count(b) as sum"
    
    result = tx.run(query)
    count = result.single()[0]
    return count

    tx.run(query) 
    

DEFINITIONS = {"is","are", "know", "known","has", "have"}
FUNCTIONS = {"use", "usage", "utilization", "purpose", "role",
                   "utilize", "apply", "practice", "implement", "represent"}
def linkNode(chNum, typeCh, subj, pred, obj, abbS=None, abbO=None):
    typeP = ""
    splitSpace = ['']
    if " " in pred:
        splitSpace = pred.split(" ")
    
    if pred in DEFINITIONS or splitSpace[0] in DEFINITIONS:
        typeP = "definition"
    elif pred in FUNCTIONS:
        typeP = "function"
    else:

        typeP = "other"
     
    if subj != "" and obj != "" and pred != "":
        linkEntity(subj, pred, obj, chNum, typeCh, typeP, abbS, abbO) 
