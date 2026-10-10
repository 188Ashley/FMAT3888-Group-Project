"""Q2: fully invested, long-only baseline with a 50% index cap.
Run: python Q2_github/Q2_full_analysis.py
Bundled Q1 exports supply the inputs. Default outputs go to generated/.
The main model is capped at 50%; other caps and signed weights are comparisons.
"""
from report_template import write_report
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog, minimize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
FEASIBILITY_TOL=1e-8
ACTIVE_TOL=1e-7

def optimise(mean, covariance, target=None, initial=None, cap=0.50):
    """Convex variance minimisation, with optional minimum expected return."""
    n = len(mean)
    constraints = [{"type": "eq", "fun": lambda x: x.sum() - 1,
                    "jac": lambda x: np.ones(n)}]
    if target is not None:
        constraints.append({"type": "ineq",
                            "fun": lambda x: mean @ x - target,
                            "jac": lambda x: mean})
    result = minimize(
        lambda x: 100 * (x @ covariance @ x),
        np.ones(n) / n if initial is None else initial,
        jac=lambda x: 200 * covariance @ x,
        bounds=[(0, cap)] * n,
        constraints=constraints,
        method="SLSQP",
        options={"ftol": 1e-11, "maxiter": 2000},
    )
    if not result.success:
        raise RuntimeError(f"Optimisation failed: {result.message}")
    weights = result.x

    # Refine the active constraints using the equality-constrained KKT system.
    equality_rows, rhs = [np.ones(n)], [1.0]
    if target is not None and abs(mean @ weights - target) < ACTIVE_TOL:
        equality_rows.append(mean)
        rhs.append(target)
    for i, weight in enumerate(weights):
        if weight < ACTIVE_TOL or weight > cap - ACTIVE_TOL:
            row = np.zeros(n)
            row[i] = 1
            equality_rows.append(row)
            rhs.append(0.0 if weight < ACTIVE_TOL else cap)
    equality_rows, rhs = np.array(equality_rows), np.array(rhs)
    system = np.block([[2 * covariance, equality_rows.T],
                       [equality_rows, np.zeros((len(rhs), len(rhs)))]])
    refined = np.linalg.lstsq(system, np.r_[np.zeros(n), rhs], rcond=None)[0][:n]
    if (np.max(abs(equality_rows @ refined - rhs)) < 1e-9
            and refined.min() > -1e-9 and refined.max() < cap + 1e-9
            and (target is None or mean @ refined >= target - 1e-9)):
        weights = refined

    residual = max(abs(weights.sum() - 1), max(0, -weights.min()),
                   max(0, weights.max() - cap),
                   0 if target is None else max(0, target - mean @ weights))
    if residual > FEASIBILITY_TOL:
        raise RuntimeError(f"Portfolio infeasible: residual {residual}")

    # Dual feasibility certificate for stationarity and complementary slackness.
    # Upper-bound multipliers implement the selected exposure limit.
    stationarity = np.column_stack([np.ones(n), -mean, -np.eye(n), np.eye(n)])
    target_bound = ((0, 0) if target is None or mean @ weights - target > ACTIVE_TOL
                    else (0, None))
    dual_bounds = [(None, None), target_bound]
    dual_bounds += [(0, None) if w < ACTIVE_TOL else (0, 0) for w in weights]
    dual_bounds += [(0, None) if w > cap - ACTIVE_TOL else (0, 0) for w in weights]
    certificate = linprog(
        np.zeros(2 + 2 * n), A_eq=stationarity, b_eq=-2 * covariance @ weights,
        bounds=dual_bounds, method="highs",
        options={"primal_feasibility_tolerance": ACTIVE_TOL,
                 "dual_feasibility_tolerance": ACTIVE_TOL},
    )
    if not certificate.success:
        raise RuntimeError("Portfolio failed the KKT optimality certificate.")
    variance = float(weights @ covariance @ weights)
    if variance < -1e-12:
        raise RuntimeError("Negative portfolio variance.")
    return {"weights": weights.tolist(), "target": target,
            "expected_return": float(mean @ weights),
            "variance": variance, "volatility": float(np.sqrt(max(0, variance))),
            "primal_residual": float(residual), "kkt_passed": True}


