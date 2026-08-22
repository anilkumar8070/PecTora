import re

class VoiceNormalizer:
    """Normalizes Indian cultural and monetary phrases into strict numeric values."""
    
    @staticmethod
    def normalize_monetary_expressions(text: str) -> str:
        # We don't want to lose case sensitivity for names, but we need case-insensitive regex
        
        def replace_hazaar(match):
            num_str = match.group(1).replace(',', '')
            return str(int(float(num_str) * 1000))
            
        def replace_lakh(match):
            num_str = match.group(1).replace(',', '')
            return str(int(float(num_str) * 100000))
            
        def replace_crore(match):
            num_str = match.group(1).replace(',', '')
            return str(int(float(num_str) * 10000000))

        # Handle hazaar / k
        text = re.sub(r'\b(\d+(?:\.\d+)?)\s*(?:hazaar|hazar|k)\b', replace_hazaar, text, flags=re.IGNORECASE)
        
        # Handle lakh / lac
        text = re.sub(r'\b(\d+(?:\.\d+)?)\s*(?:lakh|lac|lacs|lakhs)\b', replace_lakh, text, flags=re.IGNORECASE)
        
        # Handle crore / cr
        text = re.sub(r'\b(\d+(?:\.\d+)?)\s*(?:crore|cr|crores)\b', replace_crore, text, flags=re.IGNORECASE)
        
        # Normalize "rupees 42000" or "42000 rupees" -> "₹42000"
        text = re.sub(r'\b(?:rupees|rs\.?|inr)\s+(\d+)\b', r'₹\1', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+)\s+(?:rupees|rs\.?|inr)\b', r'₹\1', text, flags=re.IGNORECASE)
        
        # Remove commas from numerical values for cleaner LLM extraction
        text = re.sub(r'(?<=\d),(?=\d{3}\b)', '', text)
        
        return text

    @staticmethod
    def normalize_time_expressions(text: str) -> str:
        """Converts Hinglish time expressions into normalized English representations."""
        # Simple word boundary replacements
        time_map = {
            r'\baaj\b': 'today',
            r'\bkal\b': 'tomorrow',  # Usually future in negotiation contexts
            r'\bparso\b': 'day after tomorrow',
            r'\bsubah\b': 'morning',
            r'\bdopahar\b': 'afternoon',
            r'\bshaam\b': 'evening',
            r'\braat\b': 'night'
        }
        
        for pattern, replacement in time_map.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
        return text

    @staticmethod
    def check_ambiguity(text: str) -> bool:
        """Flags ambiguous Hinglish constraints that require human clarification."""
        text_lower = text.lower()
        
        # Example 1: 'kal' can mean yesterday or tomorrow. If the verb indicates past, it's ambiguous.
        if "kal" in text_lower and any(past_verb in text_lower for past_verb in ["tha", "diya", "bola"]):
            return True
            
        # Example 2: Contradictory times (e.g., 'subah' and 'raat' in same context without 'ya')
        # Simplified ambiguity detection
        if "approx" in text_lower or "lagbhag" in text_lower or "aas paas" in text_lower:
            # If the user says "40 hazaar ke aas paas", it's ambiguous for a hard constraint
            if re.search(r'\d+', text_lower):
                return True
                
        return False

    def process(self, text: str) -> tuple[str, bool]:
        """Runs full normalization pipeline and returns (normalized_text, requires_clarification)."""
        is_ambiguous = self.check_ambiguity(text)
        
        text = self.normalize_monetary_expressions(text)
        text = self.normalize_time_expressions(text)
        
        return text, is_ambiguous

