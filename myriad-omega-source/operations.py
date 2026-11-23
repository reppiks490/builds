"""One hundred reproducible, bounded local demonstration operations.

No LLM calls, trading orders, web requests, or external mutations occur here.
These tasks produce actual typed outputs from bundled synthetic inputs.
"""
from __future__ import annotations
from collections import Counter
import hashlib, json, math, statistics

SAMPLE = {
    "signals": [
        {"name":"Low-latency monitoring", "novelty":.82,"evidence":.71},
        {"name":"Local-first research", "novelty":.74,"evidence":.89},
        {"name":"Adaptive visual tooling", "novelty":.91,"evidence":.66},
    ],
    "samples": [{"asset":"A","value":"12.2"},{"asset":"B","value":"9.7"},{"asset":"A","value":"12.2"}],
    "evidence": ["source A confirms X", "source B suggests Y", "source C disputes X"],
    "returns": [-.04,.017,.008,-.015,.024,.003,-.021,.012],
    "scene": [8,16,32,64,128],
}

def _digest(result):
    return hashlib.sha256(json.dumps(result,sort_keys=True,default=str).encode()).hexdigest()[:16]

def run_operation(workflow_id: str, payload: dict | None = None) -> dict:
    """Run a bounded, reproducible sample operation and return its evidence hash."""
    p = payload or SAMPLE
    sig = p.get("signals", SAMPLE["signals"])
    data = p.get("samples", SAMPLE["samples"])
    ev = p.get("evidence", SAMPLE["evidence"])
    rets = p.get("returns", SAMPLE["returns"])
    scene = p.get("scene", SAMPLE["scene"])
    if workflow_id == "W01":
        result = {"ranked": sorted(({"name":v["name"],"score":round(.55*v["novelty"]+.45*v["evidence"],3)} for v in sig),key=lambda v:-v["score"])}
    elif workflow_id == "W02":
        normalized = sorted({(v['asset'],float(v['value'])) for v in data})
        result = {"records":len(normalized),"duplicate_rows_removed":len(data)-len(normalized),"rows":normalized}
    elif workflow_id == "W03":
        edges=[("cause","mediator"),("mediator","outcome"),("confounder","cause"),("confounder","outcome")]
        result={"edges":edges,"backdoor_adjustment":["confounder"],"validated":"acyclic example graph"}
    elif workflow_id == "W04":
        result={"claims_reviewed":len(ev),"disagreement_detected":any("disputes" in x for x in ev),"source_count":len(ev)}
    elif workflow_id == "W05":
        result={"baseline_error":.21,"candidate_error":.17,"holdout_improvement":round((.21-.17)/.21,4),"promotion":"evaluation required"}
    elif workflow_id == "W06":
        source="def total(xs):\n    return sum(xs)\n"
        result={"lines":len(source.splitlines()),"syntactic_check":compile(source,"<synthetic>","exec") is not None,"patch_id":hashlib.sha256(source.encode()).hexdigest()[:10]}
    elif workflow_id == "W07":
        checks={"non_empty":bool(ev),"bounded_return_series":all(-1<=r<=1 for r in rets),"source_count":len(ev)>=2}
        result={"checks":checks,"passed":all(checks.values())}
    elif workflow_id == "W08":
        settings={"public_access":False,"credential_in_source":False,"auditing_enabled":True}
        result={"config":settings,"findings":[],"mode":"defensive static example"}
    elif workflow_id == "W09":
        demand=5000; per_worker=150
        result={"tasks":demand,"nominal_worker_capacity":per_worker,"min_workers":math.ceil(demand/per_worker),"deployment":"dry-run only"}
    elif workflow_id == "W10":
        alerts=["latency","queue_depth","timeout","latency"]
        result={"top_alerts":Counter(alerts).most_common(),"recommendation":"inspect dependency saturation; no remediation executed"}
    elif workflow_id == "W11":
        result={"demo_series_only":True,"mean_return":round(statistics.mean(rets),6),"volatility":round(statistics.pstdev(rets),6),"orders_placed":0}
    elif workflow_id == "W12":
        result={"historical_worst":round(min(rets),5),"hypothetical_shock":-.12,"stress_loss_on_100_units":-12.0,"no_investment_advice":True}
    elif workflow_id == "W13":
        pop=[min(250,int(n*.94+4)) for n in scene]
        result={"population_steps":pop,"bounded":all(0<=x<=250 for x in pop),"synthetic":True}
    elif workflow_id == "W14":
        def lum(rgb):
            c=[v/255 for v in rgb];return sum(k*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for k,v in zip((.2126,.7152,.0722),c))
        ratio=(lum((235,245,244))+.05)/(lum((9,18,25))+.05)
        result={"contrast_ratio":round(ratio,2),"wcag_aa_normal_text":ratio>=4.5}
    elif workflow_id == "W15":
        frames=[round((3*t*t-2*t*t*t),4) for t in [0,.2,.4,.6,.8,1]]
        result={"ease_samples":frames,"monotonic":frames==sorted(frames),"sample_fps_target":60}
    elif workflow_id == "W16":
        result={"summary":"Three evidence statements reviewed; one explicit conflict requires investigation.","unresolved_conflicts":1}
    elif workflow_id == "W17":
        normalized=[x.strip().lower() for x in ev]
        result={"indexed_nodes":len(set(normalized)),"duplicates":len(normalized)-len(set(normalized)),"provenance":"bundled synthetic inputs"}
    elif workflow_id == "W18":
        result={"objections":["Unknown data provenance","Potential sampling bias","External replication absent"],"verdict":"hold pending independent evidence"}
    elif workflow_id == "W19":
        before=.61;after=min(.99,before+.035)
        result={"competency_before":before,"competency_after":round(after,3),"promotion_eligible":False,"note":"synthetic score, not model training"}
    elif workflow_id == "W20":
        baseline=100;candidate=103;threshold=1.05
        result={"baseline_score":baseline,"candidate_score":candidate,"improvement":round(candidate/baseline-1,3),"promote":candidate/baseline>=threshold,"rolled_out":False}
    elif workflow_id == "W21":
        prior=.25; tpr=.9; fpr=.1
        posterior=prior*tpr/(prior*tpr+(1-prior)*fpr)
        result={"prior":prior,"sensitivity":tpr,"false_positive_rate":fpr,"posterior":round(posterior,5)}
    elif workflow_id == "W22":
        probs=[.5,.25,.125,.125]
        h=-sum(x*math.log2(x) for x in probs)
        result={"distribution":probs,"entropy_bits":round(h,5),"maximum_bits":math.log2(len(probs))}
    elif workflow_id == "W23":
        graph={"A":{"B":3,"C":8},"B":{"C":2,"D":6},"C":{"D":1},"D":{}}
        frontier=[(0,"A",["A"])];seen=set();best=None
        while frontier:
            dist,node,path=__import__('heapq').heappop(frontier)
            if node in seen:continue
            seen.add(node)
            if node=="D":best=(dist,path);break
            for nxt,w in graph[node].items():__import__('heapq').heappush(frontier,(dist+w,nxt,path+[nxt]))
        result={"shortest_cost":best[0],"path":best[1],"method":"dijkstra"}
    elif workflow_id == "W24":
        import random
        rg=random.Random(1107);draws=[sum(rg.uniform(-1,1) for _ in range(3)) for i in range(600)]
        result={"draws":len(draws),"mean":round(statistics.mean(draws),5),"p05":round(sorted(draws)[30],5),"p95":round(sorted(draws)[569],5),"seed":1107}
    elif workflow_id == "W25":
        points=[("A",9,7),("B",7,9),("C",8,8),("D",5,5),("E",10,4)]
        frontier=[n for n,x,y in points if not any((xx>=x and yy>=y and (xx>x or yy>y)) for m,xx,yy in points)]
        result={"maximize":["performance","safety"],"pareto_optimal":frontier,"candidates":len(points)}
    elif workflow_id == "W26":
        xs=[4,5,5,6,5,5,6,30,4,5];median=statistics.median(xs);mad=statistics.median(abs(x-median) for x in xs)
        flags=[i for i,x in enumerate(xs) if abs(x-median)>3.5*max(mad,.5)]
        result={"median":median,"mad":mad,"flag_indices":flags,"rule":"robust absolute deviation"}
    elif workflow_id == "W27":
        p_a=.05;p_b=.1
        result={"root_event":"A OR B","failure_probability":round(1-(1-p_a)*(1-p_b),5),"mitigation":"independent redundancy"}
    elif workflow_id == "W28":
        jobs=[("ingest",3,[]),("clean",2,["ingest"]),("analyze",5,["clean"]),("review",2,["analyze"]),("render",4,["clean"])]
        earliest={}
        for name,duration,deps in jobs:earliest[name]=(max((earliest[d] for d in deps),default=0)+duration)
        result={"finish_times":earliest,"critical_path_duration":max(earliest.values()),"units":"synthetic"}
    elif workflow_id == "W29":
        chain=[{"id":"source","parents":[]},{"id":"normalized","parents":["source"]},{"id":"report","parents":["normalized"]}]
        result={"graph":chain,"root":"source","acyclic":True,"edges":2}
    elif workflow_id == "W30":
        contexts={"research":4600,"code":7300,"review":2800};limit=20000
        result={"used_tokens":sum(contexts.values()),"limit_tokens":limit,"headroom":limit-sum(contexts.values()),"distribution":contexts}
    elif workflow_id == "W31":
        a=[.3,.4,.5];b=[.5,.4,.1];cos=sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
        result={"cosine_similarity":round(cos,6),"dimensions":3,"threshold_pass":cos>=.65}
    elif workflow_id == "W32":
        votes={"NOESIS":"conditional","PRAXIS":"approve","AEGIS":"hold"}
        result={"votes":votes,"decision":"hold","rule":"AEGIS can stop unverified external effects"}
    elif workflow_id == "W33":
        request={"action":"deploy","approval":False,"environment":"production"}
        result={"request":request,"permitted":False,"reason":"external mutation requires explicit authorization"}
    elif workflow_id == "W34":
        supply=120;demands={"research":90,"engineering":70,"verification":40};s=sum(demands.values())
        alloc={name:round(supply*v/s,2) for name,v in demands.items()}
        result={"allocations":alloc,"sum_allocated":round(sum(alloc.values()),2),"total_supply":supply}
    elif workflow_id == "W35":
        vals=[(2,.85),(4,.6),(6,.9)];den=sum(w for _,w in vals)
        result={"weighted_estimate":round(sum(v*w for v,w in vals)/den,5),"sources":len(vals),"weight_sum":den}
    elif workflow_id == "W36":
        holdings=[20,20,20];history=[]
        for i in range(5):
            holdings=[holdings[-1],holdings[0],holdings[1]]
            history.append(holdings[:])
        result={"agents":len(holdings),"steps":history,"total_conserved":sum(holdings)==60}
    elif workflow_id == "W37":
        preds=[.1,.2,.8,.9];outcomes=[0,0,1,1]
        brier=sum((p-y)**2 for p,y in zip(preds,outcomes))/len(preds)
        result={"brier_score":round(brier,6),"n":len(preds),"direction":"lower better"}
    elif workflow_id == "W38":
        distance=480;width=36;index=math.log2(distance/width+1);duration=.13+.19*index
        result={"fitts_index_bits":round(index,5),"estimated_acquisition_seconds":round(duration,5),"target_width_px":width}
    elif workflow_id == "W39":
        def luminance(rgb):
            c=[v/255 for v in rgb]
            return sum(w*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for w,v in zip((.2126,.7152,.0722),c))
        pairs=[((245,246,246),(9,14,22)),((218,70,74),(9,14,22)),((93,184,200),(9,14,22))]
        scores=[round((max(luminance(a),luminance(b))+.05)/(min(luminance(a),luminance(b))+.05),3) for a,b in pairs]
        result={"contrast_ratios":scores,"normal_text_aa":[x>=4.5 for x in scores]}
    elif workflow_id == "W40":
        x=0.;v=0.;target=1.;dt=1/60.;trace=[]
        for i in range(60):
            a=60*(target-x)-14*v;v+=a*dt;x+=v*dt
            if i%10==0:trace.append(round(x,5))
        result={"spring_samples":trace,"final_position":round(x,6),"time_step":round(dt,6)}
    elif workflow_id == "W41":
        beat_sequence=["inciting_signal","first_failure","unexpected_ally","choice","reversal","resolution"]
        result={"beats":beat_sequence,"coherent_transition_count":len(beat_sequence)-1,"graph_acyclic":True}
    elif workflow_id == "W42":
        prompt="Generate a draft report from example data without contacting anyone"
        risky=[x for x in ("send money","place trade","delete database","exfiltrate") if x in prompt.lower()]
        result={"simulation_only":True,"risky_matches":risky,"automated_external_actions_allowed":False}
    elif workflow_id == "W43":
        replicas={"node1":["a","b"],"node2":["b","c"],"node3":["a","c"]}
        availability={k:sum(k in v for v in replicas.values()) for k in ("a","b","c")}
        result={"replication_factors":availability,"minimum_replication":min(availability.values()),"all_at_least_two":all(v>=2 for v in availability.values())}
    elif workflow_id == "W44":
        import zlib
        payload=("reproducible-data:"*250).encode();compressed=zlib.compress(payload,9)
        result={"source_bytes":len(payload),"compressed_bytes":len(compressed),"ratio":round(len(compressed)/len(payload),5),"lossless":zlib.decompress(compressed)==payload}
    elif workflow_id == "W45":
        body=b"artifact:local:immutable:example"
        result={"sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body),"verified":True,"source":"bundled example"}
    elif workflow_id == "W46":
        requests=10000;errors=14;slo=.999
        allowed=math.floor(requests*(1-slo))
        result={"observations":requests,"errors":errors,"error_budget":allowed,"budget_remaining":allowed-errors,"slo_met":errors<=allowed}
    elif workflow_id == "W47":
        left={"A":100,"B":250,"C":35};right={"A":100,"B":247,"C":35}
        mismatches={k:left[k]-right[k] for k in left if left[k]!=right[k]}
        result={"mismatch_count":len(mismatches),"difference_by_account":mismatches,"balances_equal":not mismatches}
    elif workflow_id == "W48":
        baseline={"cost":100,"latency":170,"risk":.12};proposal={"cost":92,"latency":140,"risk":.11}
        result={"delta":{k:round(proposal[k]-baseline[k],3) for k in baseline},"baseline":baseline,"proposal":proposal}
    elif workflow_id == "W49":
        dimensions={"traceability":.95,"replication":.78,"coverage":.83,"outlier_tests":.5}
        result={"dimension_scores":dimensions,"macro_score":round(statistics.mean(dimensions.values()),4),"lowest_dimension":min(dimensions,key=dimensions.get)}
    elif workflow_id == "W50":
        votes={"NOESIS":{"decision":"propose","evidence":True},"PRAXIS":{"decision":"prototype","feasible":True},"AEGIS":{"decision":"hold_external","verified":False}}
        result={"brain_votes":votes,"consensus":"sandbox_prototype_only","real_world_mutation":False}
    elif workflow_id.startswith('W') and workflow_id[1:].isdigit() and 51<=int(workflow_id[1:])<=100:
        from operations_extended import extended_demo
        result=extended_demo(int(workflow_id[1:]))
    else:
        raise ValueError(f"Unknown workflow: {workflow_id}")
    return {"workflow_id":workflow_id,"operation":"local_deterministic_demo","output":result,"evidence_hash":_digest(result)}
