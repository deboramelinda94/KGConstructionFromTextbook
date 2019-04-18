import spacy
from nltk.tokenize import word_tokenize

nlp = spacy.load('en_core_web_sm')

def splitSentence(theSentence):
    theComp = []
    
    w = word_tokenize(theSentence)
    doc = nlp(theSentence)
    for token in doc:
        agent = []
        patient = []
        first = ""
        last = ""
        try:
            if token.dep_ == "ROOT":
                for child in token.children:
                    if "subj" in child.dep_ and child.pos_ == "NOUN":        
                        childLeft = [item.text for item in child.lefts]           
                        ind = -1
                        ag = ' '.join(childLeft) + " " + child.text  
                        if len(childLeft) > 0:                 
                            ind = w.index(childLeft[0])
                        else:
                            ind = w.index(child.text)
                        agent = [ag, ind]

                        first = token.i
                        clNote = {"agent": agent}
                        evt = [clNote, first]
                        theComp.append(evt)
                   
                    elif child.pos_ == "VERB" and w.index(child.text) > w.index(token.text):
                        ag = ""
                        ind = -1
                        for headLeft in token.head.lefts:
                            if "subj" in headLeft.dep_:
                                subjLeft = [item.text for item in headLeft.lefts]
                                ag = ' '.join(subjLeft) + " " + headLeft.text
                                if len(subjLeft) > 0:                 
                                    ind = w.index(subjLeft[0])
                                else:
                                    ind = w.index(headLeft.text)

                        agent = [ag, ind]
                        
                        childLeft = [item.text for item in child.lefts]
                        verb = ' '.join(childLeft) + " " + child.text
                        
                        conj = {"agent": agent}

                        if len(childLeft) > 0:                 
                            ind = w.index(childLeft[0])
                        else:
                            ind = child.i
                        evt = [conj, ind]
                        theComp.append(evt)
                
               
            elif "cl" in token.dep_:
                first = token.i
                ag = ""
                event = ""
                ind = -1
                if token.pos_ == "VERB":
                    if token.head.pos_ == "NOUN":
                        subjLeft = [item.text for item in token.head.lefts]
                        ag = ' '.join(subjLeft) + " " + token.head.text 
                        ind = token.head.i
                elif token.pos_ == "NOUN":
                    for headLeft in token.head.children:
                        if headLeft.pos_ == "VERB":
                            subjLeft = [item.text for item in token.lefts]
                            ag = ' '.join(subjLeft) + " " + token.text
                            ind = token.i    
                            first = headLeft.i
                
                ag.rstrip()
                agent = [ag, ind]
                clNote = {"agent": agent}
                evt = [clNote, first]
                theComp.append(evt)
        except ValueError:
            pass   
    
    theComp.sort(key=lambda x:x[1])

    splitSent = []
    for i in range(len(theComp)):
        
        newSent = ""
        endInd = 0
        if i+1 < len(theComp):
            endInd = theComp[i+1][1] #get end index by checking the start index of next clause
        else:
            endInd = len(w) #len index is the number of word in sentence
        try:
            item = theComp[i][0]
            agentPos = item["agent"][1]
            
            if i==0:
                newSent = ' '.join(w[0:endInd])
            elif agentPos < theComp[i][1]:
                newSent = item["agent"][0] + " " + ' '.join(w[theComp[i][1]:endInd])
            else:
                newSent = ' '.join(w[theComp[i][1]:endInd])
            splitSent.append(newSent.strip())
        except:
            pass
            
    for i in range(len(splitSent)):
        splitSent[i] = deleteComponent(splitSent[i])
    
    
    while "" in splitSent:
        splitSent.remove("")
        
    return splitSent

delComp = {"what", "when", "while", "which", "that", "how", "where", "who", "whose", "whom",
           "and", "or", ",", "."}

def deleteComponent(sentence):
    wordToken = word_tokenize(sentence)
    doc = nlp(sentence)
    canDelete = []
    theComp = []
    for token in doc:
        if token.pos_ == "ADV":
            canDelete.append(token.text)
        elif token.text == "the" or token.text == "The":
            canDelete.append(token.text)
        
    try:
        for item in canDelete:
            wordToken.remove(item)
        
        while wordToken[len(wordToken)-1] in delComp:
            wordToken.remove(wordToken[len(wordToken)-1])   
              
    except:
        pass
    
    if len(wordToken) < 3:
        return ""
    
    result = ' '.join(wordToken)

    
    return result
