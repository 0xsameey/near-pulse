import time, math, json, hashlib
from decimal import Decimal
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


class SourceError(RuntimeError): pass

def timestamp(value):
    try:dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (ValueError,TypeError):raise SourceError('Invalid ISO timestamp') from None
    if dt.tzinfo is None: raise SourceError('Timezone is required')
    return dt.astimezone(timezone.utc)

def bounds(start, end):
    a,b=timestamp(start),timestamp(end)
    if not a < b or (b-a).total_seconds() > 366*86400: raise SourceError('Require a finite window of at most 366 days')
    return a,b

class HttpClient:
    def __init__(self, interval=5, session=None, sleep=time.sleep, clock=time.monotonic, retries=3, capture=False, parse_decimal=False):
        if session is None:
            try: import requests
            except ImportError: raise SourceError('Install requests from requirements.txt for live HTTP ingestion') from None
            session=requests.Session()
        self.session=session; self.interval=max(0,interval)
        self.sleep=sleep; self.clock=clock; self.last=None; self.retries=retries
        self.events=[];self.responses=[];self.capture=capture;self.parse_decimal=parse_decimal
    def get(self,url,params,headers):
        for attempt in range(self.retries+1):
            if self.last is not None: self.sleep(max(0,self.interval-(self.clock()-self.last)))
            self.last=self.clock()
            event={'requested_at':datetime.now(timezone.utc).isoformat(),'url':url,'parameters':params.copy(),'attempt':attempt+1,'http_status':None}
            self.events.append(event)
            # Do not follow redirects as extra unpaced requests, or forward
            # credential headers to an endpoint not explicitly configured.
            try: response=self.session.get(url,params=params,headers=headers,timeout=(10,60),allow_redirects=False)
            except (OSError, TimeoutError) as error:
                event['error_type']=type(error).__name__
                # Classify the known socket denial without serializing requests,
                # exception attributes or request headers that may hold secrets.
                socket_error='WinError 10013' if '10013' in str(error) else 'transport unavailable'
                event['transport_error']=socket_error
                if attempt==self.retries: raise SourceError(f'HTTP transport failed ({socket_error}); no complete export') from None
                self.sleep(min(30,2**attempt)); continue
            event['http_status']=response.status_code
            if response.status_code==429 or 500<=response.status_code<600:
                if attempt==self.retries: raise SourceError('HTTP retry budget exhausted; incomplete window')
                retry=response.headers.get('Retry-After','')
                try: delay=float(retry)
                except ValueError:
                    try: delay=(parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds()
                    except (ValueError,TypeError): delay=2**attempt
                if not math.isfinite(delay) or delay>300: raise SourceError('Retry-After exceeds bounded wait budget')
                self.sleep(max(self.interval,delay,0)); continue
            if response.status_code!=200: raise SourceError(f'Upstream HTTP {response.status_code}; check authentication and entitlement')
            try:
                if hasattr(response,'content'):
                    body=response.content
                    event['response_sha256']=hashlib.sha256(body).hexdigest()
                    if self.capture:self.responses.append({'request':event.copy(),'body':body})
                    return json.loads(body,parse_float=Decimal) if self.parse_decimal else response.json()
                return response.json()
            except ValueError: raise SourceError('Invalid JSON response') from None
        raise SourceError('Request failed')
