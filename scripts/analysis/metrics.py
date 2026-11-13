from decimal import Decimal,localcontext
from datetime import datetime,timezone

from scripts.providers.common import SourceError,timestamp

def add_decimal(left,right):
    """Add finite USD decimals without default-context rounding of long values."""
    precision=max(28,max(left.adjusted(),right.adjusted())-min(left.as_tuple().exponent,right.as_tuple().exponent)+2)
    if precision>10000:raise SourceError('USD decimal exceeds processing precision budget')
    with localcontext() as context:
        context.prec=precision
        return left+right

def daily_swaps(rows):
    grouped={}; seen={}
    for row in rows:
        key=(row['depositAddress'],row['depositMemo'])
        if key in seen:
            if row!=seen[key]: raise SourceError('Conflicting duplicate')
            continue
        seen[key]=row
        if row['status']!='SUCCESS': raise SourceError('Non-success swap in successful export')
        day=timestamp(row['createdAt']).date().isoformat(); amount=Decimal(str(row['amountInUsd']))
        if not amount.is_finite() or amount<0: raise SourceError('Invalid decimal amount')
        item=grouped.setdefault(day,{'date':day,'swaps':0,'volume':Decimal(0)})
        item['swaps']+=1;item['volume']=add_decimal(item['volume'],amount)
    return [{**x,'volume':str(x['volume'])} for _,x in sorted(grouped.items())]

def daily_prices(rows):
    # Last available sample in each UTC day, not a guaranteed exchange close.
    daily={}
    for row in sorted(rows,key=lambda r:timestamp(r['timestamp'])):
        day=timestamp(row['timestamp']).date().isoformat();daily[day]={'date':day,'price':row['price']}
    return list(daily.values())

def concentration(rows):
    """Verified origin-asset identity only; never infer a chain from a symbol."""
    totals={};seen=set()
    for row in rows:
        identity=(row['depositAddress'],row['depositMemo'])
        if identity in seen: continue
        seen.add(identity)
        asset=row['originAsset']
        if not isinstance(asset,str) or not asset: raise SourceError('Missing origin asset identity')
        amount=Decimal(str(row['amountInUsd']))
        if not amount.is_finite() or amount<0: raise SourceError('Invalid asset USD amount')
        totals[asset]=add_decimal(totals.get(asset,Decimal(0)),amount)
    total=Decimal(0)
    for value in totals.values():total=add_decimal(total,value)
    return [{'asset':asset,'volume':str(value),'share':str(value/total) if total else None}
            for asset,value in sorted(totals.items(),key=lambda p:p[1],reverse=True)]

def calendar_series(rows,key):
    import pandas as pd
    if not rows:return pd.Series(dtype=float)
    frame=pd.DataFrame(rows)
    if frame['date'].duplicated().any():raise SourceError('Duplicate daily observations')
    s=pd.Series(pd.to_numeric(frame[key],errors='raise').to_numpy(),index=pd.to_datetime(frame['date'],utc=True),dtype=float).sort_index()
    return s.reindex(pd.date_range(s.index.min(),s.index.max(),freq='D'))

def changes(s): return s.pct_change(fill_method=None).where(s.shift(1).ne(0)).replace([float('inf'),-float('inf')],float('nan'))
def moving(s,n): return s.rolling(n,min_periods=n).mean()
def indexed(s):
    if s.dropna().empty or s.dropna().iloc[0]==0:return s*float('nan')
    return s/s.dropna().iloc[0]*100

def freshness(latest,now=None,threshold=3):
    if not latest:return 'unavailable'
    age=((now or datetime.now(timezone.utc))-timestamp(latest+'T00:00:00Z')).total_seconds()/86400
    return 'stale' if age>threshold else 'current'
