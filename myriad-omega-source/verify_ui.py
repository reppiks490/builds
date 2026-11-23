"""Live, localhost HTTP + desktop/mobile browser smoke for the 100-workflow build."""
from __future__ import annotations
import json,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent

def get(url):
    with urllib.request.urlopen(url,timeout=8) as resp:return json.load(resp)

def post(url,data):
    raw=json.dumps(data).encode('utf8')
    req=urllib.request.Request(url,data=raw,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=8) as resp:return json.load(resp)

def main():
    with (ROOT/'server_verify.log').open('wb') as log:
        srv=subprocess.Popen([sys.executable,'server.py','--port','8789'],cwd=ROOT,stdout=log,stderr=log)
    try:
        base='http://127.0.0.1:8789'
        for i in range(100):
            try:
                health=get(base+'/api/health')
                if health['healthy']:break
            except Exception:time.sleep(.12)
        else:raise AssertionError('Server did not become healthy')
        assert health['live_actor_coroutines']==10000,health
        st=get(base+'/api/state')
        assert st['agent_total']==10000 and len(st['workflows'])==100
        fleet=get(base+'/api/training/fleet')
        assert fleet['gradient_trained_ledger_rows']==10000,fleet
        ag=get(base+'/api/training/agents/AG-10000')
        assert ag['byte_hash_verified'] and ag['gradient_steps']>=1
        policy=get(base+'/api/training/policy/AG-10000')
        assert policy['agent']=='AG-10000' and policy['agent_specific_parameters']==411000
        adaptation=get(base+'/api/adaptation/summary')
        assert adaptation['stored_candidate_count']==100 and adaptation['auto_promotions']==0
        adaptive_agent=get(base+'/api/adaptation/agents/AG-00001')
        assert adaptive_agent['events']
        sample=post(base+'/api/evaluate',{'workflow':'W100'})
        assert sample['output']['output']['promote'] is False
        pipeline=get(base+'/api/pipelines/P1000')
        assert pipeline['pipeline']=='P1000' and not pipeline['external_side_effects']
        # Browser sandbox blocks loopback navigation; exercise the exact HTML/CSS/JS
        # against REAL live-service responses captured above as local fixtures.
        fixture={'/api/state':st,'/api/models':get(base+'/api/models'),
                 '/api/training/fleet':fleet,'/api/training/agents/AG-10000':ag,
                 '/api/agents/AG-10000':get(base+'/api/agents/AG-10000'),
                 '/api/abilities/summary':get(base+'/api/abilities/summary'),
                 '/api/pipelines/P1000':pipeline,'/api/evaluate':sample,
                 '/api/training/policy/AG-10000':policy,
                 '/api/adaptation/summary':adaptation,
                 '/api/adaptation/agents/AG-00001':adaptive_agent}
        html=(ROOT/'index.html').read_text(encoding='utf8')
        html=html.replace('<link rel="stylesheet" href="/assets/theme.css">','').replace('<script src="/assets/console.js" defer></script>','')
        css=(ROOT/'assets/theme.css').read_text(encoding='utf8')
        js=(ROOT/'assets/console.js').read_text(encoding='utf8')
        def page_init(page):
            page.set_content(html,wait_until='domcontentloaded')
            page.add_style_tag(content=css)
            page.evaluate('''(fixtures)=>{window.fetch=async (url,options)=>({ok:Boolean(fixtures[url]),json:async()=>fixtures[url]||{error:'Fixture not captured: '+url}})}''',fixture)
            page.add_script_tag(content=js)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1600,'height':1000},device_scale_factor=1)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page_init(page)
            page.wait_for_function("document.querySelector('#actorLive').textContent.includes('10,000')",timeout=15000)
            page.wait_for_function("document.querySelector('#agentWeightsTrained').textContent.includes('10,000')",timeout=15000)
            assert page.locator('button.flow-item').count()==100
            page.locator('#agentLookup').fill('AG-10000')
            page.locator('#agentInspect').click()
            page.wait_for_function("document.querySelector('#agentWeightRecord').textContent.includes('VERIFIED')")
            page.locator('#runPolicySample').click()
            page.wait_for_function("document.querySelector('#agentPolicyRecord').textContent.includes('NO REAL TASK')")
            page.locator('#adaptiveInspect').click()
            page.wait_for_function("document.querySelector('#adaptiveRecord').textContent.includes('candidate_sha256')")
            page.locator('#pipelineLookup').fill('P1000')
            page.locator('#pipelineInspect').click()
            page.wait_for_function("document.querySelector('#pipelineRecord').textContent.includes('P1000')")
            page.locator('#runSample').click()
            page.wait_for_function("document.querySelector('#taskOutput').textContent.includes('evidence_hash')")
            assert not errors,errors
            page.screenshot(path=str(ROOT/'preview-v1-desktop.png'),full_page=True,animations='disabled')
            phone=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
            merrors=[];phone.on('pageerror',lambda e:merrors.append(str(e)))
            page_init(phone)
            phone.wait_for_function("document.querySelector('#actorLive').textContent.includes('10,000')",timeout=15000)
            extent=phone.evaluate('({scroll:document.documentElement.scrollWidth,viewport:innerWidth})')
            assert extent['scroll']<=extent['viewport']+1,extent
            assert not merrors,merrors
            phone.screenshot(path=str(ROOT/'preview-v1-mobile.png'),full_page=True,animations='disabled')
            browser.close()
        results={'schema':'myriad.ui_live_e2e.v1','registered':10000,'trained_agents_ledger':10000,
                 'byte_checked_agent_10000':True,'agent_10000_real_neural_policy_inference':True,'all_100_workflows_visible':True,
                 'pipeline_P1000_read_only':True,'adaptive_memory_evidence_count':100,'desktop_js_errors':errors,'mobile_js_errors':merrors,
                 'phone_horizontal_overflow':False,'browser_test_mode':'real backend HTTP via urllib; browser rendered with captured live-API fixtures because browser localhost navigation blocked by environment'}
        (ROOT/'BROWSER_VERIFICATION.json').write_text(json.dumps(results,indent=2)+'\n')
        print(json.dumps(results,indent=2))
    finally:
        srv.terminate()
        try:srv.wait(timeout=8)
        except subprocess.TimeoutExpired:srv.kill()

if __name__=='__main__':main()
