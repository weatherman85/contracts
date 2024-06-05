import enum

class CRF_FEATURE_TYPES(enum.Enum):
    SHAPE = 0
    BAG = 1
    PRE_SUFFIX = 2
    SYNTAX = 3
    SENTENCE = 4
    REGEX = 5
    DICTIONARY = 6
    EMBEDDING = 7
    
class FeatureExtractor(object):    
    def __init__(self,
                 parameters=None) -> None:
        self.features = None
    
    def extract(self,sentence):
        self.features = [dict() for t in sentence]
        return self.features    
    
    def update(self,
               idx: int,
               feature_name: str,
               feature_value):
        if idx > len(self.features):
            return
        self.features[idx][feature_name] = feature_value