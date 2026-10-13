"""Generate Q4 report figures from saved full-precision results; no recalculation."""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
def save(fig,folder,name):
    fig.savefig(folder/(name+'.pdf'),bbox_inches='tight');fig.savefig(folder/(name+'.png'),dpi=200,bbox_inches='tight');plt.close(fig)
def main():
    here=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=here);args=p.parse_args()
    r=args.output_dir/'results';f=args.output_dir/'figures';f.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((r/'Q4_config_and_validation.json').read_text());mv=pd.read_csv(r/'Q4a_benchmark.csv');assets=cfg['assets']
    fig,ax=plt.subplots(1,2,figsize=(10,3.5))
    # Reconstruct utility choices on the mean-variance risk/return plot.
    ax[0].plot(mv.volatility*100,mv.expected_return*100,'o-',color='#22577a')
    for _,v in mv.iterrows():ax[0].annotate(f"γ={v.gamma:g}",(100*v.volatility,100*v.expected_return),xytext=(3,6),textcoords='offset points')
    ax[0].set(xlabel='Annualised volatility (%)',ylabel='Annualised expected return (%)',title='Risk aversion reduces fitted risk and return');ax[0].grid(alpha=.2)
    matrix=mv[assets].to_numpy().T*100
    im=ax[1].imshow(matrix,aspect='auto',vmin=0,vmax=50,cmap='Blues')
    ax[1].set_xticks(range(len(mv)),[f'{g:g}' for g in mv.gamma]);ax[1].set_yticks(range(len(assets)),[a.replace(' Index','') for a in assets]);ax[1].set(xlabel='Risk aversion γ',title='Optimal capital allocations (%)')
    for i in range(len(assets)):
        for j in range(len(mv)):ax[1].text(j,i,f'{matrix[i,j]:.1f}',ha='center',va='center',color='white' if matrix[i,j]>30 else 'black',fontsize=7)
    fig.tight_layout();save(fig,f,'Q4a_risk_aversion')
    mc=pd.read_csv(r/'Q4b_MC_runs.csv');fig,ax=plt.subplots(1,2,figsize=(9,3.3))
    for method,color in [('Standard MC','#22577a'),('Antithetic MC','#d17b0f')]:
        sub=mc[mc.method==method];s=sub.groupby('N').agg(error=('half_L1_weight_error','mean'),regret=('true_CE_regret','mean'),timing=('amortised_total_seconds','median'))
        ax[0].loglog(s.index,s.error*100,'o-',label=method,color=color)
        ax[1].loglog(s.index,s.timing*1000,'o-',label=method,color=color)
    ax[0].set(xlabel='Simulated return vectors N',ylabel='Mean allocation distance (%)',title='Error relative to exact normal optimum')
    ax[1].set(xlabel='Simulated return vectors N',ylabel='Median amortised runtime (ms)',title='Generation plus optimisation')
    for a in ax:a.grid(alpha=.2);a.legend(fontsize=8)
    fig.tight_layout();save(fig,f,'Q4b_accuracy_runtime')
    a=pd.read_csv(r/'Q4c_allocation_uncertainty.csv');b=a[a.gamma==10];fig,ax=plt.subplots(1,2,figsize=(10,2.7))
    y=np.arange(len(assets));ax[0].hlines(y,b.p2_5*100,b.p97_5*100,color='#22577a',linewidth=3)
    ax[0].scatter(b.baseline_weight*100,y,c='#d17b0f',s=23,label='Fitted optimal weight',zorder=3)
    ax[0].set_yticks(y,[s.replace(' Index','') for s in assets]);ax[0].invert_yaxis();ax[0].set(xlabel='Capital weight (%)',title='γ=10: IID bootstrap 2.5%-97.5% range');ax[0].legend(fontsize=7);ax[0].grid(axis='x',alpha=.2)
    sd=a.pivot(index='Asset',columns='gamma',values='bootstrap_sd').reindex(assets)*100
    im=ax[1].imshow(sd.to_numpy(),aspect='auto',cmap='Oranges');ax[1].set_xticks(range(len(sd.columns)),[f'{g:g}' for g in sd.columns]);ax[1].set_yticks(range(len(assets)),[s.replace(' Index','') for s in assets]);ax[1].set(xlabel='Risk aversion γ',title='IID bootstrap weight SD (percentage points)');fig.colorbar(im,ax=ax[1],fraction=.045)
    fig.tight_layout();save(fig,f,'Q4c_bootstrap_uncertainty')
    iid=pd.read_csv(r/'Q4c_stability_summary.csv');block=pd.read_csv(r/'Q4c_block_stability_summary.csv');fig,ax=plt.subplots(figsize=(6.6,3.2))
    x=np.arange(len(mv));width=.2;ax.bar(x-1.5*width,iid.median_half_L1*100,width,label='IID months')
    for k,L in enumerate(sorted(block.block_length.unique())):
        v=block[block.block_length==L].sort_values('gamma');ax.bar(x+(k-.5)*width,v.median_half_L1*100,width,label=f'{L}-month blocks')
    ax.set_xticks(x,[f'{g:g}' for g in mv.gamma]);ax.set(xlabel='Risk aversion γ',ylabel='Median allocation distance (%)',title='Sensitivity to historical resampling scheme');ax.legend(fontsize=8,ncol=2);ax.grid(axis='y',alpha=.2);fig.tight_layout();save(fig,f,'Q4c_block_sensitivity')
if __name__=='__main__':main()
