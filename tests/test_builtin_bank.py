import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/physics-homework/scripts'))
import builtin_bank as bank

class BuiltinBankTests(unittest.TestCase):
    def test_empty_workspace_initializes_both_courses(self):
        with tempfile.TemporaryDirectory() as folder:
            work=Path(folder).resolve()
            for course,count in [('9702',4330),('0625',2256)]:
                doc=json.loads(bank.ensure_index(work,course).read_text())
                rows=doc['questions']
                self.assertEqual(len(rows),count)
                self.assertEqual(len({r['id'] for r in rows}),count)
                for row in rows:
                    self.assertEqual(row['course'],course)
                    for side in ['question','answer']:
                        bank.get_origin_url(bank.PROVIDER['origins'][0],row[side+'_asset'])
                        self.assertTrue(Path(row[side+'_image']).is_relative_to(work))
                if course=='0625':self.assertEqual({r['paper'] for r in rows},{'2','4'})
    def test_preserves_user_bound_bank(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder).resolve()/'9702/bank.json';path.parent.mkdir()
            path.write_text('user supplied catalog')
            self.assertEqual(bank.ensure_index(folder,'9702'),path)
            self.assertEqual(path.read_text(),'user supplied catalog')
    def test_cache_reuse_needs_no_network(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'cached.webp'
            Image.new('RGB',(20,20),'white').save(path)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()[:12]
            row={'id':'test','source_kind':'builtin','question_image':str(path),
                 'question_asset':'assets/questions/9702/test.webp?v='+digest}
            with patch('urllib.request.urlopen',side_effect=AssertionError('network should not run')):
                bank.fetch_one(row,'question')
            self.assertTrue(bank.verify_image(path,digest))
            path.write_bytes(b'corrupt')
            self.assertFalse(bank.verify_image(path,digest))
    def test_origin_and_path_validation(self):
        with self.assertRaises(ValueError):bank.get_origin_url('https://untrusted.example','asset')
        for path in ['../secret','https://other.example/file','assets/questions/9702/../../secret.webp?v=abcdef123456']:
            with self.assertRaises(ValueError):bank.get_origin_url(bank.PROVIDER['origins'][0],path)
    def test_packaged_metadata_has_no_question_body(self):
        for course in ['9702','0625']:
            rows=json.loads((bank.RESOURCES/('builtin-'+course+'.json')).read_text())['questions']
            for row in rows:
                self.assertFalse({'searchText','search_text','question_text','answer_text'} & row.keys())

if __name__=='__main__':unittest.main()
