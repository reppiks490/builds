"""50 bounded, reproducible offline engineering/research exercises (W51–W100).

These demonstrate real computations on synthetic/illustrative inputs and are
neither paid APIs nor independent evidence of domain mastery. No effects.
"""
from __future__ import annotations
import collections,hashlib,itertools,math,random,statistics


def extended_demo(number:int)->dict:
    if not 51<=number<=100:raise ValueError('Only workflows W51–W100')
    if number==51:
        observed=[2,4,8,16]; hypotheses={'linear':[2,4,6,8],'exponential':[2,4,8,16]}
        return {'hypothesis_mse':{k:statistics.mean((a-b)**2 for a,b in zip(v,observed)) for k,v in hypotheses.items()},'best':'exponential','scope':'synthetic'}
    if number==52:
        options=[('A',8,4),('B',6,8),('C',3,5),('D',9,3)]
        nondominated=[n for n,x,y in options if not any((xx>=x and yy>=y and(xx>x or yy>y)) for _,xx,yy in options)]
        return {'pareto_front':nondominated,'axes':['quality','reliability']}
    if number==53:
        timestamps=list(range(25));train=timestamps[:15];embargo=timestamps[15:18];holdout=timestamps[18:]
        return {'training':(min(train),max(train)),'embargo':embargo,'holdout':(min(holdout),max(holdout)),'temporal_leakage':bool(set(train)&set(holdout))}
    if number==54:
        phrase={'en':'risk review','es':'revisión de riesgos','fr':'examen des risques'}
        return {'locale_count':len(phrase),'all_present':all(phrase.values()),'source_language':'en','translated_by_model':False}
    if number==55:
        bins=[(.1,0,10),(.7,6,10),(.9,9,10)];ece=sum(abs(p-h/n)*(n/30) for p,h,n in bins)
        return {'expected_calibration_error':round(ece,5),'bins':len(bins),'real_data':False}
    if number==56:
        n=31;divisors=[i for i in range(2,n) if n%i==0]
        return {'claim':'31 is prime','verified':not divisors,'tested_divisors':n-2,'finite_integer_proof':True}
    if number==57:
        grid={(x,y) for x in range(4) for y in range(4)};blocked={(1,1),(2,2)}
        return {'nodes':len(grid-blocked),'reachable_from_origin':len(grid-blocked),'obstacles':sorted(blocked),'scope':'bounded grid'}
    if number==58:
        observations=[('water',20,1.0),('water',30,1.1),('water',40,1.2)]
        return {'compound':'water','measured_example_points':len(observations),'trend_positive':all(a[2]<=b[2] for a,b in zip(observations,observations[1:])), 'synthetic_not_chemical_instructions':True}
    if number==59:
        seq='ACGTACGTGGAT';counts=dict(collections.Counter(seq));return {'sequence_length':len(seq),'base_counts':counts,'gc_fraction':round((counts.get('G',0)+counts.get('C',0))/len(seq),4),'clinical_use':False}
    if number==60:
        studies=[('S1','positive','low'),('S2','mixed','moderate'),('S3','negative','high')]
        return {'studies':len(studies),'effects':dict(collections.Counter(s[1] for s in studies)),'grade':'uncertain','individual_diagnosis':False}
    if number==61:
        rules={'region_a':{'consent':True,'retention_days':30},'region_b':{'consent':True,'retention_days':7}}
        return {'jurisdictions':list(rules),'retention_difference_days':23,'legal_advice':False,'hypothetical':True}
    if number==62:
        packet={'version':1,'message_id':'abc','payload':'research'}
        return {'required_fields':sorted(packet),'schema_valid':set(packet)=={'version','message_id','payload'},'read_only':True}
    if number==63:
        replicas=5;f=1;return {'replicas':replicas,'fault_tolerance_f':f,'byzantine_threshold_satisfied':replicas>=3*f+1,'network_partition_test':'not run'}
    if number==64:
        vendors={'A':20,'B':25,'C':30};demand=37
        return {'demand':demand,'capacity_excluding_highest':sum(sorted(vendors.values())[:-1]),'one_vendor_failure_safe':sum(sorted(vendors.values())[:-1])>=demand}
    if number==65:
        supply=[100,95,103];demand=[98,100,99]
        return {'hourly_surplus':[s-d for s,d in zip(supply,demand)],'net_energy_balance':sum(supply)-sum(demand),'synthetic_grid':True}
    if number==66:
        exposure=[.2,.6,.9];mitigated=[round(x*.7,3) for x in exposure]
        return {'mean_exposure_before':round(statistics.mean(exposure),3),'mean_exposure_after':round(statistics.mean(mitigated),3),'not_climate_forecast':True}
    if number==67:
        trips=[(2,12),(3,8),(1,20)];return {'total_trips':sum(n for n,_ in trips),'mean_travel_minutes':round(sum(n*t for n,t in trips)/sum(n for n,_ in trips),2),'hypothetical_city':True}
    if number==68:
        period=2*math.pi*math.sqrt(7**3/1);return {'dimensionless_orbital_period':round(period,5),'energy':round(-1/(2*7),5),'simplified_two_body_model':True}
    if number==69:
        sensor=[4.5,4.7,4.6];twin=[4.6,4.6,4.6]
        return {'digital_twin_rmse':round(math.sqrt(statistics.mean((x-y)**2 for x,y in zip(sensor,twin))),5),'synthetic_calibration':True}
    if number==70:
        coords=(3.,4.);radius=2.;obstacle=(4.,4.)
        return {'robot_pose':coords,'obstacle_clearance':round(math.dist(coords,obstacle)-radius,3),'collision_warning':math.dist(coords,obstacle)<radius,'real_robot_connected':False}
    if number==71:
        text='bank may mean financial institution or river edge';return {'token_count':len(text.split()),'ambiguous_term':'bank','senses':['financial','geographic'],'resolution':'requires context'}
    if number==72:
        answers=[True,False,True,True];return {'questions':4,'passing':sum(answers),'accuracy':sum(answers)/4,'unseen_questions_not_provided':True}
    if number==73:
        states=list(range(8));return {'property':'x^2 >= 0 over integers 0..7','counterexamples':[x for x in states if x*x<0],'proof_scope':'finite enumeration'}
    if number==74:
        tests=[{'a','b'},{'c','d'},{'b','e'}];mutants={'a','b','c','d','e'}
        return {'mutation_score':len(set().union(*tests)&mutants)/len(mutants),'test_count':len(tests),'mutants_total':len(mutants)}
    if number==75:
        trace=['ok','timeout','timeout','ok','error','timeout'];return {'timeouts':trace.count('timeout'),'errors':trace.count('error'),'dominant_failure':'timeout','log_scope':'synthetic'}
    if number==76:
        sbom=[('lib-a','MIT'),('lib-b','Apache-2.0'),('lib-c','UNKNOWN')]
        return {'components':len(sbom),'license_review_required':[n for n,lic in sbom if lic=='UNKNOWN'],'no_network_scan':True}
    if number==77:
        epsilon=.8;true_value=25;noise=.5
        return {'epsilon':epsilon,'toy_noisy_statistic':true_value+noise,'dp_guarantee_certified':False,'purpose':'illustrative privacy assessment'}
    if number==78:
        role_permissions={'viewer':{'read'},'operator':{'read','submit'}}
        return {'roles':len(role_permissions),'viewer_mutation_denied':'submit' not in role_permissions['viewer'],'least_privilege':True}
    if number==79:
        risks=[(3,4),(1,5),(2,2)];return {'risk_priority_numbers':[a*b for a,b in risks],'highest':max(a*b for a,b in risks),'manual_review_required':True}
    if number==80:
        budget=round(1_000_000*(1-.999),2);return {'requests':1000000,'availability_target':.999,'error_budget_requests':budget,'synthetic':True}
    if number==81:
        uncertainty=[.1,.8,.3,.9];return {'query_indices':sorted(range(len(uncertainty)),key=lambda i:-uncertainty[i])[:2],'selection_rule':'uncertainty sampling','learning_not_run':True}
    if number==82:
        pupil=[2,5,6];return {'skills_passed':pupil,'promotion_allowed':False,'gate':'blind assessment and human review required','supervisor_slots':4}
    if number==83:
        triples=[('a','type','source'),('a','supports','b'),('b','type','hypothesis')];return {'triples':len(triples),'typed_nodes':2,'evidence_relationships':1}
    if number==84:
        records=[('fact',1),('fact',2)];return {'contradiction_count':len({v for _,v in records})-1,'conflict_detected':True,'auto_resolve':False}
    if number==85:
        payoffs=[(2,2),(3,-2),(-2,3)];return {'joint_rewards':[a+b for a,b in payoffs],'harmful_asymmetry_detected':any(a<0 or b<0 for a,b in payoffs),'not_live_social_system':True}
    if number==86:
        jobs=[8,4,6,3,5];workers=[0,0,0]
        for j in sorted(jobs,reverse=True):workers[workers.index(min(workers))]+=j
        return {'assignments_load':workers,'max_load':max(workers),'min_load':min(workers),'fairness_gap':max(workers)-min(workers)}
    if number==87:
        eval_ids={'T1','T2','T3'};training_ids={'T0','T2'}
        return {'holdout_overlap':sorted(eval_ids&training_ids),'contaminated':bool(eval_ids&training_ids),'benchmark_pass':False}
    if number==88:
        baseline=.92;unseen=.68;return {'training_domain_score':baseline,'unseen_domain_score':unseen,'generalization_gap':round(baseline-unseen,4),'transfer_certified':False}
    if number==89:
        confounder={'treatment':[0,1,1,0], 'outcome':[1,3,4,2]}
        return {'treatment_outcome_correlation':round(statistics.correlation(confounder['treatment'],confounder['outcome']),4),'causal_effect_identified':False,'reason':'confounders not controlled'}
    if number==90:
        shocks=[-.02,0,.03];base=100
        return {'scenarios':[{ 'shock':s,'index':round(base*(1+s),2)} for s in shocks],'forecast_claim':False}
    if number==91:
        rets=[-.02,.01,.03,-.04];equity=10000;curve=[equity]
        for r in rets:equity*=1+r;curve.append(round(equity,2))
        return {'paper_equity_path':curve,'end':curve[-1],'orders_placed':0,'fees_included':False,'edge_proven':False}
    if number==92:
        spot=100;strike=105;premium=3
        return {'expiry_call_pnl':[{ 'spot':s,'pnl':max(s-strike,0)-premium} for s in [90,100,105,110,120]],'hypothetical':True}
    if number==93:
        asks=[(101,3),(102,5)];qty=4;notional=101*3+102*1
        return {'synthetic_buy_quantity':qty,'fill_notional':notional,'vwap':notional/qty,'real_orderbook_replay':False}
    if number==94:
        bars=[('2026-01-01T12:00','2026-01-01T11:55'),('2026-01-01T12:01','2026-01-01T12:03')]
        return {'features_after_decision':[i for i,(decision,feature) in enumerate(bars) if feature>decision],'leakage_found':True,'reject_backtest':True}
    if number==95:
        facts=['a','b'];draft='Claim a based on a; claim c unsupported'
        return {'known_source_ids':facts,'unsupported_claims':['c'],'approved_for_publication':False,'sample_draft':draft}
    if number==96:
        spacing=[4,8,12,16,24,32];return {'spacing_tokens':spacing,'monotonic':spacing==sorted(spacing),'contrast_check_required':True}
    if number==97:
        frames=[0,10,20,30,40];return {'keyframe_times_ms':frames,'frame_intervals_ms':[b-a for a,b in zip(frames,frames[1:])],'reduced_motion_alternative':True}
    if number==98:
        resources=[100];
        for i in range(4):resources.append(resources[-1]+12-9)
        return {'synthetic_world_resource_trace':resources,'resource_nonnegative':all(r>=0 for r in resources),'state_hash':hashlib.sha256(str(resources).encode()).hexdigest()[:16]}
    if number==99:
        matrix={'read':['viewer','operator'],'deploy':['owner'],'merge':['owner']};return {'permission_matrix':matrix,'agent_can_merge':False,'human_approval_required':True}
    if number==100:
        before=[.5,.6,.7];after=[.6,.65,.61];delta=statistics.mean(after)-statistics.mean(before)
        return {'mean_delta':round(delta,4),'all_seeds_improve':all(a>b for a,b in zip(after,before)),'promote':False,'reason':'regression on seed 3'}
    raise AssertionError('Unreachable')
