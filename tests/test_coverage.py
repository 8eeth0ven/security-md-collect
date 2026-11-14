"""Scope provenance and refresh behavior; entirely synthetic public metadata."""
import sys
import time
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'脚本'))
import collect
from build_apk_board import normalize
from expand_policy_sources import github_seed
from update_apk_sources import android_target, convert, merge, package_from, update


class CoverageTests(unittest.TestCase):
    def test_scope_types_and_exclusions(self):
        self.assertTrue(android_target({'asset_type':'OTHER_APK','asset_identifier':'download.apk'}))
        self.assertTrue(android_target({'type':'mobile-application','target':'https://play.google.com/store/apps/details?id=com.example.app'}))
        self.assertFalse(android_target({'type':'url','endpoint':'all', 'description':'Excluded https://play.google.com/store/apps/details?id=com.example.app'}))
        self.assertFalse(android_target({'type':None,'endpoint':'https://[not an ip]'}))

    def test_package_is_not_an_arbitrary_substring(self):
        self.assertEqual(package_from('https://play.google.com/store/apps/details?id=com.example.app&hl=en'),'com.example.app')
        self.assertEqual(package_from('https://play.google.com/store/apps/dev?id=123'),'')
        self.assertEqual(package_from('App com.example.app maybe'), '')
        self.assertEqual(package_from('com.example.*'), '')

    def test_intigriti_target_bounty_and_annotated_app_link(self):
        program = {'handle':'example','company_handle':'example','name':'Example','max_bounty':{'value':500},'status':'open'}
        source = {'type':'android','endpoint':'Example app','description':'This is our app.\\nApp link: https://play.google.com/store/apps/details?id=com.example.app','impact':'Tier 1'}
        row = convert('intigriti',program,source)
        self.assertEqual(row['package'],'com.example.app')
        self.assertEqual(normalize('intigriti',row)['bounty'],'cash')
        self.assertEqual(normalize('intigriti',convert('intigriti',program,{**source,'impact':'No Bounty'}))['bounty'],'vdp')
        self.assertIsNone(convert('intigriti',program,{**source,'description':'Excluded app.\nApp link: https://play.google.com/store/apps/details?id=com.example.app'})['package'])

    def test_merge_keeps_history_and_is_idempotent(self):
        old = [{'handle':'x','target':'https://play.google.com/store/apps/details?id=com.example.app&hl=en','package':'com.example.app'},
               {'handle':'x','target':'old target','package':'com.example.old'}]
        fresh = [{'handle':'x','target':'https://play.google.com/store/apps/details?id=com.example.app','package':'com.example.app'}]
        rows, added = merge('h1',old,fresh,{'scope_observed_at':'now'})
        self.assertEqual(added,0)
        self.assertEqual(len(rows),2)
        self.assertEqual([r['scope_observation'] for r in rows],['observed','historical'])
        self.assertEqual(merge('h1',rows,fresh,{'scope_observed_at':'now'}),(rows,0))

    def test_cache_expiration_and_updated_policy(self):
        state = {'repos_checked':{'x/a':{'sec_path':None,'checked_at':'2020-01-01 00:00:00'}},'repos_data':{},'orgs':{}}
        self.assertTrue(collect.probe_due(state,'x/a'))
        with patch.object(collect,'probe_security',return_value=('SECURITY.md',None)), patch.object(collect,'save_state'):
            self.assertEqual(collect.probe_and_record(state,'x','X',{'x/a':{}},float('inf')),1)
        first = state['repos_data']['x/a']['first_seen']
        state['repos_checked']['x/a']['checked_at']='2020-01-01 00:00:00'
        with patch.object(collect,'probe_security',return_value=('error',None)), patch.object(collect,'save_state'):
            collect.probe_and_record(state,'x','X',{'x/a':{}},float('inf'))
        self.assertEqual(state['repos_data']['x/a']['first_seen'],first)
        with patch.object(collect,'probe_security',return_value=(None,None)), patch.object(collect,'save_state'):
            collect.probe_and_record(state,'x','X',{'x/a':{}},float('inf'))
        self.assertNotIn('x/a',state['repos_data'])

    def test_seed_does_not_confuse_domains_or_wildcards_with_repos(self):
        self.assertEqual(github_seed('https://github.com/example/repo/tree/main'),('example','repo'))
        self.assertEqual(github_seed('https://github.com/example/*'),('example',None))
        self.assertIsNone(github_seed('https://example.github.io/repo'))
        self.assertIsNone(github_seed('https://github.com/settings/foo'))

    def test_partial_or_capped_repository_listing_is_not_complete(self):
        with patch.object(collect, 'http_get', side_effect=[(200,b'page'),(503,b'error')]), patch.object(collect, 'parse_profile_items', return_value={'x/a':{}}), patch.object(collect.time, 'sleep'):
            self.assertIsNone(collect.list_profile('x'))

    def test_nonstandard_search_path_remains_probeable(self):
        def reply(url, *args, **kwargs):
            return (200, b'# Policy') if url.endswith('custom%20docs/SECURITY.md') else (404, b'')
        with patch.object(collect,'http_get',side_effect=reply):
            self.assertEqual(collect.probe_security('x/a',['custom docs/SECURITY.md']),('custom docs/SECURITY.md',b'# Policy'))

    def test_invalid_source_does_not_replace_existing_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            out = base/'赏金APK'
            source = base/'source'
            out.mkdir();source.mkdir()
            (source/'revision.json').write_text(json.dumps({'sha':'a'*40}),encoding='utf-8')
            for filename in ('apk_final.json','ywh_android.json','h1_android.json','intigriti_android.json'):
                (out/filename).write_text('[]',encoding='utf-8')
            for name in ('bugcrowd','yeswehack','hackerone'):
                (source/(name+'.json')).write_text('[{"targets":{"in_scope":[]}}]',encoding='utf-8')
            (source/'intigriti.json').write_text('{}',encoding='utf-8')
            before = {p.name:p.read_bytes() for p in out.iterdir()}
            with self.assertRaises(ValueError):
                update(base,source)
            self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
        with patch.dict(collect.CFG, {'page_cap_profile':1}), patch.object(collect, 'http_get', return_value=(200,b'page')), patch.object(collect, 'parse_profile_items', return_value={'x/a':{}}), patch.object(collect.time, 'sleep'):
            self.assertIsNone(collect.list_profile('x'))


if __name__ == '__main__':
    unittest.main()
