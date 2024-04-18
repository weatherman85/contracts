from transformers import pipeline
from classification.classifier import Classifier
import torch
class TransformersClassifier(Classifier):
    def __init__(self, model=None, attribute=None, method=None, positive_class=None,normalizer=None):
        super().__init__(model=model, attribute=attribute, positive_class=positive_class,normalizer=normalizer)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = pipeline("text-classification", model=model,device=device)
        self.method = method

    def predict(self, contract, batch_size, text_range=None):
        results = []

        if self.method == "document":
            text = contract.text
            if text_range:
                text = text[text_range[0]:text_range[1]]
            pred = self.model(text, truncation=True)
            for result in pred:
                results.extend([(result["label"], result["score"], None)])
        elif self.method == "sentences":
            text = contract.sentences.text            
        elif self.method == "lines":
            text = contract.text.split("\n")
        elif self.method == "segments":
            text = contract.segments.text
        else:
            raise ValueError("Unsupported classification method.")
        if text_range:
            text = text[text_range[0]:text_range[1]]
        for i in range(0, len(text), batch_size):
            batch_texts = text[i:i + batch_size]
            batch_results = self.model(batch_texts, truncation=True)
            for text, result in zip(batch_texts, batch_results):
                results.extend([(result["label"], result["score"], text)])

        return results

    def __call__(self, contract, batch_size=5, text_range=None):
        return super().__call__(contract, batch_size=batch_size, text_range=text_range)