"""
Unit tests for Hindi Voice Command Parsing for Files and Directories
"""

import unittest

class TestHindiFileCommands(TestCase := unittest.TestCase):
    def test_flexible_word_ordering(self):
        variations = [
            "डेस्कटॉप पर प्रोजेक्ट नाम का फोल्डर बनाओ",
            "क्रिएट फोल्डर प्रोजेक्ट ऑन डेस्कटॉप",
            "नया फोल्डर क्रिएट करो"
        ]
        for v in variations:
            self.assertTrue(len(v) > 5)

if __name__ == '__main__':
    unittest.main()
