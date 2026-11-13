import os
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from .common import HttpClient, SourceError, bounds, timestamp

class IntentsProvider:
    endpoint='https://explorer.near-intents.org/api/v0/transactions'
    def __init__(self,client=None):
        self.client=client
        self.audit={};self.pages=[]
    def fetch(self,start,end):
        token=(os.getenv('INTENTS_EXPLORER_JWT') or '').strip()
        if not token: raise SourceError('INTENTS_EXPLORER_JWT absent; authenticated 1Click ingestion unavailable')
        if self.client is None:self.client=HttpClient(interval=5,capture=True,parse_decimal=True)
        a,b=bounds(start,end); size=int(os.getenv('INTENTS_PAGE_SIZE','1000')); pages=int(os.getenv('INTENTS_MAX_PAGES','100'))
        if not 1<=size<=1000 or not 1<=pages<=1000: raise SourceError('Invalid pagination budget')
        self.pages=[];self.audit={'start':start,'end':end,'complete':False,'pages_received':0,'rows_received':0,'unique_swaps':0,'duplicate_records':0,'timestamp_basis':'createdAt UTC; SUCCESS status at retrieval, not completion day','identity':'depositAddress + depositMemo'}
        params={'statuses':'SUCCESS','numberOfTransactions':size,'direction':'next','startTimestamp':(a-timedelta(milliseconds=1)).isoformat(),'endTimestamp':end}
        rows={}; cursors=set()
        for page in range(pages):
            data=self.client.get(self.endpoint,params.copy(),{'Authorization':f'Bearer {token}'})
            if not isinstance(data,list) or len(data)>size: raise SourceError('Unexpected Explorer response schema')
            self.pages.append({'parameters':params.copy(),'rows':data})
            self.audit['pages_received']+=1;self.audit['rows_received']+=len(data)
            if not data:
                self.audit.update(complete=True,terminal_empty_page=True)
                return list(rows.values())
            for row in data:
                if not isinstance(row,dict) or not all(k in row for k in ['depositAddress','depositMemo','createdAt','status','amountInUsd','originAsset']): raise SourceError('Missing swap fields')
                if not isinstance(row['depositAddress'],str) or not row['depositAddress'] or (row['depositMemo'] is not None and not isinstance(row['depositMemo'],str)): raise SourceError('Invalid swap identity')
                if not isinstance(row['originAsset'],str) or not row['originAsset']:raise SourceError('Invalid origin asset identity')
                if row['status']!='SUCCESS' or not a<=timestamp(row['createdAt'])<b: raise SourceError('Record outside requested creation-time bounds/status')
                if 'createdAtTimestamp' in row:
                    epoch=row['createdAtTimestamp']
                    if isinstance(epoch,bool) or not isinstance(epoch,(int,float,Decimal)) or not Decimal(str(epoch)).is_finite() or abs(Decimal(str(timestamp(row['createdAt']).timestamp()))-Decimal(str(epoch)))>=1:
                        raise SourceError('Inconsistent createdAt / createdAtTimestamp fields')
                try: amount=Decimal(str(row['amountInUsd']))
                except InvalidOperation: raise SourceError('Invalid USD amount') from None
                if not amount.is_finite() or amount<0: raise SourceError('Invalid USD amount')
                key=(row['depositAddress'],row['depositMemo'])
                if key in rows and rows[key]!=row: raise SourceError('Conflicting duplicate swap identity')
                if key in rows:self.audit['duplicate_records']+=1
                rows[key]=row
                self.audit['unique_swaps']=len(rows)
            last=data[-1]; cursor=(last['depositAddress'],last['depositMemo'])
            if cursor in cursors: raise SourceError('Repeated cursor; pagination incomplete')
            cursors.add(cursor); params['lastDepositAddress']=cursor[0]
            if cursor[1] is not None: params['lastDepositMemo']=cursor[1]
            else: params.pop('lastDepositMemo',None)
            # Continue to an empty page; a short page alone does not establish exhaustion.
        raise SourceError('Page budget exhausted; period is incomplete')