def read_q1(directory):
    returns_path=directory/'Q1_clean_monthly_returns.csv'
    parameters_path=directory/'Q1_baseline_parameters.csv'
    workbook_path=directory/'Q1_results.xlsx'
    returns=pd.read_csv(returns_path,index_col=0,parse_dates=True,float_precision='round_trip')
    parameters=pd.read_csv(parameters_path,float_precision='round_trip').set_index('Asset')
    assets=returns.columns.tolist()
    if len(assets)!=9 or len(set(assets))!=9 or parameters.index.tolist()!=assets:
        raise ValueError('Q1 asset labels/order inconsistent.')
    if not returns.index.is_unique or not returns.index.is_monotonic_increasing:
        raise ValueError('Q1 return dates must be unique and sorted.')
    if not np.all(np.diff(returns.index.to_period('M').asi8)==1):
        raise ValueError('Q1 returns must cover consecutive months.')
    if not np.isfinite(returns.values).all() or (returns.values<=-1).any():
        raise ValueError('Missing/invalid simple returns; no filling or row removal permitted.')
    if len(returns)<120:
        raise ValueError('Q1 sample lacks the requested 120/60-month sensitivity windows.')
    period_table=pd.read_excel(workbook_path,sheet_name='Q1e_Period_Comparison',header=3)
    samples={'Full sample':returns,'Recent 10 years':returns.iloc[-120:],'Recent 5 years':returns.iloc[-60:]}
    models={};checks=[]
    for label,sample in samples.items():
        sheet='Q1c_Covariance' if label=='Full sample' else ('Q1e_10y_Covariance' if label=='Recent 10 years' else 'Q1e_5y_Covariance')
        covariance=pd.read_excel(workbook_path,sheet_name=sheet,header=3,index_col=0)
        if covariance.index.tolist()!=assets or covariance.columns.tolist()!=assets:
            raise ValueError(f'Q1 covariance labels/order inconsistent: {label}')
        p=period_table[period_table.Period.eq('Full common sample' if label=='Full sample' else label)].set_index('Asset')
        if set(p.index)!=set(assets) or len(p)!=9:
            raise ValueError('Missing/duplicate Q1 period asset rows.')
        p=p.loc[assets]
        if not pd.to_datetime(p.First_return_date).eq(sample.index[0]).all() or not pd.to_datetime(p.Last_return_date).eq(sample.index[-1]).all() or not p.Return_observations.eq(len(sample)).all():
            raise ValueError('Q1 exported period does not match the clean returns.')
        if label=='Full sample':
            mean=parameters.Annualised_Expected_Return.values
            if not np.allclose(mean,p.Annualised_Expected_Return.values,atol=1e-12,rtol=0):
                raise ValueError('Q1 baseline CSV and workbook means disagree.')
        else:
            mean=p.Annualised_Expected_Return.values
        c=covariance.values
        mean_error=float(np.max(abs(mean-sample.mean().values*12)))
        covariance_error=float(np.max(abs(c-sample.cov().values*12)))
        if mean_error>1e-12 or covariance_error>1e-12:
            raise ValueError('Q1 exported moments disagree with exported returns.')
        if not np.isfinite(mean).all() or not np.isfinite(c).all() or np.max(abs(c-c.T))>1e-12:
            raise ValueError('Invalid/asymmetric Q1 covariance or mean.')
        eigenvalues=np.linalg.eigvalsh(c);np.linalg.cholesky(c)
        if eigenvalues.min()<=0:
            raise ValueError('Positive definite covariance required for these verified runs.')
        models[label]={'n_returns':len(sample),'start':str(sample.index[0].date()),'end':str(sample.index[-1].date()),
                       'mean':mean.tolist(),'covariance':c.tolist(),'minimum_eigenvalue':float(eigenvalues.min()),'cases':{}}
        checks.append({'model':label,'mean_export_error':mean_error,'covariance_export_error':covariance_error})
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (returns_path,parameters_path,workbook_path)}
    return assets,models,checks,hashes


def check_growth(path,assets,cap):
    if path is None:
        return {'status':'Not checked: APRA growth fractions were not supplied.'}
    table=pd.read_csv(path).set_index('Asset')
    if len(table)!=len(assets) or not table.index.is_unique or set(table.index)!=set(assets):
        raise ValueError('Growth classification must contain every exact Q1 asset label once.')
    g=table.loc[assets,'Growth_fraction'].to_numpy(dtype=float)
    if not np.isfinite(g).all() or g.min()<0 or g.max()>1:
        raise ValueError('Growth fractions must be finite and in [0,1].')
    lo=linprog(g,A_eq=np.ones((1,len(g))),b_eq=[1],bounds=[(0,cap)]*len(g),method='highs')
    hi=linprog(-g,A_eq=np.ones((1,len(g))),b_eq=[1],bounds=[(0,cap)]*len(g),method='highs')
    if not lo.success or not hi.success:
        raise RuntimeError('Growth exposure feasibility calculation failed.')
    lower=float(lo.fun);upper=float(-hi.fun)
    return {'status':'Checked against supplied classification; APRA interpretation remains the group responsibility.',
            'minimum_growth':lower,'maximum_growth':upper,
            'targets':{str(a):bool(lower-1e-9<=a<=upper+1e-9) for a in (.3,.7,.9)}}


