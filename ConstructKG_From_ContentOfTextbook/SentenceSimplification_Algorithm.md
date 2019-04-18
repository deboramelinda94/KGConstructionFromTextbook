Sentence simplification is utilized to facilitate Subject-Predicate-Object detection, so that that the result can be obtained faster and accurately. 
One sentence may consist of one subject and multiple objects. 
The important of sentence simplification is to ensure that none of the subject and object is removed from the sentence. 
Therefore, the input of sentence simplification is one sentence, but the output is more than one sentence.

There are two steps in sentence simplification: 
1.splitting 
Splitting is done to obtain the clause with just one verb. Splitting is performed by analyzing the dependency parse tree of a sentence. 
Spacy library is utilized to obtain the dependency parse tree.

2.deletion
omit words that has no significance meaning such as adverb and conjunction 
