import joblib
from classification.classifier import Classifier

class SklearnClassifier(Classifier):
    def __init__(self, model=None, attribute=None,method=None,positive_class=None):
        super().__init__(model=None, attribute=attribute, positive_class=positive_class)
        if not model or not method:
            raise ValueError("Model path and method must be provided.")
        self.model = joblib.load(model)
        self.method = method

    def predict(self, contract, batch_size, text_range=None):
        if self.method == "document":
            text = contract.text
            if text_range:
                text = text[text_range[0]:text_range[1]]
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

        predictions = self.model.predict_proba(text)

        results = []
        for text_item, prediction in zip(text, predictions):
            label = prediction.argmax()  
            score = prediction[label]
            results.append((label, score, text_item))

        return results

    def __call__(self, contract, batch_size=5, text_range=None):
        return super().__call__(contract, batch_size=batch_size, text_range=text_range)