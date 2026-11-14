import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/physics-homework/scripts'))
from homework import allowed,safe,normalize

class CourseRules(unittest.TestCase):
    def test_as_a2(self):
        self.assertEqual(allowed('9702','AS'),{'1','2'})
        self.assertEqual(allowed('9702','A2'),{'4'})
        self.assertNotIn('1',allowed('9702','A2'))
    def test_core_extended(self):
        self.assertEqual(allowed('0625','Core'),{'1','3'})
        self.assertEqual(allowed('0625','Extended'),{'2','4'})
    def test_practical_differs(self):
        self.assertEqual(allowed('9702','P3'),{'3'})
        self.assertEqual(allowed('0625','P6'),{'6'})
        with self.assertRaises(ValueError):allowed('0625','A2')
        with self.assertRaises(ValueError):allowed('9702','Extended')
    def test_source_traversal(self):
        with self.assertRaises(ValueError):safe(ROOT,'../secret')
        self.assertEqual(safe(ROOT,'README.md'),ROOT/'README.md')
    def test_course_spoof(self):
        with self.assertRaises(ValueError):normalize('0625',{'course':'9702'},ROOT)
    def test_paper_spoof(self):
        with self.assertRaises(ValueError):normalize('0625',{'course':'0625','paper':'2','kind':'structured'},ROOT)

if __name__=='__main__':unittest.main()
