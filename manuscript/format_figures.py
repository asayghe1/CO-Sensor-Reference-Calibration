"""Presentation only: plot existing summary cells without recomputing metrics.

Optional; the LaTeX build uses the included static PDF figures.
Run with an installed Matplotlib; no raw inputs, model or replay code is used.
"""
from pathlib import Path
import csv, json, hashlib, os, re, datetime
P=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(P/'.figure_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

files=['AGGREGATE_METRICS.csv','SESSION_METRICS.csv',
       'CONDITIONAL_RESAMPLING_EFFECTS.csv','C5_PRIMARY_TABLE.csv',
       'C5_PRIMARY_SESSION_TABLE.csv']
rows={f:list(csv.DictReader((P/f).open(newline=''))) for f in files}
identity=dict(re.findall(r'\\newcommand\{\\(\w+)\}\{([^{}]*)\}',(P/'author_identity.tex').read_text()))
audit=[]
def value(file,field,**keys):
    found=[r for r in rows[file] if all(r[k]==str(v) for k,v in keys.items())]
    assert len(found)==1,(file,keys,len(found))
    v=found[0][field]
    audit.append(dict(file=file,keys=keys,field=field,stored_value=v))
    return float(v)
base=dict(model='RF',bounds='primary',scope='ALL',subset='all',band='ALL')
def aggregate(est,scope):
    return value('AGGREGATE_METRICS.csv','mae',**(base|dict(estimator=est,scope=scope,schedule='none',budget=0)))
def session(est,scope,day):
    return value('SESSION_METRICS.csv','mae',**(base|dict(estimator=est,scope=scope,schedule='none',budget=0,session=day)))
def effect(est,sch,b,metric,field):
    return value('CONDITIONAL_RESAMPLING_EFFECTS.csv',field,model='RF',bounds='primary',scope='ALL',estimator=est,schedule=sch,budget=b,metric=metric,block_length=10,effect='incremental')
plt.rcParams.update({'font.size':10,'axes.titlesize':11,'axes.labelsize':10,
 'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,
 'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,
 'axes.axisbelow':True})
def save(fig,name):
    fig.savefig(P/(name+'.pdf'),metadata={'Title':name,'Author':identity['AuthorOne']+' [1,*]; '+identity['AuthorTwo']+' [2,3]; '+identity['AuthorThree']+' [2,3]','Subject':'Author-review figure. [1] '+identity['AffiliationOne']+' [2] '+identity['AffiliationTwo']+' [3] '+identity['AffiliationThree']+' Corresponding author: '+identity['AuthorOne']+', '+identity['CorrespondingEmail'],'CreationDate':datetime.datetime(2026,10,12,8,tzinfo=datetime.timezone.utc),'ModDate':datetime.datetime(2026,10,12,8,tzinfo=datetime.timezone.utc)})
    fig.savefig(P/(name+'.png'),dpi=200)
    plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(7.1,3.35))
for ax,scope,top in zip(axes,['Figaro','FIS'],[1.85,.42]):
    ax.bar([0,1],[aggregate(e,scope) for e in ['consensus','affine']],width=.54,color=['#aab8c2','#4b83aa'],edgecolor='#38444e',linewidth=.6)
    for day,mark in zip(['D6','D8','D10'],['o','s','^']):
        ax.plot([0,1],[session(e,scope,day) for e in ['consensus','affine']],linestyle='none',marker=mark,ms=7,mfc='white',mec='#9b3f17',mew=1.3,label=day,zorder=4)
    ax.set(xticks=[0,1],xticklabels=['Consensus','Affine B0'],title=scope,ylabel='MAE (ppm)',ylim=(0,top))
    ax.grid(axis='y',color='.88',lw=.5)
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,1.01),ncol=3,frameon=False)
fig.subplots_adjust(left=.095,right=.98,bottom=.13,top=.84,wspace=.37)
save(fig,'fig_1_historical_mae')

