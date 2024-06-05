import json

class BiLSTM_CRFConfig:
    """
    Configuration class for Bidirectional LSTM  CRFmodel for sequence labeling tasks.

    Args:
        num_labels (int): Number of distinct labels.
        labels (dict): Mapping of label ids to names
        hidden_size (int): Size of the hidden states in the LSTM.
        hidden_dropout_prob (float): Dropout probability for the LSTM.
        embedding_model (str): Name or path of the pre-trained embedding model to use.
        batch_first (bool, optional): Whether the input tensors have batch size as the first dimension.
            Defaults to True.
        use_crf (bool, optional): Whether to use additional CRF layer.
            Defaults to True.
    Attributes:
        num_labels (int): Number of distinct labels.
        labels (dict): Mapping of label ids to names
        hidden_size (int): Size of the hidden states in the LSTM.
        hidden_dropout_prob (float): Dropout probability for the LSTM.
        batch_first (bool): Whether the input tensors have batch size as the first dimension.
        embedding_model (str): Name or path of the pre-trained embedding model to use.
        use_crf (bool): Whether the model will use the CRF layer.
    Note:
        The `embedding_model` should be compatible with the `transformers` or `sentence-transformers` library.
    """

    def __init__(self, 
                 num_labels: int,
                 labels: dict, 
                 embedding_model: str, 
                 num_layers: int=2, 
                 dropout:int=0.2, 
                 batch_first:bool=True,
                 use_crf:bool=True):
        self.num_labels = num_labels
        self.labels = labels
        self.embedding_model = embedding_model
        self.num_layers = num_layers
        self.dropout = dropout
        self.batch_first = batch_first
        self.use_crf = use_crf

    def to_dict(self):
        return {
            'num_labels': self.num_labels,
            'labels': self.labels,
            'embedding_model': self.embedding_model,
            'num_layers': self.num_layers,
            'dropout': self.dropout,
            'batch_first': self.batch_first,
            "use_crf":self.use_crf
        }

    @classmethod
    def from_dict(cls, config_dict):
        return cls(
            num_labels=config_dict['num_labels'],
            labels=config_dict['labels'],
            embedding_model=config_dict['embedding_model'],
            num_layers=config_dict.get('num_layers', 2),
            dropout=config_dict.get('dropout', 0.2),
            batch_first=config_dict.get('batch_first', True),
            use_crf = config_dict.get("use_crf",True)
        )

    def save_config(self, path):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f)
        print(f"Configuration saved to {path}")

    @classmethod
    def load_config(cls, path):
        with open(path, 'r') as f:
            config_dict = json.load(f)
        print(f"Configuration loaded from {path}")
        return cls.from_dict(config_dict)