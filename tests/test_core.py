"""Offline regression checks for generation, configuration, and public serving."""
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '脚本'))
from build_dashboard import build_dashboard, safe_name
import collect
import serve
from sync_github import sync_public_data


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.stats = {'generated_at':'2026-11-13 10:00:00','mode':'html',
                      'totals':{'vendors':1,'orgs':1,'orgs_swept':1,'sec_repos':2},
                      'vendors':[{'vendor':'示例/公司','src':'Example','orgs':['example'],'sec_repos':2}]}
        self.records = [
            {'vendor':'示例/公司','org':'example','full_name':'example/a','sec_path':'.github/SECURITY.md','stars':5},
            {'vendor':'示例/公司','org':'example','full_name':'example/b','sec_path':'docs/SECURITY.md','description':'</script><img src=x onerror=alert(1)>'},
        ]
        folder = self.base / '厂商/示例_公司'
        (folder / 'example__a').mkdir(parents=True)
        (folder / 'example__a/SECURITY.md').write_text('A policy',encoding='utf-8')
        (folder / 'repos.json').write_text(json.dumps(self.records),encoding='utf-8')
        (self.base / '索引').mkdir()
        (self.base / '索引/统计.json').write_text(json.dumps(self.stats),encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_public_snapshots_rebuild_without_state_or_network(self):
        self.assertEqual(build_dashboard(self.base),2)
        payload = json.loads((self.base / '索引/dashboard.json').read_text(encoding='utf-8'))
        self.assertEqual(payload['repos'][0]['loc'],quote('厂商/示例_公司/example__a/SECURITY.md'))
        self.assertIsNone(payload['repos'][1]['loc'])
        self.assertEqual(payload['repos'][1]['path'],'docs/SECURITY.md')
        self.assertIn('</script>',payload['repos'][1]['d'])
        self.assertTrue((self.base / 'web/dashboard.js').is_file())
        self.assertNotIn('</script><img', (self.base / 'index.html').read_text(encoding='utf-8'))
        self.assertIn('../index.html',(self.base / '索引/index.html').read_text(encoding='utf-8'))

    def test_collector_and_standalone_generation_agree(self):
        with patch.object(collect,'BASE',self.base):
            collect.write_index_html(self.stats,{'repos_data':{r['full_name']:r for r in self.records}})
        first = (self.base / '索引/dashboard.json').read_bytes()
        build_dashboard(self.base)
        self.assertEqual(first,(self.base / '索引/dashboard.json').read_bytes())

    def test_custom_vendor_mapping_is_actually_loaded(self):
        assets = self.base / '资产'
        assets.mkdir()
        (assets / '厂商映射-自加.json').write_text(json.dumps([{'vendor':'Custom','src':'None','orgs':['custom']}]),encoding='utf-8')
        with patch.object(collect,'ASSETS',assets), patch.object(collect,'MAPPING_FILES',[]):
            vendors, orgs = collect.merge_vendors()
        self.assertEqual(orgs,{'custom':'Custom'})
        self.assertEqual(vendors[0]['vendor'],'Custom')

    def test_default_https_verifies_certificates(self):
        self.assertTrue(collect._session().verify)
        self.assertEqual(safe_name('示例/公司'),'示例_公司')

    def test_snapshot_sync_preserves_code_and_excludes_runtime_files(self):
        with tempfile.TemporaryDirectory() as destination:
            destination = Path(destination)
            (self.base / 'index.html').write_text('old UI',encoding='utf-8')
            (self.base / '索引/state.json').write_text('private',encoding='utf-8')
            (self.base / '资产').mkdir()
            (self.base / '资产/.gh_token').write_text('private',encoding='utf-8')
            (destination / 'index.html').write_text('new UI',encoding='utf-8')
            self.assertGreater(sync_public_data(self.base,destination),0)
            self.assertEqual((destination / 'index.html').read_text(encoding='utf-8'),'new UI')
            self.assertFalse((destination / '索引/state.json').exists())
            self.assertFalse((destination / '资产/.gh_token').exists())
            self.assertTrue((destination / '厂商/示例_公司/repos.json').is_file())
            self.assertEqual(sync_public_data(self.base,destination),0)


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        for file,content in {'index.html':'Home','索引/统计.json':'{"ok":true}',
                             '厂商/示例/example__a/SECURITY.md':'Policy',
                             '资产/.gh_token':'test-secret','索引/state.json':'private',
                             '.git/config':'private','脚本/config.json':'private'}.items():
            path = base / file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        self.patcher = patch.object(serve,'BASE',base)
        self.patcher.start()
        class QuietHandler(serve.Handler):
            def log_message(self,*args): pass
        self.server = ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:%s' % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.patcher.stop()
        self.temp.cleanup()

    def request(self,path,method='GET'):
        return urlopen(Request(self.url+quote(path,safe='/%'),method=method),timeout=5)

    def test_startup_home_status_and_unicode_policy(self):
        with self.request('/') as response:
            self.assertEqual(response.read(),b'Home')
            self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
        with self.request('/status') as response:
            self.assertEqual(json.load(response),{'ok':True})
        with self.request('/厂商/示例/example__a/SECURITY.md') as response:
            self.assertEqual(response.read(),b'Policy')

    def test_private_files_and_directory_listings_are_blocked_for_get_and_head(self):
        for method in ('GET','HEAD'):
            for path in ('/资产/.gh_token','/.git/config','/索引/state.json','/脚本/config.json','/厂商/','/web/../脚本/config.json','/web/%2e%2e/脚本/config.json'):
                with self.subTest(method=method,path=path), self.assertRaises(HTTPError) as error:
                    self.request(path,method)
                self.assertEqual(error.exception.code,404)


if __name__ == '__main__':
    unittest.main()
