"""
Unit tests for Devanagari Hindi Token Recognition in FRIDAY
"""

import unittest

class TestHindiTokenMatching(TestCase := unittest.TestCase):
    def setUp(self):
        self.folder_tokens = ["क्रिएट फोल्डर", "नया फोल्डर", "फोल्डर बनाओ"]
        self.file_tokens = ["क्रिएट फाइल", "नई फाइल", "फाइल बनाओ"]

    def test_folder_intent_detection(self):
        phrase = "डेस्कटॉप पर नया फोल्डर बनाओ"
        matched = any(token in phrase for token in self.folder_tokens)
        self.assertTrue(matched)

    def test_file_intent_detection(self):
        phrase = "क्रिएट फाइल नोट्स डॉट टीएक्सटी"
        matched = any(token in phrase for token in self.file_tokens)
        self.assertTrue(matched)

if __name__ == '__main__':
    unittest.main()