def signed_portfolio(mean,covariance,target=None):
    """Unrestricted mathematical benchmark; financing and borrowing costs omitted."""
    one=np.ones(len(mean));v=np.linalg.solve(covariance,one);weights=v/(one@v)
    multipliers=np.array([2/(one@v),0.])
    if target is not None and mean@weights<target:
        a=np.vstack([one,mean]);v=np.linalg.solve(covariance,a.T)
        multipliers=2*np.linalg.solve(a@v,np.array([1.,target]));weights=v@(multipliers/2)
        if multipliers[1]<-1e-9:
            raise RuntimeError('Signed return multiplier invalid.')
    residual=max(abs(weights.sum()-1),max(0,0 if target is None else target-mean@weights),float(np.max(abs(2*covariance@weights-multipliers[0]*one-multipliers[1]*mean))))
    if residual>1e-8:
        raise RuntimeError('Signed benchmark failed feasibility/stationarity.')
    return {'weights':weights.tolist(),'expected_return':float(mean@weights),
            'volatility':float(np.sqrt(weights@covariance@weights)),
            'gross_exposure':float(abs(weights).sum()),'short_exposure':float(np.maximum(-weights,0).sum()),
            'check_residual':residual}

def signed_comparison(mean,covariance):
    gmv=signed_portfolio(mean,covariance)
    # Plot endpoint is a display range, not a signed-weight exposure constraint.
    points=[signed_portfolio(mean,covariance,float(t)) for t in np.linspace(gmv['expected_return'],mean.max(),81)]
    return {'gmv':gmv,'selected_targets':{str(t):signed_portfolio(mean,covariance,t) for t in (.04,.06,.08)},
            'frontier':points,'costs_included':False,'gross_exposure_limit':None}

def make_figures(models,case_specs,figures):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    colours=['#222222','#126b8b','#c27822','#894d9b','#4e8c51']
    def draw(ax,case,label,colour):
        points=case['frontier'];ax.plot([p['volatility']*100 for p in points],[p['expected_return']*100 for p in points],label=label,color=colour)
        g=case['gmv'];ax.scatter(g['volatility']*100,g['expected_return']*100,s=20,color=colour)
    def style(ax):
        ax.set(xlabel='Annualised volatility (%)',ylabel='Annualised expected return (%)');ax.grid(alpha=.2);ax.legend(fontsize=7)
    full=models['Full sample']
    fig,ax=plt.subplots(figsize=(7.0,4.0))
    draw(ax,full['cases']['Baseline: 50% cap'],'50% cap: efficient frontier','#126b8b')
    g=full['cases']['Baseline: 50% cap']['gmv'];ax.annotate('GMV',(100*g['volatility'],100*g['expected_return']),xytext=(7,7),textcoords='offset points',fontsize=9)
    style(ax);fig.tight_layout();fig.savefig(figures/'Q2_baseline_frontier.pdf');fig.savefig(figures/'Q2_baseline_frontier.png',dpi=180);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10.2,4))
    for i,(case,cap) in enumerate(case_specs):draw(axs[0],full['cases'][case],'Uncapped benchmark' if cap==1 else ('50% cap: baseline' if cap==.5 else f'{cap:.0%} cap'),colours[i%len(colours)])
    draw(axs[1],full['cases'][case_specs[0][0]],'50% cap: long-only baseline',colours[0]);draw(axs[1],full['cases']['Uncapped benchmark'],'Uncapped long-only benchmark','#126b8b');draw(axs[1],full['unrestricted_signed'],'Unrestricted signed weights','#bd433d')
    for ax in axs:style(ax)
    axs[0].set_title('Index-cap comparisons');axs[1].set_title('Short-selling comparison (costs omitted)')
    fig.tight_layout();fig.savefig(figures/'Q2a_alternative_frontiers.pdf');fig.savefig(figures/'Q2a_alternative_frontiers.png',dpi=180);plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(10.2,3.4))
    for ax,(label,model) in zip(axs,models.items()):
        for i,(case,cap) in enumerate(case_specs):draw(ax,model['cases'][case],'Uncapped' if cap==1 else f'{cap:.0%} cap',colours[i%len(colours)])
        style(ax);ax.set_title(label,fontsize=10);ax.set_xlabel('Volatility (%)');ax.set_ylabel('Expected return (%)');ax.legend(fontsize=6.5)
    fig.tight_layout();fig.savefig(figures/'Q2a_window_frontiers.pdf');fig.savefig(figures/'Q2a_window_frontiers.png',dpi=180);plt.close(fig)


