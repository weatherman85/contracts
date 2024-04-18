import re
from dateutil.parser import parse
from datetime import date
from normalization.normalizer import Normalizer
    
class DateNorm(Normalizer):
    def __init__(self):
        super().__init__()

    def process(self, ent):
        date_input = ent.name
        if not isinstance(date_input, date):
            date_string = str(date_input)
            if date_string.lower() != 'nan':
                date_from_parser = self.parse_date_string(date_string)
                if date_from_parser:
                    return date_from_parser.strftime("%Y-%m-%d")

                return self.custom_format_parsing(date_string).strftime("%Y-%m-%d")

        return date_input.strftime("%Y-%m-%d")

    def parse_date_string(self, date_string):
        try:
            return parse(date_string, fuzzy=True).date()
        except:
            return None

    def custom_format_parsing(self, date_string):
        try:
            date_string = re.sub(r"\d{5,}", "", date_string)
            for ch in ['th', 'rd', 'nd', 'day', 'of', 'k', 'q', 'w', 'x', 'z']:
                if ch in date_string.lower():
                    date_string = date_string.lower().replace(ch, '')
            return parse(date_string, fuzzy=True).date()
        except:
            return None