"""Check the APK board without contacting any bounty target or download service."""
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from browser_checks import PagesHandler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'脚本'))
from build_dashboard import build_dashboard


def main():
    build_dashboard(ROOT)
    payload=json.loads((ROOT/'赏金APK/dashboard.json').read_text(encoding='utf-8'))
    server=ThreadingHTTPServer(('127.0.0.1',0),PagesHandler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    root='http://127.0.0.1:%s/security-md-collect/'%server.server_port
    url=root+'赏金APK/赏金APK看板.html'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch()
            context=browser.new_context()
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(url)
            expect(page.locator('#apk-results tr')).to_have_count(25)
            expect(page.locator('#apk-count')).to_contain_text(str(payload['stats']['cash']))
            expect(page.locator('#apk-bounty')).to_have_value('cash')
            page.locator('#apk-bounty').select_option('all')
            for platform in payload['stats']['platforms']:
                page.locator('#apk-platform').select_option(platform['key'])
                expect(page.locator('#apk-count')).to_contain_text(str(platform['targets']))
                expect(page.locator('#apk-results tr')).to_have_count(min(25,platform['targets']))
            # No package ID still has an official program link, with no invented mirror.
            expect(page.locator('#apk-results .package')).to_have_text('包名待补充')
            assert page.locator('#apk-results .mirror').count()==0
            page.locator('#apk-platform').select_option('h1')
            page.locator('#apk-next').click()
            assert 'page=2' in page.url
            page.reload()
            expect(page.locator('#apk-platform')).to_have_value('h1')
            expect(page.locator('#apk-bounty')).to_have_value('all')
            expect(page.locator('#apk-page-number')).to_contain_text('2')
            page.locator('#apk-last').click()
            expect(page.locator('#apk-next')).to_be_disabled()
            page.locator('#langbtn').click()
            expect(page.locator('#apk-title')).to_have_text('Android app directory')
            expect(page.locator('#apk-platform')).to_have_value('h1')
            expect(page.locator('#apk-bounty')).to_have_value('all')
            page.locator('#apk-reset').click()
            page.locator('#apk-q').fill('no-such-apk-2399473')
            expect(page.locator('.empty')).to_be_visible()
            page.locator('#apk-reset').click()
            page.locator('#apk-access').select_option('missing')
            missing=sum(r['bounty']=='cash' and not(r['play'] or r['apk_direct'] or r['xapk']) for r in payload['rows'])
            expect(page.locator('#apk-count')).to_contain_text(str(missing))
            page.locator('#theme-select').select_option('dark')
            page.goto(root)
            expect(page.locator('html')).to_have_attribute('data-theme','dark')
            expect(page.locator('.feature-callout')).to_be_visible()
            page.locator('.feature-callout').click()
            expect(page.locator('html')).to_have_attribute('data-theme','dark')
            expect(page.locator('#apk-results tr')).to_have_count(25)
            for theme in ('light','dark'):
                for language in ('zh','en'):
                    for width in (320,390,768,1024,1440):
                        page.set_viewport_size({'width':width,'height':1000})
                        page.goto(url+'?lang='+language)
                        expect(page.locator('#apk-count')).not_to_contain_text('…')
                        page.locator('#theme-select').select_option(theme)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(theme,language,width)
            page.route('**/dashboard.json',lambda route:route.abort())
            page.reload()
            expect(page.locator('#apk-error')).to_be_visible()
            expect(page.locator('#apk-results tr')).to_have_count(25)
            page.unroute('**/dashboard.json')
            page.locator('#apk-retry').click()
            expect(page.locator('#apk-error')).to_be_hidden()
            injected=json.loads(json.dumps(payload))
            injected['rows'][0]['program']='apk-xss-case <img src=x onerror=alert(1)>'
            injected['rows'][0]['xapk']='javascript:alert(1)'
            page.route('**/dashboard.json',lambda route:route.fulfill(json=injected))
            page.goto(url+'?bounty=all&q=apk-xss-case')
            expect(page.locator('#apk-results')).to_contain_text('<img src=x onerror=alert(1)>')
            assert page.locator('#apk-results img').count()==0
            assert page.locator('#apk-results a[href^="javascript:"]').count()==0
            assert not errors,errors
            readonly=browser.new_context(java_script_enabled=False)
            static=readonly.new_page()
            static.goto(url)
            expect(static.locator('#apk-results tr')).to_have_count(25)
            assert static.locator('#apk-results a').count()>25
            readonly.close()
            browser.close()
        print('PASS: APK platform/bounty/access filters, pagination, share URL, i18n, cross-page themes, 20 viewports, static first page, retry and safe rendering.')
    finally:
        server.shutdown();server.server_close();thread.join()


if __name__=='__main__':main()
