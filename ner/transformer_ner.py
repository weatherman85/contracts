from ner.named_entity_recognizer import NamedEntityRecognizer
from ner.named_entity import NamedEntity
from transformers import pipeline
import torch

class TransformersNER(NamedEntityRecognizer):
    def __init__(self, model=None, keywords=None, normalizer=None):
        super().__init__(keywords=keywords, normalizer=normalizer)
        # device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = pipeline("ner",model,aggregation_strategy="max",device="cpu")
    

    def predict(self, text):
        ner_prediction =  self.model(text)
        # print(ner_prediction)
        for ent in ner_prediction:
                named_ent = NamedEntity(
                    name=ent["word"],
                    label=ent["entity_group"],
                    start=ent['start'],
                    end=ent["end"]
                )
                yield named_ent
                
    def __call__(self, text):
        return super().__call__(text)