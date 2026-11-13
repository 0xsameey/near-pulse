

from .metrics import changes
MIN_PAIRS=30

def correlate(x,y,lag=0):
    import pandas as pd
    from scipy.stats import spearmanr
    # Positive lag: x on day t compared with y on day t+lag.
    shifted=y.copy();shifted.index=shifted.index-pd.Timedelta(days=lag)
    paired=pd.concat([x.rename('x'),shifted.rename('y')],axis=1,sort=True).dropna()
    n=len(paired);result={'lag':lag,'n':n,'rho':None,'p':None,'start':None,'end':None}
    if n:result.update(start=paired.index.min().date().isoformat(),end=paired.index.max().date().isoformat())
    if n<MIN_PAIRS or paired.x.nunique()<2 or paired.y.nunique()<2:return result
    rho,p=spearmanr(paired.x,paired.y);return {**result,'rho':float(rho),'p':float(p)}

def comparisons(series):
    if 'volume' not in series: return []
    import pandas as pd
    transformed={key:changes(value) for key,value in series.items() if key in ('volume','signers','transactions','contracts','price')}
    required=('volume','signers','transactions','contracts','price')
    common=None
    if all(k in transformed for k in required):
        common=pd.concat([transformed[k].rename(k) for k in required],axis=1).dropna()
    results=[]
    for key in ('signers','transactions','contracts','price'):
        if key not in transformed: continue
        for lag in (0,7,30):
            # Same-day verdict comparisons share exactly the same valid dates.
            x,y=(common['volume'],common[key]) if lag==0 and common is not None else (transformed['volume'],transformed[key])
            results.append({'pair':f'volume \u2192 {key}',**correlate(x,y,lag)})
    return results