def baseline_summary(models,assets,tables):
    """Tables for Q2(b)--(d); keep exact weights and signed zeros in raw outputs."""
    baseline='Baseline: 50% cap';full=models['Full sample']['cases'][baseline]
    gmv=[];targets=[];distances=[]
    for label,model in models.items():
        case=model['cases'][baseline]
        for a,w in zip(assets,case['gmv']['weights']):
            gmv.append({'model':label,'Asset':a,'weight':w,'expected_return':case['gmv']['expected_return'],'volatility':case['gmv']['volatility']})
        for key,p in case['selected_targets'].items():
            x=np.array(p['weights']);ref=full['selected_targets'][key]
            targets.append({'model':label,'target':float(key),'achieved_return':p['expected_return'],'volatility':p['volatility'],
                            'largest_weight':float(x.max()),'largest_index':assets[int(x.argmax())],**dict(zip(assets,x))})
            distances.append({'model':label,'portfolio':key,'half_L1_distance_from_full':float(.5*abs(x-np.array(ref['weights'])).sum())})
        distances.append({'model':label,'portfolio':'GMV','half_L1_distance_from_full':float(.5*abs(np.array(case['gmv']['weights'])-full['gmv']['weights']).sum())})
    pd.DataFrame(gmv).to_csv(tables/'Q2_baseline_GMV_allocations.csv',index=False,float_format='%.17g')
    pd.DataFrame(targets).to_csv(tables/'Q2_baseline_target_returns.csv',index=False,float_format='%.17g')
    pd.DataFrame(distances).to_csv(tables/'Q2_baseline_allocation_sensitivity.csv',index=False,float_format='%.17g')

