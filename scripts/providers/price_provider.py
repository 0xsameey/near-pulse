import os, math
from datetime import timedelta,datetime,timezone
from .common import HttpClient,SourceError,bounds

class PriceProvider:
    def __init__(self,client=None): self.client=client
    def fetch(self,start,end):
        key=os.getenv('COINGECKO_API_KEY'); tier=os.getenv('COINGECKO_TIER','demo')
        if not key: raise SourceError('COINGECKO_API_KEY absent; historical prices unavailable')
        if tier not in ('demo','pro'): raise SourceError('COINGECKO_TIER must be demo or pro')
        if os.getenv('COINGECKO_REDISTRIBUTION_CONFIRMED')!='true': raise SourceError('Confirm historical-feed redistribution rights before exporting public prices')
        return self._fetch_private(start,end)

    def probe(self,start,end):
        """Private in-memory validation only. Never return prices or write exports."""
        a,b=bounds(start,end)
        if (b-a)>timedelta(days=14):raise SourceError('Private probe limited to 14 days')
        rows=self._fetch_private(start,end)
        days=sorted({r['timestamp'][:10] for r in rows})
        expected=[];cursor=a
        while cursor<b:
            expected.append(cursor.date().isoformat());cursor+=timedelta(days=1)
        return {'authenticated_historical_request':True,'sample_count':len(rows),
                'observed_utc_dates':days,'missing_utc_dates':sorted(set(expected)-set(days)),
                'complete_daily_coverage':set(expected)<=set(days),
                'published':False,'prices_persisted':False,
                'rights_status':'Not assessed by authentication probe'}

    def _fetch_private(self,start,end):
        key=os.getenv('COINGECKO_API_KEY','').strip();tier=os.getenv('COINGECKO_TIER','demo')
        if not key:raise SourceError('COINGECKO_API_KEY absent; historical prices unavailable')
        if tier not in ('demo','pro'):raise SourceError('COINGECKO_TIER must be demo or pro')
        if self.client is None:self.client=HttpClient(interval=max(2,float(os.getenv('COINGECKO_INTERVAL_SECONDS','6'))))
        a,b=bounds(start,end); cursor=a; points={}
        host='pro-api' if tier=='pro' else 'api'
        while cursor<b:
            stop=min(cursor+timedelta(days=90),b)
            data=self.client.get(f'https://{host}.coingecko.com/api/v3/coins/near/market_chart/range',{'vs_currency':'usd','from':int(cursor.timestamp()),'to':int(stop.timestamp()),'precision':'full'},{f'x-cg-{tier}-api-key':key})
            if not isinstance(data,dict) or not isinstance(data.get('prices'),list) or not data['prices']: raise SourceError('Missing historical prices / insufficient plan entitlement')
            for point in data['prices']:
                if not isinstance(point,list) or len(point)!=2 or any(isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) for x in point) or point[1]<=0: raise SourceError('Invalid price point')
                t=datetime.fromtimestamp(point[0]/1000,timezone.utc)
                if not cursor<=t<=stop: raise SourceError('Price sample outside requested batch bounds')
                if a<=t<b:
                    if point[0] in points and points[point[0]]!=point[1]: raise SourceError('Conflicting price samples')
                    points[point[0]]=point[1]
            cursor=stop
        return [{'timestamp':datetime.fromtimestamp(t/1000,timezone.utc).isoformat(),'price':v} for t,v in sorted(points.items())]
