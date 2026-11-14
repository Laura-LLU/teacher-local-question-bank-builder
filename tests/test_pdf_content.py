import unittest,sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/physics-homework/scripts'))
from pdf_engine import _trim_outer_whitespace
from homework import topic_matches

class ContentPreservation(unittest.TestCase):
    def test_separate_blocks_are_retained(self):
        im=Image.new('RGB',(600,600),'white');draw=ImageDraw.Draw(im)
        draw.rectangle((20,20,80,40),fill='black')
        draw.rectangle((400,480,500,530),fill='black')
        result=_trim_outer_whitespace(im)
        self.assertEqual(sum(im.convert('L').histogram()[:100]),sum(result.convert('L').histogram()[:100]))
        self.assertGreater(result.height,480)
    def test_numeric_topics_are_not_prefixes(self):
        self.assertTrue(topic_matches('Topic 1','Topic 1 · Physical quantities and units'))
        self.assertFalse(topic_matches('Topic 1','Topic 12 · Motion in a circle'))
        self.assertFalse(topic_matches('1.1','1.10 Something else'))
        self.assertTrue(topic_matches('1.1','1.1 Physical quantities and measurement techniques'))

if __name__=='__main__':unittest.main()
