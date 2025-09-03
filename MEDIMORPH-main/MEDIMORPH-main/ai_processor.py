import re
import json
from datetime import datetime, timedelta
import numpy as np

class AIProcessor:
    def __init__(self):
        # Initialize with rule-based extraction only
        print("Using rule-based extraction for medication information")
        # Common medication names and their variations
        self.medication_database = {
            'aspirin': ['aspirin', 'acetylsalicylic acid', 'asa'],
            'ibuprofen': ['ibuprofen', 'advil', 'motrin', 'brufen'],
            'acetaminophen': ['acetaminophen', 'paracetamol', 'tylenol'],
            'amoxicillin': ['amoxicillin', 'amoxil', 'trimox'],
            'augmentin': ['augmentin'],
            'metformin': ['metformin', 'glucophage'],
            'lisinopril': ['lisinopril', 'prinivil', 'zestril'],
            'atorvastatin': ['atorvastatin', 'lipitor'],
            'omeprazole': ['omeprazole', 'prilosec'],
            'pand': ['pand'],
            'simvastatin': ['simvastatin', 'zocor'],
            'metoprolol': ['metoprolol', 'lopressor', 'toprol'],
            'losartan': ['losartan', 'cozaar'],
            'amlodipine': ['amlodipine', 'norvasc'],
            'hydrochlorothiazide': ['hydrochlorothiazide', 'hctz', 'microzide'],
            'pantoprazole': ['pantoprazole', 'protonix'],
            'carvedilol': ['carvedilol', 'coreg'],
            'furosemide': ['furosemide', 'lasix'],
            'spironolactone': ['spironolactone', 'aldactone'],
            'tramadol': ['tramadol', 'ultram'],
            'gabapentin': ['gabapentin', 'neurontin'],
            'duloxetine': ['duloxetine', 'cymbalta'],
            'enzoflam': ['enzoflam'],
            'hexigel': ['hexigel'],
            # Pediatric medications from prescription samples
            'calpol': ['calpol', 'syp calpol'],
            'delcon': ['delcon', 'syp delcon'],
            'levolin': ['levolin', 'syp levolin'],
        }
    # Add more methods as needed for AI processing
