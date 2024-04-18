from normalization.normalizer import Normalizer
import requests

class EntityNormalizer(Normalizer):
    def __init__(self,lookups=None):
        super().__init__()
        self.lookups = lookups
        
    def process(self,ent):
        normalized = ent.name.title()
        # Query GLEIF API
        gleif_api_url = f"https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]={normalized}"
        response = requests.get(gleif_api_url)
        ## TODO ensure that matches are above a certain threshold or ignore 
        if response.status_code == 200:
            gleif_data = response.json()
            if len(gleif_data["data"]) >0:
                if ''.join(e.lower() for e in normalized if e.isalnum()) == ''.join(e.lower() for e in gleif_data["data"][0]["attributes"]["entity"]["legalName"]["name"] if e.isalnum()):
                    ent.lei_info = gleif_data["data"][0]["attributes"]
        return normalized
                
        