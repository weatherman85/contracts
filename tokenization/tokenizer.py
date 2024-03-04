import spacy

class Tokenizer(object):
    def __init__(self,tokenizer=None,default=True):
        if default:
            self.tokenizer = spacy.blank("en").tokenizer
        else:
            self.tokenizer = tokenizer
    def __call__(self,
                 contract):
        contract.tokens = [token for token in self.tokenizer(contract.text)]
        return contract