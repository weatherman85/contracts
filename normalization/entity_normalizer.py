from normalization.normalizer import Normalizer
import rapidfuzz

class EntityNormalizer(Normalizer):
    def __init__(self,lookups):
        super().__init__()
        self.lookups = lookups
        
    def process(self,ent):
        ent - ''.join(e.lower() for e in ent if e.isalnum())
        res = rapidfuzz.process.cdist(ent,self.lookups,workers=-1)
        return res
    
        