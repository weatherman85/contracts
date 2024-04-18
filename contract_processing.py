import os
from ner.clf_ner import CLF_NER
from ner.regex_ner import RegexNER
from normalization.date_normalizer import DateNorm
from normalization.gov_normalizer import GovNorm
from normalization.lang_normalizer import LangNorm
from normalization.entity_normalizer import EntityNormalizer
from classification.transformer_classifier import TransformersClassifier
from classification.sklearn_classifier import SklearnClassifier
from ner.transformer_ner import TransformersNER
from contract import ContractPipeline
from utils import generate_annotations
import streamlit as st

class ContractData:
    def __init__(self, contract_type, language, effective_dates, governing_laws, sections, glossary, counterparties):
        self.contract_type = contract_type
        self.language = language
        self.effective_dates = effective_dates
        self.governing_laws = governing_laws
        self.sections = sections
        self.glossary = glossary
        self.counterparties = counterparties

def create_contract_pipeline():
    pipeline = ContractPipeline(defaults=True)
    if st.sidebar.checkbox("Document Language Classifier (Linear SVM)"):
        language_classifier = SklearnClassifier(
            model="./classification/pretrained/document_language_model.pkl",
            attribute="language",
            method="lines",
            positive_class="multi",
            normalizer=LangNorm()
        )
        model = language_classifier.model["Linear SVM"]
        language_classifier.model = model["model"]
        language_classifier.label_encoder = model["label_encoder"]
        pipeline.add_pipe(
            name="language_classifier",
            component=language_classifier,
            before="tokenizer",
            params={"text_range": (0, 50)}
        )
    if st.sidebar.checkbox("Governing Law (BERT)"):
        gov_law_ner = CLF_NER(keywords=["law", "jurisdicition", "governing"],
                              model="sguarnaccio/gov_law_clf_ner", normalizer=GovNorm())
        pipeline.add_pipe(name="governing_law", component=gov_law_ner)
    if st.sidebar.checkbox("Effective Dates (Regex)"):
        effective_date_rules = [(
            r"(?:effective|dated) (?:as of|on)*? ((?:\d{1,2}[-/th|st|nd|rd\s]*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|Decmebter)?[a-z\s,.]*(?:\d{1,2}[-/th|st|nd|rd)\s,]*)+(?:\d{2,4})+)",
            "EFFECTIVE_DATE"),
            (
                r"(?:effective|dated) (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*(?<!\d)([12][0-9]{3})(?!\d)",
                "EFFECTIVE_DATE"),
            (
                r"(?:effective|dated) (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                "EFFECTIVE_DATE"),
            (
                r"(?:effective|dated) (?:as of|on)*? ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*(day)\s*(of)\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                "EFFECTIVE_DATE"),
            (
                r"(?:effective|dated) (?:as of|on)*? (January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                "EFFECTIVE_DATE"),
            (
                r"(?:effective|dated) (?:as of|on)*?  ((?<!\d)([1-9]|([12][0-9])|(3[01]))(?!\d))((?<=1)st|(?<=2)nd|(?<=3)rd|(?<=[0456789])th|\"|°)?\s*of\s*(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                "EFFECTIVE_DATE"),
            (
                r"(?:effective|dated) (?:as of|on)*?  (January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*[,\.]\s*(?<!\d)([12][0-9]{3})(?!\d)",
                "EFFECTIVE_DATE")]
        eff_date_ner = RegexNER(normalizer=DateNorm())
        eff_date_ner.load_raw_rules(effective_date_rules)
        pipeline.add_pipe(name="effective_date", component=eff_date_ner)
    if st.sidebar.checkbox("Currency (Regex)"):
        currency_rules = [(
            r"(?P<currency>[\$£€¥₹]|(?:USD|US Dollar|GBP|British Pound|EUR|Euro|JPY|Japanese Yen|INR|Indian Rupee|CAD|Canadian Dollar|AUD|Australian Dollar|CHF|Swiss Franc|CNY|Chinese Yuan|SGD|Singapore Dollar|NZD|New Zealand Dollar|HKD|Hong Kong Dollar|SEK|Swedish Krona|NOK|Norwegian Krone|KRW|South Korean Won|MXN|Mexican Peso|BRL|Brazilian Real|TRY|Turkish Lira|ZAR|South African Rand|IDR|Indonesian Rupiah|MYR|Malaysian Ringgit|PHP|Philippine Peso|THB|Thai Baht|HUF|Hungarian Forint|CZK|Czech Koruna|ILS|Israeli New Shekel|PLN|Polish Złoty|DKK|Danish Krone|AED|United Arab Emirates Dirham|SAR|Saudi Riyal|RON|Romanian Leu|RUB|Russian Ruble|CLP|Chilean Peso|TWD|New Taiwan Dollar|ARS|Argentine Peso|COP|Colombian Peso|VND|Vietnamese Đồng|NGN|Nigerian Naira|UAH|Ukrainian Hryvnia|EGP|Egyptian Pound|QAR|Qatari Riyal|BDT|Bangladeshi Taka|PKR|Pakistani Rupee|PEN|Peruvian Sol))\s*(?P<amount>[0-9]+(?:[,.][0-9]{3})*(?:[,.][0-9]+)?)",
            "currency")]
        currency_ner = RegexNER()
        currency_ner.load_raw_rules(currency_rules)
        pipeline.add_pipe(name="currency", component=currency_ner)
    if st.sidebar.checkbox("Document Type Classifier (Linear SVM)"):
        document_type_classifier = SklearnClassifier(
            model="./classification/pretrained/document_type_model.pkl",
            method="lines",
            positive_class=1,
            attribute="document_type")
        document_type_classifier.model = document_type_classifier.model["Linear SVM"]["model"]
        pipeline.add_pipe(name="document_type_classifier", component=document_type_classifier, params={"text_range": (0, 15)})
    if st.sidebar.checkbox("Counterparties and Signatories (BERT)"):
        le_ner = TransformersNER(keywords=["signature"], model="sguarnaccio/le_signatory", normalizer=EntityNormalizer())
        pipeline.add_pipe(name="legal_entities", component=le_ner)
    return pipeline

@st.cache_resource
def process_contract(text_file):
    pipeline = create_contract_pipeline()
    bytes_data = text_file.read()
    file_path = f"tmp/{text_file.name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(bytes_data)
    doc = pipeline(file_path)
    effective_dates = list(set([ent.normalized for ent in doc.ents if ent.label == "EFFECTIVE_DATE"]))
    governing_laws = list(set([ent.normalized for ent in doc.ents if ent.label == "gov_law"]))
    sections = [(segment.section, segment.subsection, segment.title, segment.text, segment.start, segment.end)
                for segment in doc.segments]
    glossary = [df for df in doc.glossary]
    counterparties = list(set([ent for ent in doc.ents if ent.label == "legal_entity"]))
    return ContractData(doc.document_type, doc.language, effective_dates, governing_laws, sections, glossary, counterparties)

def generate_html(html, start, entities):
    highlighted_html, entity_info = annotate_entities(html, start, entities)
    for info in entity_info:
        if isinstance(info["normalized"], date):
            info["normalized"] = info["normalized"].strftime("%Y-%m-%d")
    entity_info_str = json.dumps(entity_info)
    WRAPPER = f"""
    <div id="annotated-text" style="white-space: pre-wrap; overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{highlighted_html}</div>
    """
    return WRAPPER.strip(), entity_info_str
