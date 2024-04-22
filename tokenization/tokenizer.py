import spacy
from spacy.tokens import Doc, Token, Span
import string

# Set extensions on the Doc, Token and Span
Token.set_extension("bbox", default=None, force=True)

class Tokenizer(object):
    def __init__(self, tokenizer=None, default=True):
        if default:
            self.tokenizer = spacy.blank("en").tokenizer
        else:
            self.tokenizer = tokenizer
    
    def preprocess_text(self, text):
        # Remove punctuation marks from the text
        return text.translate(str.maketrans('', '', string.punctuation))

    def align_words_to_bbox(self, tokens, bbox_info):
            aligned_tokens = []
            word_index = 0  # Initialize word index
            for token in tokens:
                # Find the bbox information corresponding to the token
                bboxes = self.find_bbox_for_token(token, bbox_info)
                if bboxes:
                    for bbox in bboxes:
                        token._.bbox = bbox

    def find_bbox_for_token(self, token, bbox_info):
        bboxes = []
        token_text = self.preprocess_text(token.text)
        for page_num, page_data in enumerate(bbox_info, start=1):
            for i, text in enumerate(page_data["text"]):
                bbox_text = self.preprocess_text(text)
                if bbox_text.strip() == token_text.strip():
                    bbox = {
                        "page": page_num,  # Add the page number
                        "left": page_data["left"][i],
                        "top": page_data["top"][i],
                        "width": page_data["width"][i],
                        "height": page_data["height"][i]
                    }
                    self.merge_bbox(bboxes, bbox)
        return bboxes
    
    def merge_bbox(self, bboxes, new_bbox):
        merged = False
        for bbox in bboxes:
            if self.are_bboxes_overlapping(bbox, new_bbox) or self.are_bboxes_adjacent(bbox, new_bbox):
                # Merge new_bbox into bbox
                bbox["left"] = min(bbox["left"], new_bbox["left"])
                bbox["top"] = min(bbox["top"], new_bbox["top"])
                bbox["width"] = max(bbox["left"] + bbox["width"], new_bbox["left"] + new_bbox["width"]) - bbox["left"]
                bbox["height"] = max(bbox["top"] + bbox["height"], new_bbox["top"] + new_bbox["height"]) - bbox["top"]
                merged = True
                break
        if not merged:
            bboxes.append(new_bbox)

    def are_bboxes_overlapping(self, bbox1, bbox2):
        x_overlap = max(0, min(bbox1["left"] + bbox1["width"], bbox2["left"] + bbox2["width"]) - max(bbox1["left"], bbox2["left"]))
        y_overlap = max(0, min(bbox1["top"] + bbox1["height"], bbox2["top"] + bbox2["height"]) - max(bbox1["top"], bbox2["top"]))
        return x_overlap > 0 and y_overlap > 0

    def are_bboxes_adjacent(self, bbox1, bbox2):
        x_distance = abs((bbox1["left"] + bbox1["width"]) - bbox2["left"]) if bbox1["left"] < bbox2["left"] else abs((bbox2["left"] + bbox2["width"]) - bbox1["left"])
        y_distance = abs((bbox1["top"] + bbox1["height"]) - bbox2["top"]) if bbox1["top"] < bbox2["top"] else abs((bbox2["top"] + bbox2["height"]) - bbox1["top"])
        return x_distance <= 1 or y_distance <= 1

    def __call__(self, contract):
        contract.tokens = [token for token in self.tokenizer(contract.text)]
        # contract.aligned_tokens = self.align_words_to_bbox(contract.tokens, contract.bbox_info)
        return contract

