import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / '脚本'))
from build_apk_board import build_apk_board, normalize, row_html


class APKTests(unittest.TestCase):
    def test_bounty_is_asset_eligible_and_not_archived(self):
        source = {'handle':'example','offers_bounties':True,'eligible_for_bounty':True,'eligible_for_submission':True}
        self.assertEqual(normalize('h1',source)['bounty'],'cash')
        self.assertEqual(normalize('h1',{**source,'eligible_for_bounty':False})['bounty'],'vdp')
        self.assertEqual(normalize('h1',{**source,'archived':True})['bounty'],'inactive')
        self.assertEqual(normalize('h1',{'handle':'unknown'})['bounty'],'unknown')
        self.assertEqual(normalize('bugcrowd',{'handle':'points','bounty_type':'points'})['bounty'],'points')

    def test_candidates_are_unverified_and_invalid_packages_do_not_create_links(self):
        source = {'handle':'example','package':'com.example.app','package_source':'人工兜底', 'apk_direct':'javascript:alert(1)'}
        row = normalize('bugcrowd',source)
        self.assertTrue(row['needs_review'])
        self.assertFalse(row['download_verified'])
        self.assertEqual(row['apk_direct'],'')
        self.assertIn('/XAPK/com.example.app?',row['xapk'])
        invalid = normalize('bugcrowd',{**source,'package':'com.example.*'})
        self.assertEqual(invalid['package'],'')
        self.assertEqual(invalid['xapk'],'')
        self.assertEqual(invalid['package_hint'],'com.example.*')

    def test_source_links_and_static_html_escape_untrusted_text(self):
        source = {'handle':'example','program':'<img src=x onerror=alert(1)>','bounty_type':'cash','package':'com.example.app','uri':'https://play.google.com/store/apps/details?id=com.example.app'}
        row = normalize('bugcrowd',source)
        self.assertEqual(row['package_source'],'play')
        rendered = row_html(row)
        self.assertIn('&lt;img',rendered)
        self.assertNotIn('<img',rendered)

    def test_builder_has_readable_first_page_and_deterministic_public_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            out = base/'赏金APK'
            out.mkdir()
            records = [{'handle':'paid','program':'Paid App','bounty_type':'cash','package':'com.example.app'},
                       {'handle':'other','program':'No reward app','bounty_type':'vdp_or_unknown'},
                       {'handle':'formula','program':'=1+1','bounty_type':'cash'}]
            (out/'apk_final.json').write_text(json.dumps(records),encoding='utf-8')
            (out/'snapshot.json').write_text('{"generated_at":"2026-11-13 12:29"}',encoding='utf-8')
            stats = build_apk_board(base)
            self.assertEqual(stats['targets'],3)
            self.assertEqual(stats['cash'],2)
            self.assertEqual(stats['packages'],1)
            page = (out/'赏金APK看板.html').read_text(encoding='utf-8')
            self.assertIn('Paid App',page)
            self.assertNotIn('No reward app',page)
            self.assertNotIn('@@',page)
            csv_rows = list(csv.DictReader(io.StringIO((out/'dashboard.csv').read_text(encoding='utf-8-sig'))))
            self.assertIn("'=1+1",[r['program'] for r in csv_rows])
            before = {path.name:path.read_bytes() for path in out.iterdir()}
            build_apk_board(base)
            self.assertEqual(before,{path.name:path.read_bytes() for path in out.iterdir()})


if __name__ == '__main__': unittest.main()
