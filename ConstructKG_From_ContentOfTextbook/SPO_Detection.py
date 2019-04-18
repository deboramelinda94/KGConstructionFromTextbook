#adapted from https://github.com/peter3125/enhanced-subject-verb-object-extraction

import en_core_web_sm
nlp = en_core_web_sm.load()

SUBJECTS = {"nsubj", "nsubjpass", "agent"}
OBJECTS = {"dobj", "dative", "attr", "oprd"}
BREAKER_POS = {"CCONJ", "VERB"}
NEGATIONS = {"no", "not", "n't", "never", "none"}
NOUNS = {"NOUN", "PROPN", "PRON"}

def contains_conj(token):
    for tok in token:
        if tok.dep_ == "cc" or tok.dep_ == "conj":
            return True
    return False

def _get_subs_from_conjunctions(subs):
    more_subs = []
    for sub in subs:
        rights = list(sub.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if contains_conj(rights):
            more_subs.extend([tok for tok in rights if tok.dep_ in SUBJECTS or tok.pos_ == "NOUN"])
            if len(more_subs) > 0:
                more_subs.extend(_get_subs_from_conjunctions(more_subs))
    return more_subs

def _get_objs_from_conjunctions(objs):
    more_objs = []
    for obj in objs:
        rights = list(obj.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if contains_conj(rights):
            more_objs.extend([tok for tok in rights if tok.dep_ in OBJECTS or tok.pos_ == "NOUN"])
            if len(more_objs) > 0:
                more_objs.extend(_get_objs_from_conjunctions(more_objs))
        
    return more_objs
    
def _is_negated(tok):
    parts = list(tok.lefts) + list(tok.rights)
    for dep in parts:
        if dep.lower_ in NEGATIONS:
            return True
    return False

def _get_head_noun(tok):
    if tok.pos_ in NOUNS:
        return tok
    else:
        if tok == tok.head:
            lefts = list(tok.lefts)
            for token in lefts:
                if tok.pos_ in NOUNS:
                    return tok
            return None
        tok = tok.head
        return _get_head_noun(tok)
 
def _get_all_subs(v):
    verb_negated = _is_negated(v)
    subs = []
    for tok in v.lefts:
        if tok.dep_ in SUBJECTS:
            if tok.pos_ in NOUNS:
                subs.append(tok)
    
    if len(subs) > 0:
        subs.extend(_get_subs_from_conjunctions(subs))
    else:
        for tok in v.lefts:
            if tok.dep_ in SUBJECTS:
                if tok.pos_ in NOUNS:
                    subs.append(tok)
                else:
                    headNoun = _get_head_noun(tok)
                    if headNoun != None:
                        subs.append(headNoun)
    return subs, verb_negated
    
def _is_non_aux_verb(tok):
      return tok.pos_ == "VERB" and (tok.dep_ != "aux" and tok.dep_ != "auxpass")
    
def _get_all_objs(v, is_pas):
    rights = list(v.rights)
    objs = []
    for tok in rights:
        if is_pas:
            if tok.dep_ == "agent":
                rightBy = list(tok.rights)
                for token in rightBy: 
                    if token.dep_ == 'pobj':
                        objs.append(token)
        if tok.dep_ in OBJECTS:
            objs.append(tok)
        elif tok.dep_ == "prep":
            rightBy = list(tok.rights)
            for token in rightBy: 
                if token.dep_ == 'pobj':
                    objs.append(token)
                   
    if len(objs) > 0:
        objs.extend(_get_objs_from_conjunctions(objs))
    return v, objs

def _is_passive(tokens):
    for tok in tokens:
        if tok.dep_ == "auxpass":
            return True
    return False

def _get_lemma(word: str):
    tokens = nlp(word)
    if len(tokens) == 1:
        return tokens[0].lemma_
    return word

#get the modifier of the token
def expand(item, tokens):
    parts = []
    
    if len(parts) > 3:
        return parts
    if hasattr(item, 'lefts'):
        for part in item.lefts:
            if part.pos_ in BREAKER_POS and part.dep_ != "amod":
                break
            if not part.lower_ in NEGATIONS and part.pos_ != "DET" and part.dep_ != "prep":
                parts.append(part)

    parts.append(item)
    
    tempParts = parts

    if hasattr(item, 'rights'):
        for part in item.rights:
            if part.pos_ in BREAKER_POS and part.dep_ != "amod":
                break
            if not part.lower_ in NEGATIONS and part.pos_ != "DET" and part.dep_ != "prep" or part.text == "of":
                parts.append(part)
                break #only allow 1 right

    if hasattr(parts[-1], 'rights'): 
        for item2 in parts[-1].rights:
            if item2.pos_ == "NOUN":
                partInpart = expand(item2, tokens)
                for p in partInpart:              
                    parts.append(p)
            break                 
          
    if hasattr(parts[0], 'lefts'):
        for item2 in parts[0].lefts:
            if item2.pos_ == "NOUN":
                partInpart = expand(item2, tokens)
                for p in partInpart:              
                    parts.insert(0, p)
            break
        
    if item.head.dep_ == "prep":
        parts.insert(0, item.head)
            
    if parts[-1].dep_ == "prep":
        del parts[-1]
        
    return parts


# convert a list of tokens to a string
def to_str(tokens):
    thePrep = ""
    if len(tokens) == 0:
        return ""
    else:
        arrayDep = [token.dep_ for token in tokens]
        arrayText = [item.text for item in tokens]
        
        if "prep" in arrayDep:
            if "of" in arrayText:
                countOf = arrayText.count("of")
                if countOf > 1:
                    arrayText.remove("of")
            else:
                indPrep = arrayDep.index("prep")
                thePrep = arrayText[indPrep]
                arrayText = arrayText[indPrep+1:]
        
        if "of" in arrayText:
            indOf = arrayText.index("of")
            arrayText = arrayText[indOf+1:]
            
        text = ' '.join(arrayText)
        try:
            while text[-1].isalpha() == False:
                text = text[:len(text)-2]
        except:
            pass
        return [text, thePrep]
    
def findSVOs(tokens):
    svos = []
    is_pas = _is_passive(tokens)
    verbs = [tok for tok in tokens if _is_non_aux_verb(tok)]
    
    for v in verbs:   
        subs, verbNegated = _get_all_subs(v)
 
        if len(subs) > 0:
            v, objs = _get_all_objs(v, is_pas)
            for sub in subs:            
                for obj in objs:
                    objNegated = _is_negated(obj)                     
                       
                    if is_pas:  # reverse object / subject for passive
                        s = to_str(expand(obj, tokens))[0]
                        prep = to_str(expand(obj, tokens))[1]                        
                        o = to_str(expand(sub, tokens))[0]   
                        
                        if prep != "":
                            verb = v.lemma_ + " " + prep
                        else:
                            verb = v.lemma_
                        svos.append([s,verb,o])  
                                           
                    else:
                        s = to_str(expand(sub, tokens))[0]
                        o = to_str(expand(obj, tokens))[0] 
                        prep = to_str(expand(obj, tokens))[1]          
                        
                        if prep != "":
                            verb =  v.lemma_ + " " + prep
                        else:
                            verb = v.lemma_ 
                        
                        svos.append([s,verb,o])  
                                           
    return svos