def main():
    here=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--q1-dir',type=Path,default=here/'inputs'/'Q1_exports')
    parser.add_argument('--output-dir',type=Path,default=here/'generated')
    parser.add_argument('--caps',type=float,nargs='*',default=[.40,.30],help='Additional comparison caps; baseline remains 50%%, with an uncapped benchmark.')
    parser.add_argument('--growth-classification',type=Path,help='Optional CSV with Asset and Growth_fraction from the course APRA methodology.')
    args=parser.parse_args()
    assets,models,input_checks,hashes=read_q1(args.q1_dir)
    if any(not 1/len(assets)<=cap<1 for cap in args.caps) or len(set(args.caps))!=len(args.caps) or .5 in args.caps:
        raise ValueError('Comparison caps must be distinct and in [1/n,1).')
    case_specs=[('Baseline: 50% cap',.5),('Uncapped benchmark',1.)]+[(f'Comparison: {cap:.0%} cap',cap) for cap in args.caps]
    tables=args.output_dir/'results';figures=args.output_dir/'figures'
    tables.mkdir(parents=True,exist_ok=True);figures.mkdir(parents=True,exist_ok=True)
    records=[];comparisons=[];sensitivity=[]
    output={'assets':assets,'baseline_cap':.5,'comparison_caps':args.caps,'source_hashes':hashes,
            'input_checks':input_checks,'models':models,
            'q3_feasibility':check_growth(args.growth_classification,assets,.5)}
    for label,model in models.items():
        mean=np.array(model['mean']);c=np.array(model['covariance']);slug=label.lower().replace(' ','_')
        pd.DataFrame({'Asset':assets,'Annualised_Expected_Return':mean,'Annualised_Volatility':np.sqrt(np.diag(c))}).to_csv(tables/f'Q2_parameters_{slug}.csv',index=False,float_format='%.17g')
        pd.DataFrame(c,index=assets,columns=assets).to_csv(tables/f'Q2_covariance_{slug}.csv',float_format='%.17g')
        for case,cap in case_specs:
            gmv=optimise(mean,c,cap=cap)
            maximum=linprog(-mean,A_eq=np.ones((1,len(mean))),b_eq=[1],bounds=[(0,cap)]*len(mean),method='highs')
            if not maximum.success:
                raise RuntimeError('Maximum-return LP failed.')
            maxmean=float(mean@maximum.x)
            frontier=[];initial=np.array(gmv['weights'])
            for target in np.linspace(gmv['expected_return'],maxmean,81):
                portfolio=optimise(mean,c,float(target),initial,cap)
                initial=np.array(portfolio['weights']);frontier.append(portfolio)
            if np.min(np.diff([p['variance'] for p in frontier])) < -1e-10:
                raise RuntimeError('Nonmonotone efficient frontier.')
            selected={str(t):optimise(mean,c,t,cap=cap) for t in (.03,.04,.05,.06,.07,.08,.09,.095) if t<=maxmean}
            below=optimise(mean,c,float(mean.min()),cap=cap)
            if abs(below['variance']-gmv['variance'])>1e-10:
                raise RuntimeError('Below-GMV requirement should return the GMV portfolio.')
            model['cases'][case]={'cap':cap,'gmv':gmv,'maximum_return':maxmean,'frontier':frontier,'selected_targets':selected}
            for kind,portfolios in [('GMV',[gmv]),('Frontier',frontier),('Selected',list(selected.values())),('Below GMV check',[below])]:
                for p in portfolios:
                    x=np.array(p['weights'])
                    records.append({'model':label,'case':case,'kind':kind,
                                    **{k:v for k,v in p.items() if k!='weights'},'largest_weight':float(x.max()),
                                    **dict(zip(assets,p['weights']))})
            print(label,case,'GMV',gmv['expected_return'],gmv['volatility'],'maximum mean',maxmean)
        model['unrestricted_signed']=signed_comparison(mean,c)
        for case,cap in case_specs:
            if cap==1.:
                continue
            for key,p in model['cases'][case]['selected_targets'].items():
                benchmark=model['cases']['Uncapped benchmark']['selected_targets'][key]
                if p['variance']<benchmark['variance']-1e-10:
                    raise RuntimeError('Nested-feasible-set variance comparison failed.')
                comparisons.append({'model':label,'comparison_cap':cap,'target':float(key),
                                    'capped_volatility':p['volatility'],'uncapped_volatility':benchmark['volatility'],
                                    'volatility_cost':p['volatility']-benchmark['volatility'],
                                    'capped_return':p['expected_return'],'uncapped_return':benchmark['expected_return']})
    full=models['Full sample']
    for label,model in models.items():
        for case,result in model['cases'].items():
            for key,p in [('GMV',result['gmv'])]+list(result['selected_targets'].items()):
                if key!='GMV' and key not in full['cases'][case]['selected_targets']:
                    continue  # No matched full-sample portfolio exists above that case's maximum.
                reference=full['cases'][case]['gmv'] if key=='GMV' else full['cases'][case]['selected_targets'][key]
                sensitivity.append({'model':label,'case':case,'portfolio':key,
                                    'half_L1_allocation_distance':float(.5*np.abs(np.array(p['weights'])-np.array(reference['weights'])).sum())})
    output['verification']={'solved_portfolios':len(records),'all_kkt_passed':all(p['kkt_passed'] for p in records),
                            'maximum_primal_residual':max(p['primal_residual'] for p in records),
                            'frontier_monotonicity_passed':True,'nested_feasible_set_comparison_passed':True,
                            'below_gmv_tests_passed':True,'kkt_certificate_tolerance':ACTIVE_TOL}
    configuration={'recommended_constraints':{'sum_weights':1,'lower_bounds':[0]*len(assets),'upper_bounds':[.5]*len(assets),'short_selling':False,'additional_index_cap':.5},
                   'comparison_caps':args.caps,'constraint_role':'Long-only baseline with 50% cap',
                   'justification':'Long-only controls gross exposure without unmodelled short financing. The 50% cap implements the chosen policy that no index receives more capital than all others combined. It is not a data-estimated optimal threshold.',
                   'asset_order':assets,'mean':full['mean'],'covariance':full['covariance'],
                   'annualisation':'Q1 arithmetic monthly mean x12, sample covariance x12, ddof=1; decimal units.',
                   'frontier_range':[full['cases']['Baseline: 50% cap']['gmv']['expected_return'],full['cases']['Baseline: 50% cap']['maximum_return']],
                   'q3_feasibility':output['q3_feasibility'],'fixed_target':None,'risk_free_rate':None,'risk_aversion_gamma':None}
    (tables/'Q2_baseline_config.json').write_text(json.dumps(configuration,indent=2))
    (tables/'Q2_results.json').write_text(json.dumps(output,indent=2))
    pd.DataFrame(records).to_csv(tables/'Q2_portfolios.csv',index=False,float_format='%.17g')
    pd.DataFrame(comparisons).to_csv(tables/'Q2_cap_comparison.csv',index=False,float_format='%.17g')
    pd.DataFrame(sensitivity).to_csv(tables/'Q2_parameter_sensitivity.csv',index=False,float_format='%.17g')
    make_figures(models,case_specs,figures)
    baseline_summary(models,assets,tables)
    write_report(output,args.output_dir)
    print(output['verification'])


if __name__=='__main__':
    main()

