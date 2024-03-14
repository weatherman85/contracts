import json
import spacy
from typing import List
from spacy.training import offsets_to_biluo_tags, biluo_to_iob
from tqdm import tqdm


nlp = spacy.blank("en")


def doccano_to_iob(data: List[dict]) -> List[tuple]:
    formatted_data = []
    for d in tqdm(data):
        text = d['text']
        entities = d['label']
        doc = nlp(text)
        offsets = [(start, end, label) for start, end, label in entities]
        ents = offsets_to_biluo_tags(doc, offsets)
        ents = biluo_to_iob(ents)
        formatted_data.append((text, [token.text for token in doc], ents))
    return formatted_data