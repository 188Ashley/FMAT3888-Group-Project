"""FMAT3888 Q4(a)-(c): normal utility benchmark, MC and historical bootstrap.
All returns/weights are decimal units; one-period horizon is one year.
Default output is generated/, preserving the submitted results/report.
"""
from pathlib import Path
import argparse, hashlib, json, platform, time
import numpy as np
import pandas as pd
from scipy.optimize import minimize, linprog
from scipy.special import logsumexp
from threadpoolctl import threadpool_limits

GAMMAS = (1., 5., 10., 25., 100.)
FEASIBILITY_TOL = 1e-8
GAP_TOL = 1e-7

def constraint_error(w):
    return max(abs(w.sum()-1), float(np.maximum(-w, 0).max()), float(np.maximum(w-.5,0).max()))

def linear_gap(w, gradient):
    # Linear minimisation over the capped simplex. Greedy exact solution:
    # allocate 0.5 each to the two lowest gradient entries.
    order=np.argsort(gradient); v=np.zeros(len(w)); v[order[:2]]=.5
    return max(0.,float(gradient@(w-v)))

def validate(w, gradient):
    primal=constraint_error(w); gap=linear_gap(w,gradient)
    if primal>FEASIBILITY_TOL or gap>GAP_TOL:
        raise RuntimeError(f'Invalid optimum: primal={primal}, convex optimality gap={gap}')
    return primal,gap

