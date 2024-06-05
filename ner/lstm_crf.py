from typing import List, Optional, Tuple, Dict, Union, Generator
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn as nn
from torchcrf import CRF
from sentence_transformers import SentenceTransformer
from ner.lstm_config import BiLSTM_CRFConfig
from ner.named_entity_recognizer import NamedEntityRecognizer
from ner.named_entity import NamedEntity

class BiLSTM_CRF(nn.Module):
    """
    Bidirectional LSTM model for sequence labeling tasks.

    Args:
        config (BiLSTM_CRFConfig): Configuration file for BiLSTM class

    Attributes:
        num_labels (int): Number of distinct labels.
        labels (dict): Mapping of label ids to names.
        hidden_size (int): Size of the hidden states in the LSTM.
        batch_first (bool): Whether the input tensors have batch size as the first dimension.
        embedding_model (transformers.AutoModel): Pre-trained transformer model for embeddings.
        tokenizer (transformers.AutoTokenizer): Tokenizer associated with the pre-trained model.
        linear (torch.nn.Linear): Linear layer for label prediction.
        lstm (torch.nn.LSTM): Bidirectional LSTM layer.
        crf (torchcrf.CRF): Conditional Random Field Layer
    """
    def __init__(self, config):
        super(BiLSTM_CRF, self).__init__()
        self.config = config
        
        self.embedding_model = AutoModel.from_pretrained(config.embedding_model)
        self.tokenizer = AutoTokenizer.from_pretrained(config.embedding_model)
        self.hidden_size = self.embedding_model.config.hidden_size
        
        for param in self.embedding_model.parameters():
            param.requires_grad = False

        self.num_labels = config.num_labels
        self.labels = config.labels        
        self.batch_first = config.batch_first
        self.embedding_type = config.embedding_type
        self.num_layers = config.num_layers
        self.dropout = config.dropout
        self.use_crf = config.use_crf
        self.lstm = nn.LSTM(input_size=self.hidden_size, hidden_size=self.hidden_size // 2,
                            num_layers=self.num_layers, dropout=self.dropout, batch_first=self.batch_first, bidirectional=True)
        
        self.linear = nn.Linear(self.hidden_size, self.num_labels)
        self.drop = nn.Dropout(self.dropout)
        self.crf = CRF(self.num_labels, batch_first=self.batch_first) if self.use_crf else None
        self.loss_fct = nn.CrossEntropyLoss()

    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None,
                labels: Optional[torch.LongTensor] = None) -> Tuple[torch.Tensor, torch.Tensor, List[List[int]]]:
        
        with torch.no_grad():
            outputs = self.embedding_model(input_ids=input_ids, attention_mask=attention_mask)
            embeddings = outputs.last_hidden_state
        
        lstm_outputs, _ = self.lstm(embeddings)
        lstm_outputs = self.drop(lstm_outputs)
        logits = self.linear(lstm_outputs)
        
        if labels is not None:
            if not self.use_crf:
                loss = self.loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
                return logits, loss.mean()
            else:
                is_pad = labels == -100
                labels = labels.masked_fill(is_pad, 0)
                loss = -self.crf(logits, labels, mask=attention_mask.bool())
                normalized_loss = loss / torch.sum(attention_mask)
                tags = self.crf.decode(logits, mask=attention_mask.bool())
                return logits, normalized_loss.mean(), tags
        else:
            if not self.use_crf:
                return logits
            else:
                tags = self.crf.decode(logits, mask=attention_mask.bool())
                return logits, tags

    def predict(self, text):
        with torch.no_grad():
            tokenized = self.tokenizer.encode_plus(text, truncation=True, max_length=512,
                                                    return_tensors="pt", return_offsets_mapping=True)
            if not self.use_crf:
                logits = self(tokenized['input_ids'], tokenized['attention_mask'])            
                aligned_predictions = self.align_predictions(text, logits, tokenized['offset_mapping'])
            else:
                logits, tags = self(tokenized['input_ids'], tokenized['attention_mask'])      
                aligned_predictions = self.align_predictions(text, tags, tokenized['offset_mapping'])
        return aligned_predictions

    def align_predictions(self, text, logits_or_tags, offsets):
        results = []
        if self.use_crf:
            predictions = logits_or_tags[0]  # tags
        else:
            predictions = torch.argmax(logits_or_tags, dim=-1)[0].tolist()
        offsets = offsets[0].tolist()
        idx = 0
        
        while idx < len(predictions):
            tag = predictions[idx]
            label = self.labels[tag]
            
            if label != "O":
                label = label[2:]
                start, end = offsets[idx]
                idx += 1
                while idx < len(predictions) and self.labels[predictions[idx]] == f"I-{label}":
                    _, end = offsets[idx]
                    idx += 1
                word = text[start:end]
                results.append({"label": label, "entity": word, "start": start, "end": end})
            idx += 1
        
        return results

    def save_model(self, path: str):
        model_state = {
            'model_state_dict': self.state_dict(),
            'config': self.config.to_dict()
        }
        torch.save(model_state, path)
        print(f"Model and configuration saved to {path}")

    @classmethod
    def load_model(cls, path: str):
        model_state = torch.load(path, map_location=torch.device('cpu'))
        config = BiLSTM_CRFConfig.from_dict(model_state['config'])
        model = cls(config)
        model.load_state_dict(model_state['model_state_dict'])
        print(f"Model and configuration loaded from {path}")
        return model
    
class BILSTM_NER(NamedEntityRecognizer):
    """
    BILSTM_NER is a named entity recognizer that uses a BiLSTM model for predictions.

    Args:
        model (str): Path to the pre-trained BiLSTM model.
        keywords (Optional[List[str]]): List of keywords for the NamedEntityRecognizer. Defaults to None.
        normalizer (Optional[Callable[[str], str]]): Function to normalize text. Defaults to None.

    Attributes:
        model (BiLSTM): The loaded BiLSTM-CRF model.
    
    Methods:
        predict(text: str) -> Generator[NamedEntity, None, None]:
            Predicts named entities in the given text.
        
        __call__(text: str) -> List[NamedEntity]:
            Calls the predict method and returns the results.
    """

    def __init__(self, model: str, 
                 keywords: Optional[list] = None, 
                 normalizer: Optional[callable] = None):
        super().__init__(keywords=keywords, normalizer=normalizer)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = BiLSTM_CRF.load_model(model)
        self.model.to(device)

    def predict(self, text: str) -> Generator[NamedEntity, None, None]:
        """
        Predicts named entities in the given text.

        Args:
            text (str): The input text to process.

        Yields:
            NamedEntity: A named entity found in the text.
        """
        res = self.model.predict(text)
        clf_prediction = res["classification"]
        ner_prediction = res["entities"]
        if clf_prediction != "Negative":
            for ent in ner_prediction:
                named_ent = NamedEntity(
                    name=ent["entity"],
                    label=ent['label'],
                    start=ent['start'],
                    end=ent["end"]
                )
                yield named_ent

    def __call__(self, text: str) -> list:
        """
        Calls the predict method and returns the results.

        Args:
            text (str): The input text to process.

        Returns:
            List[NamedEntity]: A list of named entities found in the text.
        """
        return list(self.predict(text))