schedules=['periodic','random','confidence','envelope','rlsvar']
names=['Periodic','Random','Confidence','Envelope','Information']
colors=['#0072B2','#E69F00','#009E73','#D55E00','#8C549C']
styles=['-','--','-.',':',(0,(5,1,1,1))]
for metric,name,ylabel in [('mae','fig_2_affine_increment_mae','Incremental MAE (ppm)'),('p1.0','fig_3_affine_increment_exceedance','Incremental >1 ppm\n(percentage points)')]:
    fig,axes=plt.subplots(1,3,figsize=(7.2,4.15),sharey=True)
    for ax,est,title in zip(axes,['affine','affine_l095','affine_l090'],['λ = 1','λ = .95','λ = .90']):
        for sch,label,color,style in zip(schedules,names,colors,styles):
            ax.plot([0,5,10,20],[0]+[effect(est,sch,b,metric,'estimate') for b in [5,10,20]],color=color,ls=style,lw=1.35,marker='D',ms=3.7,mec='white',mew=.3,zorder=4)
            for day,mark in zip(['D6','D8','D10'],['o','s','^']):
                ax.plot([5,10,20],[effect(est,sch,b,metric,day) for b in [5,10,20]],ls='none',marker=mark,ms=5.7,mfc='none',mec=color,mew=1.05,zorder=3)
        ax.axhline(0,color='.2',lw=.8)
        ax.grid(axis='y',color='.9',lw=.5)
        ax.set(title=title,xticks=[0,5,10,20],xlim=(-1.7,21.7))
    axes[0].set_ylabel(ylabel)
    fig.supxlabel('Additional shared references per session',fontsize=10,y=.015)
    h=[Line2D([],[],color=c,ls=s,lw=1.6,label=n) for c,s,n in zip(colors,styles,names)]
    fig.legend(handles=h,loc='upper center',bbox_to_anchor=(.51,1.0),ncol=5,frameon=False,columnspacing=1,handlelength=2)
    h=[Line2D([],[],color='.25',marker=m,ls='none',ms=6,mfc='none' if m!='D' else '.25',label=n) for m,n in [('o','D6'),('s','D8'),('^','D10'),('D','Equal-session mean')]]
    fig.legend(handles=h,loc='upper center',bbox_to_anchor=(.51,.927),ncol=4,frameon=False,columnspacing=1.3)
    fig.subplots_adjust(left=.105,right=.985,bottom=.15,top=.76,wspace=.14)
    save(fig,name)

fig,axes=plt.subplots(1,3,figsize=(7.2,3.7),sharey=True)
for ax,scope,title in zip(axes,['ALL','Figaro','FIS'],['Pooled','Figaro','FIS']):
    for day,mark,color in zip([11,12,13],['o','s','^'],colors[:3]):
        yy=[value('C5_PRIMARY_SESSION_TABLE.csv',f,day=day,scope=scope) for f in ['consensus_mae','affine_B0_mae','affine_B20_mae']]
        ax.plot([0,1,2],yy,ls='--',color=color,marker=mark,ms=6.6,mec='white',mew=.7,lw=1.3,label=f'D{day}')
    yy=[value('C5_PRIMARY_TABLE.csv',f,scope=scope) for f in ['consensus_mae','affine_B0_mae','affine_envelope_B20_mae']]
    ax.plot([0,1,2],yy,color='black',lw=2,marker='D',ms=5.8,label='Equal-session mean')
    ax.set(xticks=[0,1,2],xticklabels=['Consensus','Affine\nB0','Affine\nB20'],title=title,ylim=(0,2.85),xlim=(-.18,2.18))
    ax.tick_params(axis='x',labelsize=8.8)
    ax.grid(axis='y',color='.88',lw=.5)
axes[0].set_ylabel('MAE (ppm)')
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.51,1.01),ncol=4,frameon=False,columnspacing=1.2)
fig.subplots_adjust(left=.09,right=.985,bottom=.19,top=.84,wspace=.15)
save(fig,'fig_4_c5_primary_mae')

(P/'FIGURE_VALUE_AUDIT.json').write_text(json.dumps({'scope':'Presentation only; each plotted nonzero data coordinate copied from an existing saved summary cell. Zero incremental B0 coordinates express the existing own-baseline identity. No metrics recomputed.','input_sha256':{f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in files},'plotted_cells':audit},indent=2)+'\n')
print('Formatted four figures using',len(audit),'unchanged saved cells.')
