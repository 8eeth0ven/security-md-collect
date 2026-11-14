"""Official scope reconciliation and domestic import boundaries, using synthetic data."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'脚本'))
from build_apk_board import normalize
from import_domestic_apk import import_rows
from verify_apk_history import classify, run


class HistoryReviewTests(unittest.TestCase):
    def evidence(self, scopes):
        return {'complete':True,'scopes':scopes,'program':{}}

    def test_named_exclusion_beats_guessed_package_on_in_scope_version(self):
        row = {'target':'Non-current Android version','package':'com.example.app'}
        scopes = [{'value':'com.example.app','android':True,'in_scope':True},
                  {'value':'Non-current Android version','android':True,'in_scope':False}]
        self.assertEqual(classify(row,self.evidence(scopes))['status'],'out_of_scope')

    def test_website_does_not_inherit_an_unrelated_curated_android_package(self):
        row = {'target':'Digits Web','uri':'https://example.test/digits','package':'com.example.other','package_source':'人工兜底'}
        scopes = [{'value':'https://example.test/digits','name':'Digits Web','type':'website','android':False,'in_scope':True},
                  {'value':'com.example.other','android':True,'in_scope':True}]
        self.assertEqual(classify(row,self.evidence(scopes))['status'],'not_android')

    def test_current_asset_takes_precedence_over_its_archived_copy(self):
        row = {'target':'com.example.app'}
        scopes = [{'value':row['target'],'android':True,'archived':True,'in_scope':True},
                  {'value':row['target'],'android':True,'archived':False,'in_scope':True}]
        self.assertEqual(classify(row,self.evidence(scopes))['status'],'in_scope')

    def test_unavailable_or_absent_is_not_an_explicit_exclusion(self):
        row = {'target':'com.example.app'}
        self.assertEqual(classify(row,{'complete':False})['status'],'unavailable')
        self.assertEqual(classify(row,self.evidence([]))['status'],'not_listed')

    def test_package_case_is_significant(self):
        self.assertEqual(classify({'target':'com.Example.app'},self.evidence([
            {'value':'com.example.app','android':True,'in_scope':True}]))['status'],'not_listed')

    def test_review_and_paused_state_override_old_cash_snapshot(self):
        row = {'handle':'example','offers_bounties':True,'eligible_for_bounty':True,'eligible_for_submission':True,
               'scope_observation':'reviewed','scope_review_status':'in_scope'}
        self.assertEqual(normalize('h1',{**row,'program_submission_state':'paused'})['bounty'],'inactive')
        self.assertEqual(normalize('h1',{**row,'scope_review_status':'out_of_scope'})['bounty'],'excluded')
        self.assertEqual(normalize('h1',{**row,'scope_review_status':'android_unresolved'})['bounty'],'unknown')

    def test_domestic_unresolved_and_unsupported_packages_are_not_imported(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);(base/'赏金APK').mkdir()
            evidence=base/'evidence.json'
            source={'vendor':'Example','src_name':'ExampleSRC','product':'App','scope_url':'https://src.example.test/rules',
                    'scope_evidence':'Named Android scope','download_page':'https://example.test/android',
                    'reward_status':'unknown','observed_at':'2026-11-14','scope_status':'confirmed'}
            evidence.write_text(json.dumps([source,{**source,'product':'Unresolved','scope_status':'product_rename'}]),encoding='utf-8')
            result=import_rows(base,evidence)
            self.assertEqual((result['confirmed'],result['pending']),(1,1))
            rows=json.loads((base/'赏金APK/src_android.json').read_text(encoding='utf-8'))
            self.assertEqual(normalize('src',rows[0])['bounty'],'unknown')
            evidence.write_text(json.dumps([{**source,'package':'com.example.app'}]),encoding='utf-8')
            with self.assertRaises(ValueError):
                import_rows(base,evidence)
            self.assertEqual(len(json.loads((base/'赏金APK/src_android.json').read_text(encoding='utf-8'))),1)

    def test_review_can_be_repeated_without_erasing_original_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);out=base/'赏金APK';out.mkdir();cache=base/'cache';cache.mkdir()
            record={'handle':'example','target':'com.example.app','scope_observation':'historical'}
            for filename in ('apk_final.json','ywh_android.json','intigriti_android.json'):
                (out/filename).write_text('[]',encoding='utf-8')
            (out/'h1_android.json').write_text(json.dumps([record]),encoding='utf-8')
            evidence={'complete':True,'observed_at':'2026-11-14','url':'https://hackerone.com/example',
                      'program':{'offers_bounties':True,'submission_state':'open'},
                      'scopes':[{'value':'com.example.app','android':True,'in_scope':True,'eligible_for_bounty':True}]}
            (cache/'h1-example.json').write_text(json.dumps(evidence),encoding='utf-8')
            first=run(base,cache)
            second=run(base,cache)
            self.assertEqual(first['baseline_targets'],second['baseline_targets'])
            self.assertEqual(second['status_counts'],{'in_scope':1})


if __name__=='__main__':
    unittest.main()
