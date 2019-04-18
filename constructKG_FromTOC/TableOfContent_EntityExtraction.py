from nltk import pos_tag
from nltk.tokenize import word_tokenize

def createTermGlossary(fileName): #related to selected dataset (e.g. python syntax that may is listed in the TOC)
    TermGlossary = []
    f = open(fileName, "r")
    content = f.readlines()

    for item in content:
        item = item.rstrip("\n")
        TermGlossary.append(item)
    f.close()
    return TermGlossary


def checkPureTerm(posTag):
    termType = {"NN", "NNP", "NNS", "JJ", "VBG", "VBN"}
    canConcept = []
    for i in range(len(posTag)):
        #linguistic filtering      
        if (posTag[i][1] in termType or posTag[i][0] in pythonGlossary\
            ) and re.search('[a-zA-Z]', posTag[i][0]) and len(posTag[i][0]) > 1:
            canConcept.append(posTag[i][0])        
    canConcept.append("")
   
    finConcept = []
    temp = ""
    for item in canConcept:
        if item != "":
            temp = temp + item + " "
        else:
            finConcept.append(temp.rstrip())
            temp = ""
    return finConcept        

def getNounAdj(token): #token --> array of tokenize
    listConcept = []
    determiner = ['the','a', 'an']
    subConcept = []
   
    determinerRemove = []
    for word in token:
        if word not in determiner:
            determinerRemove.append(word)
    token = determinerRemove
    
    posTag = pos_tag(token)
    
    if "and" in token:
        indexConj = token.index("and")
        
        if "," in token:
            subTopic = checkPureTerm(posTag[indexConj+1:])  
            subConcept.extend(subTopic)
                
            for i in range(indexConj):
                if token[i] is not ",":
                    subConcept.append(token[i])         
        else:
            subTopic = checkPureTerm(posTag[indexConj+1:])  
            subConcept.extend(subTopic)

            #If the word at the left is Noun, directly become new topic
            if "NN" in posTag[indexConj-1][1]:
                #subTopic = ' '.join(token[:indexConj])    
                subTopic = checkPureTerm(posTag[:indexConj])        
                subConcept.extend(subTopic)
                  
            #If the word at the left is Verb, merge it with the Noun that located at the right
            else:
                for i in range(len(token)-1, indexConj+1,-1):
                    if "NN" in posTag[i][1]:
                        otherTopic = token[indexConj-1] + " " + posTag[i][0]
                        subConcept.append(otherTopic)
                        break            
    else:
        subTopic = checkPureTerm(posTag)                
        subConcept.extend(subTopic)
        
    while "" in subConcept:
        subConcept.remove("")
    return subConcept
