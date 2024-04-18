from normalization.normalizer import Normalizer
import pandas as pd

df = pd.read_csv(r"normalization\utils\gpe.csv",encoding="utf-8")
import numpy as np
gov_lookup = {}
for i, row in df.iterrows():
    if pd.isna(row["State/Province"]):
        gov_lookup[row["Country"]] = (row["Location"],row["Priority"])
    else:
        gov_lookup[row["State/Province"]] = (row["Location"],row["Priority"])

class GovNorm(Normalizer):
    def __init__(self,lookups:dict=None):
        super().__init__()
        if not lookups:
            self.lookups = gov_lookup
        else:
            self.lookups = lookups
        
    def process(self,ent):
        text = ent.name
        if str(text).lower() != 'nan':
            best_match = None
            best_priority = float('inf')  # Initialize with positive infinity
            for key, (value, priority) in self.lookups.items():
                if key.lower() in text.lower() and priority < best_priority:
                    best_match = value
                    best_priority = priority
            return best_match
                