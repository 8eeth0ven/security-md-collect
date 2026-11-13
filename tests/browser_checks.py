"""Run real browser checks on public snapshots, including a Pages-style URL prefix."""
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / '脚本'))
from build_dashboard import build_dashboard


class PagesHandler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)

    def translate_path(self,path):
        path = path.removeprefix('/security-md-collect')
        return super().translate_path(path or '/')

    def log_message(self,*args):
        pass

    def copyfile(self,source,outputfile):
        try:
            super().copyfile(source,outputfile)
        except ConnectionError:
            pass  # Link checks intentionally close large responses without reading bodies.


def main():
    build_dashboard(ROOT)
    server = ThreadingHTTPServer(('127.0.0.1',0),PagesHandler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    origin = 'http://127.0.0.1:%s' % server.server_port
    base = origin + '/security-md-collect/'
    payload = json.loads((ROOT / '索引/dashboard.json').read_text(encoding='utf-8'))
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width':1440,'height':1000})
            errors = []
            page.on('pageerror',lambda error: errors.append(str(error)))
            page.goto(base)
            expect(page.locator('#results .repo-title')).to_have_count(25)
            # Last page must reach all records, beyond the previous 2,000 result cap.
            page.locator('#last').click()
            expect(page.locator('#next')).to_be_disabled()
            assert 'page=' in page.url
            expect(page.locator('#page-info')).to_contain_text(f"{len(payload['repos']):,}")
            page.locator('#reset').click()
            page.locator('#fv').select_option('腾讯')
            page.locator('#langbtn').click()
            expect(page.locator('#fv')).to_have_value('腾讯')
            expect(page.locator('th[data-sort="v"] button')).to_have_text('Vendor')
            assert all(text == '腾讯' for text in page.locator('.vendor-name').all_text_contents())
            page.reload()
            expect(page.locator('#fv')).to_have_value('腾讯')
            expect(page.locator('#result-count')).to_contain_text('repositories found')
            page.locator('#reset').click()
            page.locator('#page-size').select_option('100')
            expect(page.locator('#results .repo-title')).to_have_count(100)
            page.locator('th[data-sort="s"] button').click()
            expect(page.locator('th[data-sort="s"]')).to_have_attribute('aria-sort','ascending')
            page.locator('#q').fill('there-is-no-such-security-policy-239481')
            expect(page.locator('.empty')).to_be_visible()
            expect(page.locator('#next')).to_be_disabled()
            page.locator('#q').fill('<img src=x onerror=alert(1)>')
            expect(page.locator('.empty')).to_be_visible()
            assert page.locator('#results img').count() == 0
            page.locator('#reset').click()
            page.locator('#vendors details').evaluate('(el) => el.open = true')
            expect(page.locator('.vendor-card')).to_have_count(len(payload['stats']['vendors']))
            # Validate every generated local policy link plus visible static/file links.
            actual_paths = {path.relative_to(ROOT).as_posix() for path in (ROOT / '厂商').glob('*/*/SECURITY.md')}
            for record in payload['repos']:
                if record['loc']:
                    assert unquote(record['loc']) in actual_paths,record['loc']
            local_links = page.locator('a[href]').evaluate_all('(els) => els.map(el => el.href).filter(h => h.startsWith(location.origin) && !h.includes("#"))')
            for link in set(local_links):
                assert link.startswith(base),f'Escaped Pages prefix: {link}'
                with urlopen(link,timeout=10) as response:
                    assert response.status == 200,link
            # Invalid localStorage values and storage denial must not break startup.
            page.evaluate("localStorage.setItem('secmd_lang','invalid')")
            page.goto(base)
            expect(page.locator('#results .repo-title')).to_have_count(25)
            blocked = browser.new_page()
            blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage blocked')}})")
            blocked.goto(base)
            expect(blocked.locator('#results .repo-title')).to_have_count(25)
            blocked.locator('#theme-select').select_option('dark')
            expect(blocked.locator('html')).to_have_attribute('data-theme','dark')
            blocked.emulate_media(color_scheme='light')
            expect(blocked.locator('html')).to_have_attribute('data-theme','dark')
            blocked.locator('#theme-select').select_option('light')
            expect(blocked.locator('html')).to_have_attribute('data-theme','light')
            blocked.close()
            # Appearance is applied in head, before body parsing, with persistence and OS changes.
            themed_context = browser.new_context(color_scheme='dark')
            themed_context.add_init_script('''
                window.themeBeforeBody = null;
                new MutationObserver(records => {
                    if (window.themeBeforeBody === null && records.some(r => r.attributeName === 'data-theme'))
                        window.themeBeforeBody = !document.body;
                }).observe(document, {subtree:true, attributes:true, attributeFilter:['data-theme']});
            ''')
            themed = themed_context.new_page()
            themed.goto(base)
            expect(themed.locator('#results .repo-title')).to_have_count(25)
            expect(themed.locator('html')).to_have_attribute('data-theme','light')
            assert themed.evaluate('window.themeBeforeBody') is True
            assert themed.evaluate('getComputedStyle(document.body).backgroundColor') == 'rgb(255, 255, 255)'
            themed.locator('#theme-select').select_option('system')
            expect(themed.locator('html')).to_have_attribute('data-theme','dark')
            themed.locator('#fv').select_option('腾讯')
            themed.locator('#theme-select').select_option('light')
            expect(themed.locator('#fv')).to_have_value('腾讯')
            themed.reload()
            expect(themed.locator('html')).to_have_attribute('data-theme','light')
            expect(themed.locator('#theme-select')).to_have_value('light')
            assert themed.evaluate('window.themeBeforeBody') is True
            themed.emulate_media(color_scheme='dark')
            expect(themed.locator('html')).to_have_attribute('data-theme','light')
            themed.locator('#langbtn').click()
            expect(themed.locator('#theme-select option[value="light"]')).to_have_text('Light')
            expect(themed.locator('#theme-select')).to_have_value('light')
            other = themed_context.new_page()
            other.goto(base)
            expect(other.locator('html')).to_have_attribute('data-theme','light')
            themed.locator('#theme-select').select_option('dark')
            expect(other.locator('html')).to_have_attribute('data-theme','dark')
            themed.locator('#theme-select').select_option('system')
            expect(themed.locator('html')).to_have_attribute('data-theme','dark')
            themed.emulate_media(color_scheme='light')
            expect(themed.locator('html')).to_have_attribute('data-theme','light')
            themed.evaluate("localStorage.setItem('secmd_theme','invalid')")
            themed.reload()
            expect(themed.locator('#theme-select')).to_have_value('light')
            expect(themed.locator('html')).to_have_attribute('data-theme','light')
            themed_context.close()
            # Offline/error state is useful and recovers on retry.
            page.route('**/dashboard.json',lambda route: route.abort())
            page.reload()
            expect(page.locator('#error')).to_be_visible()
            page.unroute('**/dashboard.json')
            page.locator('#retry').click()
            expect(page.locator('#error')).to_be_hidden()
            expect(page.locator('#results .repo-title')).to_have_count(25)
            for theme in ('light','dark'):
                for language in ('zh','en'):
                    for width in (320,390,768,1024,1440):
                        page.set_viewport_size({'width':width,'height':1000})
                        page.goto(base + '?lang=' + language)
                        expect(page.locator('#results .repo-title')).to_have_count(25)
                        page.locator('#theme-select').select_option(theme)
                        expect(page.locator('html')).to_have_attribute('data-theme',theme)
                        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),(width,language,theme,'overflow')
            # Treat untrusted descriptions as text, never HTML.
            injected = json.loads(json.dumps(payload))
            injected['repos'][0]['d'] = '<img src=x onerror=alert(1)>'
            page.route('**/dashboard.json',lambda route: route.fulfill(json=injected))
            page.goto(base+'?q='+payload['repos'][0]['f'])
            expect(page.locator('.repo-description').first).to_contain_text('<img src=x onerror=alert(1)>')
            assert page.locator('#results img').count() == 0
            assert not errors,errors
            browser.close()
        print('PASS: collection checks; theme before first paint, persistence, OS changes, cross-tab sync, blocked storage; 20 viewport/language/theme combinations.')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    main()