def solve_mv(mean,cov,gamma,initial=None):
    n=len(mean);start=time.perf_counter()
    q=minimize(lambda w:100*(gamma/2*w@cov@w-mean@w),
               np.full(n,1/n) if initial is None else initial,
               jac=lambda w:100*(gamma*cov@w-mean),method='SLSQP',
               bounds=[(0,.5)]*n,constraints={'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(n)},
               options={'ftol':1e-12,'maxiter':2000})
    if not q.success:raise RuntimeError(q.message)
    w=q.x
    # Refine the active-set solution of this strictly convex quadratic problem.
    active=(w<1e-7)|(w>.5-1e-7);free=~active
    if free.any():
        wa=np.where(w[active]>.25,.5,0.)
        cf=cov[np.ix_(free,free)]
        matrix=np.block([[gamma*cf,np.ones((free.sum(),1))],[np.ones((1,free.sum())),np.zeros((1,1))]])
        rhs=np.r_[mean[free]-gamma*cov[np.ix_(free,active)]@wa,1-wa.sum()]
        candidate=w.copy();candidate[active]=wa;candidate[free]=np.linalg.solve(matrix,rhs)[:-1]
        if constraint_error(candidate)<FEASIBILITY_TOL and linear_gap(candidate,gamma*cov@candidate-mean)<GAP_TOL:w=candidate
    primal,gap=validate(w,gamma*cov@w-mean)
    elapsed=time.perf_counter()-start
    return w,elapsed,primal,gap

def portfolio(w,mean,cov,gamma):
    mu=float(mean@w);var=float(w@cov@w);ce=mu-gamma/2*var
    return {'expected_return':mu,'volatility':float(np.sqrt(var)), 'variance':var,
            'certainty_equivalent_return':ce,'certainty_equivalent_wealth':1+ce,
            'normal_expected_utility':float(-np.exp(-gamma*(1+ce)))}

def solve_mc(samples,gamma,initial):
    n=samples.shape[1];start=time.perf_counter()
    def fun(w):
        z=-gamma*(samples@w);normaliser=logsumexp(z)
        tilted=np.exp(z-normaliser)
        value=(normaliser-np.log(len(samples)))/gamma
        gradient=-(samples.T@tilted)
        return 100*value,100*gradient
    q=minimize(fun,initial,jac=True,method='SLSQP',bounds=[(0,.5)]*n,
               constraints={'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(n)},
               options={'ftol':1e-11,'maxiter':2000})
    if not q.success:raise RuntimeError(q.message)
    value,gradient=fun(q.x);primal,gap=validate(q.x,gradient/100)
    elapsed=time.perf_counter()-start
    return q.x,elapsed,primal,gap,-value/100,q.nfev

def load_inputs(directory):
    config=json.loads((directory/'Q2_baseline_config.json').read_text())
    assets=config['asset_order'];returns=pd.read_csv(directory/'Q1_clean_monthly_returns.csv',index_col=0,parse_dates=True,float_precision='round_trip')
    if list(returns.columns)!=assets or returns.shape!=(248,9) or returns.isna().any().any():raise ValueError('Unexpected Q1 return matrix')
    if returns.index[0]!=pd.Timestamp('2006-01-31') or returns.index[-1]!=pd.Timestamp('2026-08-31'):raise ValueError('Unexpected sample period')
    m=12*returns.mean().to_numpy();C=12*returns.cov(ddof=1).to_numpy()
    errors={'mean_max_abs_error':float(np.max(abs(m-np.array(config['mean'])))),
            'covariance_max_abs_error':float(np.max(abs(C-np.array(config['covariance'])))),
            'minimum_eigenvalue':float(np.linalg.eigvalsh(C).min()),'symmetry_error':float(abs(C-C.T).max())}
    bounds=config['recommended_constraints']
    if errors['mean_max_abs_error']>1e-12 or errors['covariance_max_abs_error']>1e-12 or errors['minimum_eigenvalue']<=0:raise ValueError('Q1/Q2 moment reconciliation failed')
    if bounds['lower_bounds']!=[0]*9 or bounds['upper_bounds']!=[.5]*9 or bounds['short_selling'] or bounds['sum_weights']!=1:raise ValueError('Q2 baseline changed')
    # Independently reconcile the current Q1 workbook, rather than relying on the bundled config alone.
    p=pd.read_excel(directory/'Q1_results.xlsx',sheet_name='Q1c_Annualised_Parameters',header=3,index_col=0)
    c=pd.read_excel(directory/'Q1_results.xlsx',sheet_name='Q1c_Covariance',header=3,index_col=0)
    if np.max(abs(p.loc[assets,'Annualised_Expected_Return'].to_numpy()-m))>1e-12 or np.max(abs(c.loc[assets,assets].to_numpy()-C))>1e-12:raise ValueError('Current Q1 workbook mismatch')
    return assets,returns,m,C,errors

def main():
    here=Path(__file__).resolve().parent;parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir',type=Path,default=here/'inputs')
    parser.add_argument('--output-dir',type=Path,default=here/'generated')
    parser.add_argument('--gammas',nargs='+',type=float,default=list(GAMMAS))
    parser.add_argument('--mc-sizes',nargs='+',type=int,default=[1000,10000,100000])
    parser.add_argument('--mc-repetitions',type=int,default=8)
    parser.add_argument('--bootstrap-repetitions',type=int,default=10000)
    parser.add_argument('--block-bootstrap-repetitions',type=int,default=1000)
    parser.add_argument('--block-lengths',nargs='+',type=int,default=[6,12,24])
    parser.add_argument('--seed',type=int,default=388804)
    args=parser.parse_args()
    if any(g<=0 for g in args.gammas) or any(n<2 or n%2 for n in args.mc_sizes) or args.mc_repetitions<2 or args.bootstrap_repetitions<100:raise ValueError('Invalid experiment settings')
    out=args.output_dir;results=out/'results';results.mkdir(parents=True,exist_ok=True)
    assets,returns,m,C,checks=load_inputs(args.input_dir);n=len(assets)
    rows=[];references={};gaps=[];primals=[]
    rngtree=np.random.SeedSequence(args.seed);simulation_seed,bootstrap_seed,block_seed=rngtree.spawn(3)
    with threadpool_limits(limits=1):
        # Small convex benchmark; repeated timings separate solve cost from input loading.
        for gamma in args.gammas:
            w,t,p,g=solve_mv(m,C,gamma);references[gamma]=w;primals.append(p);gaps.append(g)
            timings=[]
            for _ in range(30):timings.append(solve_mv(m,C,gamma)[1])
            rows.append({'gamma':gamma,**portfolio(w,m,C,gamma),'median_solver_seconds':float(np.median(timings)),**dict(zip(assets,w))})
        mv=pd.DataFrame(rows);mv.to_csv(results/'Q4a_benchmark.csv',index=False,float_format='%.17g')
        print('Q4(a) benchmark:',mv[['gamma','expected_return','volatility']].to_dict('records'),flush=True)
        chol=np.linalg.cholesky(C);mc=[]
        replicate_seeds=simulation_seed.spawn(args.mc_repetitions)
        for rep,ss in enumerate(replicate_seeds):
            children=ss.spawn(2*len(args.mc_sizes));k=0
            for size in args.mc_sizes:
                for method in ['Standard MC','Antithetic MC']:
                    rng=np.random.default_rng(children[k]);k+=1;start=time.perf_counter()
                    if method=='Standard MC':samples=m+rng.standard_normal((size,n))@chol.T
                    else:
                        shocks=rng.standard_normal((size//2,n))@chol.T
                        samples=np.concatenate([m+shocks,m-shocks])
                    generation=time.perf_counter()-start
                    for gamma in args.gammas:
                        # Uniform start: the numerical solver is not seeded with the exact answer.
                        w,t,p,g,ce,nfev=solve_mc(samples,gamma,np.full(n,1/n));primals.append(p);gaps.append(g)
                        true=portfolio(w,m,C,gamma);ref=portfolio(references[gamma],m,C,gamma)
                        regret=ref['certainty_equivalent_return']-true['certainty_equivalent_return']
                        if regret < -1e-9:raise RuntimeError('MC exceeds exact normal optimum')
                        ce_ref_sample=-float(logsumexp(-gamma*(samples@references[gamma]))-np.log(size))/gamma
                        mc.append({'method':method,'N':size,'replicate':rep,'gamma':gamma,
                            'half_L1_weight_error':float(.5*abs(w-references[gamma]).sum()),
                            'max_weight_error':float(abs(w-references[gamma]).max()),
                            'true_CE_regret':max(0,regret),'sample_CE_return':ce,
                            'CE_estimation_error_at_benchmark':ce_ref_sample-ref['certainty_equivalent_return'],
                            'relative_EU_error_at_benchmark':float(abs(np.expm1(gamma*(ref['certainty_equivalent_return']-ce_ref_sample)))),
                            'solver_seconds':t,'shared_generation_seconds':generation,
                            'amortised_total_seconds':t+generation/len(args.gammas),'evaluations':nfev,
                            **true,**dict(zip(assets,w))})
                    if rep==0:np.savez_compressed(results/f'Q4b_{method.replace(" ","_").lower()}_N{size}_rep0_samples.npz',asset_returns=samples)
            print(f'Q4(b): completed independent replication {rep+1}/{args.mc_repetitions}',flush=True)
        mc=pd.DataFrame(mc);mc.to_csv(results/'Q4b_MC_runs.csv',index=False,float_format='%.17g')
        summary=mc.groupby(['method','N','gamma']).agg(
            mean_half_L1_weight_error=('half_L1_weight_error','mean'),
            p95_half_L1_weight_error=('half_L1_weight_error',lambda x:np.quantile(x,.95)),
            mean_true_CE_regret=('true_CE_regret','mean'),max_true_CE_regret=('true_CE_regret','max'),
            rmse_CE_estimation_at_benchmark=('CE_estimation_error_at_benchmark',lambda x:np.sqrt(np.mean(x*x))),
            mean_relative_EU_error_at_benchmark=('relative_EU_error_at_benchmark','mean'),
            median_solver_seconds=('solver_seconds','median'),median_amortised_total_seconds=('amortised_total_seconds','median')).reset_index()
        summary.to_csv(results/'Q4b_MC_summary.csv',index=False,float_format='%.17g')
        rng=np.random.default_rng(bootstrap_seed);B=args.bootstrap_repetitions;data=returns.to_numpy()
        indices=rng.integers(0,len(data),size=(B,len(data)));weights=np.empty((B,len(args.gammas),n));means=np.empty((B,n));covs=np.empty((B,n,n));bootrows=[]
        for b in range(B):
            sample=data[indices[b]];mb=12*sample.mean(0);cb=12*np.cov(sample,rowvar=False,ddof=1);means[b]=mb;covs[b]=cb
            if np.linalg.eigvalsh(cb).min()<=0:raise RuntimeError('Bootstrap covariance is not positive definite')
            for j,gamma in enumerate(args.gammas):
                w,t,p,g=solve_mv(mb,cb,gamma,references[gamma]);primals.append(p);gaps.append(g);weights[b,j]=w
                true=portfolio(w,m,C,gamma);ref=portfolio(references[gamma],m,C,gamma)
                bootrows.append({'replicate':b,'gamma':gamma,'half_L1_from_baseline':float(.5*abs(w-references[gamma]).sum()),
                    'reference_model_CE_regret':max(0,ref['certainty_equivalent_return']-true['certainty_equivalent_return']),
                    'resampled_expected_return':float(mb@w),'resampled_volatility':float(np.sqrt(w@cb@w)),
                    **dict(zip(assets,w))})
            if (b+1)%250==0:print(f'Q4(c): bootstrap {b+1}/{B}',flush=True)
        np.savez_compressed(results/'Q4c_bootstrap_distributions.npz',weights=weights,means=means,covariances=covs,indices=indices,gammas=args.gammas,assets=assets)
        boot=pd.DataFrame(bootrows);boot.to_csv(results/'Q4c_bootstrap_runs.csv',index=False,float_format='%.17g')
        allocation=[];stability=[];convergence=[]
        for j,gamma in enumerate(args.gammas):
            w=weights[:,j,:];qlo,qhi=np.quantile(w,[.025,.975],axis=0);marginal_sd=w.std(0,ddof=1)
            for i,a in enumerate(assets):allocation.append({'gamma':gamma,'Asset':a,'baseline_weight':references[gamma][i],
                'bootstrap_mean':float(w[:,i].mean()),'bootstrap_sd':float(marginal_sd[i]),'p2_5':float(qlo[i]),'p97_5':float(qhi[i]),
                'probability_zero':float((w[:,i]<1e-7).mean()),'probability_cap':float((w[:,i]>.5-1e-7).mean())})
            dist=.5*abs(w-references[gamma]).sum(1);regrets=boot.loc[boot.gamma==gamma,'reference_model_CE_regret'].to_numpy()
            stability.append({'gamma':gamma,'median_half_L1':float(np.median(dist)),'p95_half_L1':float(np.quantile(dist,.95)),
                'median_reference_CE_regret':float(np.median(regrets)),'p95_reference_CE_regret':float(np.quantile(regrets,.95)),
                'max_marginal_sd':float(marginal_sd.max()),'maximum_interval_width':float((qhi-qlo).max())})
            first=w[:B//2];convergence.append({'gamma':gamma,'B_first':B//2,'B_full':B,
                'max_mean_weight_difference':float(abs(first.mean(0)-w.mean(0)).max()),
                'max_percentile_endpoint_difference':float(abs(np.quantile(first,[.025,.975],axis=0)-np.quantile(w,[.025,.975],axis=0)).max())})
        pd.DataFrame(allocation).to_csv(results/'Q4c_allocation_uncertainty.csv',index=False,float_format='%.17g')
        pd.DataFrame(stability).to_csv(results/'Q4c_stability_summary.csv',index=False,float_format='%.17g')
        pd.DataFrame(convergence).to_csv(results/'Q4c_replication_convergence.csv',index=False,float_format='%.17g')
        # Moving paired blocks preserve within-block time dependence. This is a
        # sensitivity check, keeping Q1's annualisation and the normal objective unchanged.
        blockrows=[];blockalloc=[];blockstability=[]
        for length,seed in zip(args.block_lengths,block_seed.spawn(len(args.block_lengths))):
            if not 1<=length<=len(data):raise ValueError('Invalid block length')
            rg=np.random.default_rng(seed);blockweights=np.empty((args.block_bootstrap_repetitions,len(args.gammas),n))
            starts=rg.integers(0,len(data)-length+1,size=(args.block_bootstrap_repetitions,int(np.ceil(len(data)/length))))
            for b,begin in enumerate(starts):
                chosen=(begin[:,None]+np.arange(length)).ravel()[:len(data)];sample=data[chosen]
                mb=12*sample.mean(0);cb=12*np.cov(sample,rowvar=False,ddof=1)
                for j,gamma in enumerate(args.gammas):
                    w,t,p,g=solve_mv(mb,cb,gamma,references[gamma]);primals.append(p);gaps.append(g);blockweights[b,j]=w
                    blockrows.append({'block_length':length,'replicate':b,'gamma':gamma,
                        'half_L1_from_baseline':float(.5*abs(w-references[gamma]).sum()),**dict(zip(assets,w))})
            np.savez_compressed(results/f'Q4c_block_L{length}_distributions.npz',weights=blockweights,starts=starts,gammas=args.gammas,assets=assets)
            for j,gamma in enumerate(args.gammas):
                wb=blockweights[:,j];lo,hi=np.quantile(wb,[.025,.975],axis=0);dist=.5*abs(wb-references[gamma]).sum(1)
                blockstability.append({'block_length':length,'gamma':gamma,'median_half_L1':float(np.median(dist)),
                    'p95_half_L1':float(np.quantile(dist,.95)),'max_marginal_sd':float(wb.std(0,ddof=1).max()),
                    'BAUBIL_mean_weight':float(wb[:,-1].mean()),'BAUBIL_p2_5':float(lo[-1]),'BAUBIL_p97_5':float(hi[-1])})
                for i,a in enumerate(assets):blockalloc.append({'block_length':length,'gamma':gamma,'Asset':a,
                    'bootstrap_mean':float(wb[:,i].mean()),'bootstrap_sd':float(wb[:,i].std(ddof=1)),
                    'p2_5':float(lo[i]),'p97_5':float(hi[i])})
            print(f'Q4(c): moving-block check L={length}, B={args.block_bootstrap_repetitions}',flush=True)
        pd.DataFrame(blockrows).to_csv(results/'Q4c_block_bootstrap_runs.csv',index=False,float_format='%.17g')
        pd.DataFrame(blockalloc).to_csv(results/'Q4c_block_allocation_uncertainty.csv',index=False,float_format='%.17g')
        pd.DataFrame(blockstability).to_csv(results/'Q4c_block_stability_summary.csv',index=False,float_format='%.17g')

        # Gamma grid is an illustrative sensitivity design, not estimated preferences.
        sweep=[]
        for gamma in [0.01,.1,1,5,10,25,50,100,250]:
            w,*_=solve_mv(m,C,gamma);sweep.append({'gamma':gamma,**portfolio(w,m,C,gamma),**dict(zip(assets,w))})
        pd.DataFrame(sweep).to_csv(results/'Q4a_gamma_design_sweep.csv',index=False,float_format='%.17g')
        # Limiting portfolios and comparative-statics checks.
        gmv,*_=solve_mv(np.zeros(n),C,1.)
        maxreturn=linprog(-m,A_eq=np.ones((1,n)),b_eq=[1],bounds=[(0,.5)]*n,method='highs')
        ordered=mv.sort_values('gamma')
        if np.max(np.diff(ordered.volatility))>1e-8 or np.max(np.diff(ordered.expected_return))>1e-8:raise RuntimeError('Risk-aversion monotonicity failure')
        plan={'assets':assets,'m':m.tolist(),'C':C.tolist(),'horizon':'One-year normal arithmetic return model; not compounded annual return',
            'constraints':{'sum_weights':1,'lower_bounds':[0]*n,'upper_bounds':[.5]*n,'short_selling':False,'growth_target':None},
            'gammas':args.gammas,'mc_sizes':args.mc_sizes,'mc_independent_repetitions':args.mc_repetitions,'bootstrap_repetitions':B,
            'bootstrap_scheme':'IID paired monthly rows, resample 248 rows with replacement; reestimate annual moments; solve Q4(a)',
            'block_bootstrap':{'scheme':'Moving joint monthly blocks, uniform valid starts, concatenate and truncate to 248 rows','lengths':args.block_lengths,'replications_per_length':args.block_bootstrap_repetitions},
            'seed':args.seed,'seed_sequence_entropy':rngtree.entropy,'seed_spawn_keys':{'MC':list(simulation_seed.spawn_key),'bootstrap':list(bootstrap_seed.spawn_key),'block_bootstrap':list(block_seed.spawn_key)},
            'timing':'Single BLAS thread; benchmark median of 30 solves; MC solver plus per-gamma share of draw-generation time; excludes input/output',
            'input_checks':checks,'lag1_autocorrelations':{a:float(returns[a].autocorr(1)) for a in assets},
            'gmv':{'weights':gmv.tolist(),'mean':float(m@gmv),'volatility':float(np.sqrt(gmv@C@gmv))},
            'maximum_return_portfolio':{'weights':maxreturn.x.tolist(),'mean':float(m@maxreturn.x),'volatility':float(np.sqrt(maxreturn.x@C@maxreturn.x))},
            'validation':{'maximum_primal_error':float(max(primals)),'maximum_convex_optimality_gap':float(max(gaps)),
                          'gap_tolerance':GAP_TOL,'checked_solutions':len(primals),'risk_return_monotonicity':True},
            'runtime':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},
            'input_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in args.input_dir.iterdir() if f.is_file()}}
        (results/'Q4_config_and_validation.json').write_text(json.dumps(plan,indent=2)+'\n')
    print('Q4 complete:',plan['validation'],flush=True)

if __name__=='__main__':main()
