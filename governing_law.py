import re
from named_entity import NamedEntity,Entities,RegexNER
from transformers import AutoTokenizer
from clf_ner import ClassifierNER
from named_entity import Entities

governing_law_rules=[(r"\b([A-Z][a-z]+\s)+([Ll]aws?|[Cc]ourts?)", "GOVERNING_LAW"),
                   ##captures items like "English law" and "Luxembourg courts")
                   (
                   r"\b([Ll]aws?\s|[Cc]ourts?\s)(of|for|in|located in|sitting in|residing in|situated in|located within|of or in)?\s(([Tt]he)? ([Ss]tate of\s|[Pp]rovince of\s|[Cc]ommonwealth of\s|[Cc]ity of\s))?([A-Z]\w*[,.]?\s){1,3}",
                   "GOVERNING_LAW")  ##Captures "courts/laws of "
                   ]

effective_date_rules = [(r"(?:effective|dated|made)*? (?:as of|on)*? ((?:\d{1,2}[-/th|st|nd|rd\s]*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|Decmebter)?[a-z\s,.]*(?:\d{1,2}[-/th|st|nd|rd)\s,]*)+(?:\d{2,4})+)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated|made)*? (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated|made)*? (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated|made)*? (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(day)\s*(of)\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated|made)*? (?:as of|on)*? (January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated|made)*? (?:as of|on)*?  ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*of\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE"),
                   (
                   r"(?:effective|dated|made)*? (?:as of|on)*?  (January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                   "EFFECTIVE_DATE")]

def regex_gov_law(doc) -> Entities:
    gov_law_ner = RegexNER()
    gov_law_ner.load_raw_rules(governing_law_rules)
    ents = None    
    for segment in doc.segments:
        text = segment.text
        title = segment.title
        print
        if title != None:
            print(title)
            if any(["law","jurisdicition","governing"] in title.lower().split()):
                print(title)
                ents = gov_law_ner(text)
    # if not ents:
    #     for segment in doc.segments:
    #         text = segment.text
    #         ents = gov_law_ner(text)    
    return ents



def gov_law_clf_ner(doc) -> Entities:
    ents = Entities()
    tokenizer = AutoTokenizer.from_pretrained("sguarnaccio/gov_law_clf_ner")
    model = ClassifierNER.from_pretrained("sguarnaccio/gov_law_clf_ner")

    for segment in doc.segments:
        text = segment.text
        title = segment.title

        if title is not None and any(keyword in title.lower().split() for keyword in ["law", "jurisdiction", "governing"]):
            res = model.predict(text)
            classification, entities = res["classification"], res["entities"]

            if classification == "Governing Law":
                for ent in entities:
                    named_ent = NamedEntity(
                        name=ent["entity"],
                        label=ent['label'],
                        start=ent['start'] + segment.start,
                        end=ent["end"] + segment.start
                    )
                    ents.append(named_ent)

    return ents
