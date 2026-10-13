"""Independent checks of saved Q4 results, utility transformations and MC gradients."""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
from scipy.special import logsumexp

def main():
    h=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=h);a=p.parse_args();r=a.output_dir/'results'
    cfg=json.loads((r/'Q4_config_and_validation.json').read_text());assets=cfg['assets'];m=np.array(cfg['m']);C=np.array(cfg['C']);mv=pd.read_csv(r/'Q4a_benchmark.csv',float_precision='round_trip');errors={}
    meanerr=volerr=euerr=0.
    for _,row in mv.iterrows():
        w=row[assets].to_numpy(float);g=row.gamma;mu=m@w;v=w@C@w;ce=mu-g*v/2
        meanerr=max(meanerr,abs(mu-row.expected_return));volerr=max(volerr,abs(np.sqrt(v)-row.volatility))
        eu=-np.exp(-g*(1+mu)+g*g*v/2);euerr=max(euerr,abs(eu-row.normal_expected_utility)/max(abs(eu),1e-300))
    errors.update(benchmark_mean_error=meanerr,benchmark_volatility_error=volerr,normal_utility_identity_relative_error=euerr)
    samples=np.load(r/'Q4b_standard_mc_N1000_rep0_samples.npz')['asset_returns'];w=np.full(9,1/9);g=10
    def objective(x):return (logsumexp(-g*(samples@x))-np.log(len(samples)))/g
    z=-g*(samples@w);tilted=np.exp(z-logsumexp(z));analytic=-(samples.T@tilted)
    numeric=np.zeros(9);eps=1e-6
    for i in range(9):
        delta=np.zeros(9);delta[i]=eps;numeric[i]=(objective(w+delta)-objective(w-delta))/(2*eps)
    errors['MC_gradient_finite_difference_error']=float(abs(analytic-numeric).max())
    raw_eu=-np.mean(np.exp(-g*(1+samples@w)))
    transformed=-np.exp(-g*(1-objective(w)))
    errors['sampled_utility_transform_relative_error']=float(abs(raw_eu-transformed)/abs(raw_eu))
    original=pd.read_csv(h/'inputs/Q1_clean_monthly_returns.csv',index_col=0,float_precision='round_trip').to_numpy();boot=np.load(r/'Q4c_bootstrap_distributions.npz')
    bm=bc=0.
    for j in np.linspace(0,len(boot['indices'])-1,20,dtype=int):
        x=original[boot['indices'][j]];bm=max(bm,float(abs(12*x.mean(0)-boot['means'][j]).max()));bc=max(bc,float(abs(12*np.cov(x,rowvar=False,ddof=1)-boot['covariances'][j]).max()))
    errors['bootstrap_mean_reconstruction_error']=bm;errors['bootstrap_covariance_reconstruction_error']=bc
    allweights=boot['weights'];errors['saved_bootstrap_constraint_error']=float(max(abs(allweights.sum(2)-1).max(),np.maximum(-allweights,0).max(),np.maximum(allweights-.5,0).max()))
    for filename in ['Q4b_MC_runs.csv','Q4c_bootstrap_runs.csv','Q4c_block_bootstrap_runs.csv']:
        d=pd.read_csv(r/filename,float_precision='round_trip');x=d[assets].to_numpy();assert abs(x.sum(1)-1).max()<1e-8 and x.min()>-1e-8 and x.max()<.5+1e-8
    assert meanerr<1e-12 and volerr<1e-12 and euerr<1e-10
    assert errors['MC_gradient_finite_difference_error']<1e-8 and errors['sampled_utility_transform_relative_error']<1e-10
    assert bm<1e-12 and bc<1e-12 and errors['saved_bootstrap_constraint_error']<1e-8
    output={'status':'passed','checks':errors,'bootstrap_reconstruction_samples':20,'saved_rows_constraints_checked':True}
    (r/'Q4_independent_checks.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
