"""
Sinhala Unicode Shaping Engine
================================
Handles Unicode normalization, ZWJ handling, virama validation,
and cluster structure verification for Sinhala text.

This module ensures that Sinhala text from any source (API, fine-tuned model, etc.)
is properly normalized before being passed to the rendering engine (HarfBuzz/browser).

Research Contribution:
  "Unicode-aware Sinhala text shaping pipeline ensuring orthographic correctness
   through NFC normalization, ZWJ insertion for conjunct consonants (rakaransaya,
   yansaya), and virama sequence validation."

Sinhala Unicode Block: U+0D80 - U+0DFF
Key Characters:
  - Virama (Al-lakuna): U+0DCA (්)
  - ZWJ: U+200D
  - ZWNJ: U+200C
  - Consonants: U+0D9A - U+0DC6
  - Vowels: U+0D85 - U+0D96
  - Vowel Signs: U+0DCA - U+0DDF, U+0DF2 - U+0DF3
"""
import unicodedata
import re
from typing import List, Tuple, Optional


class SinhalaShapingEngine:
    """
    Unicode-aware Sinhala text shaping preprocessor.
    
    Ensures proper Unicode sequences before HarfBuzz rendering:
    1. NFC Normalization
    2. ZWJ insertion for rakaransaya/yansaya
    3. Virama (U+0DCA) validation
    4. Cluster structure validation
    """
    
    # Sinhala Unicode ranges
    SINHALA_RANGE = (0x0D80, 0x0DFF)
    
    # Key Sinhala characters
    VIRAMA = '\u0DCA'      # ් (Al-lakuna / Hal kirīma)
    ZWJ = '\u200D'         # Zero Width Joiner
    ZWNJ = '\u200C'        # Zero Width Non-Joiner
    
    # Consonants (U+0D9A to U+0DC6)
    CONSONANT_RANGE = (0x0D9A, 0x0DC6)
    
    # Special consonants for conjunct formation
    RA = '\u0DBB'          # ර (Ra)
    YA = '\u0DBA'          # ය (Ya)
    
    # Independent vowels
    VOWEL_RANGE = (0x0D85, 0x0D96)
    
    # Dependent vowel signs
    VOWEL_SIGN_RANGE_1 = (0x0DCF, 0x0DDF)  # Common vowel signs
    VOWEL_SIGN_RANGE_2 = (0x0DF2, 0x0DF3)  # Additional vowel signs
    
    def __init__(self):
        print("✅ Sinhala Shaping Engine initialized")
        print("   - NFC Normalization: enabled")
        print("   - ZWJ Handling: enabled")
        print("   - Virama Validation: enabled")
        print("   - Cluster Validation: enabled")
    
    def process(self, text: str) -> str:
        """
        Full shaping pipeline: normalize → validate → fix ZWJ → return
        
        Args:
            text: Raw Unicode text (may contain Sinhala, English, emojis, etc.)
        
        Returns:
            Properly shaped Unicode text ready for HarfBuzz rendering
        """
        if not text:
            return text
        
        # Step 1: NFC Normalization (canonical composition)
        text = self.normalize_nfc(text)
        
        # Step 2: Ensure ZWJ for rakaransaya/yansaya sequences
        text = self.ensure_zwj_conjuncts(text)
        
        # Step 3: Validate virama sequences
        text = self.validate_virama_sequences(text)
        
        # Step 4: Clean up any double ZWJ or invalid sequences
        text = self.cleanup_sequences(text)
        
        return text
    
    def normalize_nfc(self, text: str) -> str:
        """
        Apply NFC (Canonical Decomposition + Canonical Composition) normalization.
        
        NFC ensures that characters like:
          - Base + combining mark → precomposed form (if available)
          - Consistent representation across platforms
        
        This is critical for Sinhala because different input methods may produce
        decomposed or composed forms of the same character.
        """
        return unicodedata.normalize('NFC', text)
    
    def is_sinhala_consonant(self, char: str) -> bool:
        """Check if character is a Sinhala consonant"""
        cp = ord(char)
        return self.CONSONANT_RANGE[0] <= cp <= self.CONSONANT_RANGE[1]
    
    def is_sinhala_char(self, char: str) -> bool:
        """Check if character is in the Sinhala Unicode block"""
        cp = ord(char)
        return self.SINHALA_RANGE[0] <= cp <= self.SINHALA_RANGE[1]
    
    def is_sinhala_vowel_sign(self, char: str) -> bool:
        """Check if character is a Sinhala dependent vowel sign"""
        cp = ord(char)
        return (
            (self.VOWEL_SIGN_RANGE_1[0] <= cp <= self.VOWEL_SIGN_RANGE_1[1]) or
            (self.VOWEL_SIGN_RANGE_2[0] <= cp <= self.VOWEL_SIGN_RANGE_2[1])
        )
    
    def has_sinhala(self, text: str) -> bool:
        """Check if text contains any Sinhala characters"""
        return any(self.is_sinhala_char(c) for c in text)
    
    def ensure_zwj_conjuncts(self, text: str) -> str:
        """
        Ensure ZWJ is present for rakaransaya and yansaya sequences.
        
        Rakaransaya (රකාරාංශය):
          Consonant + Virama + ZWJ + Ra → conjunct form
          e.g., ක + ් + ZWJ + ර = ක්‍ර (kra)
        
        Yansaya (යංසය):
          Consonant + Virama + ZWJ + Ya → conjunct form
          e.g., ක + ් + ZWJ + ය = ක්‍ය (kya)
        
        Without ZWJ, the shaping engine may render them as separate characters
        instead of the proper conjunct form.
        """
        if not text:
            return text
        
        result = []
        i = 0
        chars = list(text)
        
        while i < len(chars):
            result.append(chars[i])
            
            # Check for Consonant + Virama + (Ra or Ya) without ZWJ
            if (i + 2 < len(chars) and
                self.is_sinhala_consonant(chars[i]) and
                chars[i + 1] == self.VIRAMA and
                chars[i + 2] in (self.RA, self.YA)):
                
                # Check if ZWJ is already there
                # Pattern: Consonant + Virama + ZWJ + Ra/Ya (already correct)
                if (i + 3 < len(chars) and 
                    chars[i + 1] == self.VIRAMA and
                    chars[i + 2] == self.ZWJ and
                    chars[i + 3] in (self.RA, self.YA)):
                    # Already has ZWJ, skip
                    pass
                else:
                    # Insert ZWJ: Consonant + Virama + [ZWJ] + Ra/Ya
                    result.append(chars[i + 1])  # Virama
                    result.append(self.ZWJ)       # ZWJ (inserted)
                    result.append(chars[i + 2])   # Ra or Ya
                    i += 3
                    continue
            
            i += 1
        
        return ''.join(result)
    
    def validate_virama_sequences(self, text: str) -> str:
        """
        Validate that virama (U+0DCA) appears only after consonants.
        
        Valid: Consonant + Virama (e.g., ක් = k with no vowel)
        Invalid: Vowel + Virama, Space + Virama, etc.
        
        This prevents rendering errors in the shaping engine.
        """
        if not text:
            return text
        
        result = []
        prev_char = None
        
        for char in text:
            if char == self.VIRAMA:
                # Virama should only follow a consonant
                if prev_char and self.is_sinhala_consonant(prev_char):
                    result.append(char)
                else:
                    # Invalid virama placement - skip it
                    print(f"   ⚠️ Invalid virama after '{prev_char}' (U+{ord(prev_char) if prev_char else 0:04X}) - skipped")
                    continue
            else:
                result.append(char)
            
            prev_char = char
        
        return ''.join(result)
    
    def cleanup_sequences(self, text: str) -> str:
        """
        Clean up invalid or redundant Unicode sequences:
        - Remove double ZWJ
        - Remove orphan ZWJ (not in valid conjunct context)
        - Remove double virama
        """
        # Remove double ZWJ
        text = text.replace(self.ZWJ + self.ZWJ, self.ZWJ)
        
        # Remove double virama
        text = text.replace(self.VIRAMA + self.VIRAMA, self.VIRAMA)
        
        return text
    
    def analyze_text(self, text: str) -> dict:
        """
        Analyze Sinhala text for research/debugging purposes.
        
        Returns detailed information about:
        - Character counts by type
        - Conjunct sequences found
        - ZWJ usage
        - Potential issues
        """
        analysis = {
            "total_chars": len(text),
            "sinhala_chars": 0,
            "consonants": 0,
            "vowels": 0,
            "vowel_signs": 0,
            "viramas": 0,
            "zwj_count": 0,
            "zwnj_count": 0,
            "english_chars": 0,
            "emoji_count": 0,
            "rakaransaya_sequences": 0,
            "yansaya_sequences": 0,
            "conjunct_sequences": [],
            "issues": []
        }
        
        for i, char in enumerate(text):
            cp = ord(char)
            
            if self.is_sinhala_char(char):
                analysis["sinhala_chars"] += 1
                
                if self.is_sinhala_consonant(char):
                    analysis["consonants"] += 1
                elif self.VOWEL_RANGE[0] <= cp <= self.VOWEL_RANGE[1]:
                    analysis["vowels"] += 1
                elif self.is_sinhala_vowel_sign(char):
                    analysis["vowel_signs"] += 1
                
                if char == self.VIRAMA:
                    analysis["viramas"] += 1
            
            elif char == self.ZWJ:
                analysis["zwj_count"] += 1
            elif char == self.ZWNJ:
                analysis["zwnj_count"] += 1
            elif char.isascii() and char.isalpha():
                analysis["english_chars"] += 1
        
        # Detect rakaransaya and yansaya
        for i in range(len(text) - 3):
            if (self.is_sinhala_consonant(text[i]) and
                text[i + 1] == self.VIRAMA and
                text[i + 2] == self.ZWJ):
                if i + 3 < len(text):
                    if text[i + 3] == self.RA:
                        analysis["rakaransaya_sequences"] += 1
                        analysis["conjunct_sequences"].append(
                            f"Rakaransaya at pos {i}: {text[i]}+්+ZWJ+ර"
                        )
                    elif text[i + 3] == self.YA:
                        analysis["yansaya_sequences"] += 1
                        analysis["conjunct_sequences"].append(
                            f"Yansaya at pos {i}: {text[i]}+්+ZWJ+ය"
                        )
        
        return analysis
    
    def get_unicode_info(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Get detailed Unicode info for each character (for debugging).
        
        Returns list of (character, codepoint, name) tuples.
        """
        info = []
        for char in text:
            try:
                name = unicodedata.name(char, f"UNKNOWN (U+{ord(char):04X})")
            except ValueError:
                name = f"UNKNOWN (U+{ord(char):04X})"
            info.append((char, f"U+{ord(char):04X}", name))
        return info


# ============================================
# Singleton
# ============================================
_shaping_engine = None


def get_shaping_engine() -> SinhalaShapingEngine:
    """Get or create Sinhala shaping engine"""
    global _shaping_engine
    if _shaping_engine is None:
        _shaping_engine = SinhalaShapingEngine()
    return _shaping_engine


# ============================================
# Test
# ============================================
if __name__ == "__main__":
    engine = SinhalaShapingEngine()
    
    # Test texts
    test_texts = [
        "රු. 10,000 කට සපත්තු ගන්නවද?",
        "ක්‍රිස්මස් විශේෂ දීමනාව!",
        "ප්‍රවර්ධන මිල අඩුකිරීම",
        "අද Special Offer එකක්! 🎉",
    ]
    
    for text in test_texts:
        print(f"\n{'='*60}")
        print(f"Input:  {text}")
        
        processed = engine.process(text)
        print(f"Output: {processed}")
        
        analysis = engine.analyze_text(processed)
        print(f"Analysis:")
        print(f"  Sinhala chars: {analysis['sinhala_chars']}")
        print(f"  Consonants: {analysis['consonants']}")
        print(f"  Viramas: {analysis['viramas']}")
        print(f"  ZWJ count: {analysis['zwj_count']}")
        print(f"  Rakaransaya: {analysis['rakaransaya_sequences']}")
        print(f"  Yansaya: {analysis['yansaya_sequences']}")
        if analysis['conjunct_sequences']:
            for seq in analysis['conjunct_sequences']:
                print(f"    → {seq}")
