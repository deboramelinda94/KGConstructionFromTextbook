import nltk
import re
from nltk.tokenize import word_tokenize, sent_tokenize
import math
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("english")
stop_words = set(stopwords.words('english'))

import nltk
import re
from nltk.tokenize import word_tokenize, sent_tokenize
import math
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("english")
stop_words = set(stopwords.words('english'))

def scoreByLength(sentColl, scoreArray):
    #first filter the length of the sentence
    longSent = []
    for i in range(len(sentColl)):
        tokens = word_tokenize(sentColl[i])
        longSent.append(len(tokens)) 
        
    maxV = max(longSent)
    maxV = 0.8*maxV
    for i in range(len(longSent)):
        if longSent[i] > maxV:
            scoreArray[i] += 0
        else:
            scoreArray[i] += 1
    
    return scoreArray

def scoreResembleTitle(title, sentColl, scoreArray):
    titleToken = word_tokenize(title)

    for i in range(len(sentColl)):
        t = word_tokenize(sentColl[i]) 
        countWordTitle = 0
        for j in range(len(t)):
            for k in range(len(titleToken)):
                if t[j] == titleToken[k]:
                    countWordTitle += 1
                        
        scoreResembTitle = countWordTitle / len(titleToken)
        scoreArray[i] += scoreResembTitle
        
        return scoreArray
    
def scoreByPosition(sentColl, scoreArray):   
    countSent = len(sentColl)
    midSent = math.ceil(countSent/2)
    
    if countSent % 2 == 1:
        themid = midSent -1
        for i in range(len(sentColl)-1, themid, -1):
            scoreArray[i] += countSent
            countSent -= 1
    else:
        themid = midSent    
        for i in range(len(sentColl)-1, themid-1, -1):
            scoreArray[i] += countSent
            countSent -= 1
    
    for i in range(themid):
        scoreArray[i] += countSent
        countSent -= 1
   
    return scoreArray

def scoreByTfidf(sentColl, scoreArray):
    index = defaultdict(list)
    tf = defaultdict(list)
    df = defaultdict(int)
    
    wordDict = {}
    for i in range(len(sentColl)):         
        filtered_tokens = []
        tokens = word_tokenize(sentColl[i])
        for token in tokens:
            if re.search('[a-zA-Z]', token):
                filtered_tokens.append(token)
        stems = [stemmer.stem(t) for t in filtered_tokens]
                     
        result = []
        for stem in stems:
            if stem not in stop_words:
                result.append(stem)
        
        for res in result:
            if not res in wordDict:
                wordDict[res] = [i]
            else:
                wordDict[res].append(i)
           
    norm = 0
    for term,posting in wordDict.items():
        norm +=len(posting)**2
    norm = math.sqrt(norm)
            
    for term, posting in wordDict.items():
        tf[term].append('%.4f'% (len(posting)/norm))
        df[term] += 1
        index[term].append(posting)        
           
    countTf = 0
    sumTfidf = 0
    tfidfDict = defaultdict(list)
    for term, tf in tf.items():
        for i in range(len(tf)):
            countTf += 1
            idfScore = math.log(len(sentColl)/(df[term]),2)
            tfScore = float(tf[i])
            tfidfScore = tfScore * idfScore
            sumTfidf += tfidfScore
            tfidfDict[term].append(tfidfScore)
    
     
    avgTfidf = sumTfidf / countTf
    
    for term, score in tfidfDict.items():     
        for i in range(len(score)):
            pos = index[term][0]
            for sentIndex in pos:
                scoreArray[sentIndex] += score[i]
    
    return scoreArray

def summarize(theParagraph, title, gloss):
    scoreArray = [0]*len(theParagraph)   
    scoreArray = scoreByLength(theParagraph, scoreArray)
    scoreArray = scoreResembleTitle(title, theParagraph, scoreArray)
    scoreArray = scoreByPosition(theParagraph, scoreArray)
    scoreArray = scoreByTfidf(theParagraph, scoreArray)
    
    dictArr = {}
    sum = 0
    for val in scoreArray:
        sum += val
    avg = sum / len(scoreArray)
    
    filterSent = []
    flag = False

    for i in range(len(scoreArray)):     
        if flag:
            flag = False
            continue
        
        if scoreArray[i] > avg:
            filterSent.append(i) #return the index of sentence in paragraf
    
    return filterSent
