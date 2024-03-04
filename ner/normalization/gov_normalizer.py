from ner.normalization.normalizer import Normalizer

class GovNorm(Normalizer):
    def __init__(self,lookups):
        super().__init__()
        self.lookups = lookups
        
    def process(self,text):
        if str(text).lower() != 'nan':
            gov_law = self.lookups.get(text.lower().replace('\n'," "),text)
            return gov_law
        