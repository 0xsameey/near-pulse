import type {Dashboard,Metric,SourceKey} from '../types';
export const metricInfo:Record<Metric,{label:string;unit:string;source:SourceKey;note:string}>={
 signers:{label:'Daily active signers',unit:'Signing accounts / day',source:'network',note:'Signing accounts are not unique people.'},
 transactions:{label:'Daily signed transactions',unit:'Transactions / day',source:'network',note:'Native-chain transaction table rows, including all statuses; checked against partition row counts.'},
 contracts:{label:'Contract function calls',unit:'Function-call actions / day',source:'network',note:'FUNCTION_CALL receipt-action rows, including delegated rows represented by the source. Not successful executions or unique receipts.'},
 volume:{label:'1Click input volume',unit:'USD / day',source:'intents',note:'Successful 1Click swaps grouped by creation date, not completion date.'},
 swaps:{label:'Successful 1Click swaps',unit:'Swaps / day',source:'intents',note:'Explorer 1Click scope; excludes other Intents activity.'},
 price:{label:'NEAR / USD',unit:'USD / NEAR',source:'price',note:'Last available CoinGecko sample in each UTC day.'}};
export function emptyDashboard(reason='No verified source export has been supplied.'):Dashboard {return {generated_at:null,window:{start:null,end:null},sources:{network:{status:'unavailable',reason,latest:null,retrieved_at:null},intents:{status:'unavailable',reason,latest:null,retrieved_at:null},price:{status:'unavailable',reason,latest:null,retrieved_at:null}},series:[],correlations:[],verdict:'Insufficient data',daily:{},freshness_threshold_days:3}}
export function sourceName(k:SourceKey){return {network:'Google BigQuery',intents:'Intents Explorer \u00b7 1Click',price:'CoinGecko'}[k]}
export function format(value:unknown,unit=''){if(typeof value!=='number'||!Number.isFinite(value))return '\u2014';return new Intl.NumberFormat('en-US',{notation:value>=1e6?'compact':'standard',maximumFractionDigits:unit.includes('USD')?2:0,...(unit.includes('USD')?{style:'currency',currency:'USD'}:{})}).format(value)}
export function filterRange(rows:Dashboard['series'],days:string){if(days==='all'||!rows.length)return rows;const last=new Date(rows[rows.length-1].date+'T00:00:00Z');const cut=last.getTime()-(Number(days)-1)*86400000;return rows.filter(r=>new Date(r.date+'T00:00:00Z').getTime()>=cut)}
export function latestValue(rows:Dashboard['series'],metric:Metric){return rows.length?rows[rows.length-1][metric]:null}
export function freshness(latest:string|null,threshold=3,now=Date.now()){return !latest?'unavailable':now-new Date(latest+'T00:00:00Z').getTime()>threshold*86400000?'stale':'current'}
export function metricAvailability(data:Dashboard,metric:Metric):Dashboard['sources']['network']{
 const source=data.sources[metricInfo[metric].source];
 const dates=data.series.filter(r=>typeof r[metric]==='number').map(r=>r.date);
 const latest=dates.at(-1)??null;
 return {...source,latest,status:latest?freshness(latest,data.freshness_threshold_days):'unavailable',
  reason:latest?source.reason:metric==='contracts'?'Contract calls were not acquired for this period. Missing calls remain gaps; verified transaction/signing-account data is preserved.':source.reason};
}
export function validateDashboard(value:unknown):Dashboard{
 const fail=()=>{throw new Error('Dashboard export failed validation. Rebuild verified source exports.')};
 if(!value||typeof value!=='object')return fail();
 const d=value as Dashboard;
 if(!d.sources||!d.window||!d.daily||!Array.isArray(d.series)||!Array.isArray(d.correlations)||typeof d.freshness_threshold_days!=='number'||d.freshness_threshold_days<=0)return fail();
 const verdicts=['Insufficient data','Evidence supports the hypothesis','Mixed or inconclusive evidence','Evidence does not support the hypothesis'];
 if(!verdicts.includes(d.verdict))return fail();
 for(const key of ['network','intents','price'] as const){
  const s=d.sources[key];
  if(!s||!['unavailable','current','stale','incomplete'].includes(s.status)||typeof s.reason!=='string'||!(s.latest===null||/^\d{4}-\d{2}-\d{2}$/.test(s.latest))||!(s.retrieved_at===null||Number.isFinite(Date.parse(s.retrieved_at))))return fail();
  if(s.status==='current'&&!s.latest)return fail();
  if(d.daily[key]&&!Array.isArray(d.daily[key]))return fail();
 }
 let previous='';
 for(const row of d.series){
  if(typeof row.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(row.date)||row.date<=previous)return fail();
  previous=row.date;
  if(Object.entries(row).some(([k,v])=>k!=='date'&&v!==null&&(typeof v!=='number'||!Number.isFinite(v))))return fail();
 }
 for(const r of d.correlations){if(typeof r.pair!=='string'||!Number.isInteger(r.n)||r.n<0||![0,7,30].includes(r.lag)||(r.rho!==null&&(typeof r.rho!=='number'||!Number.isFinite(r.rho)||Math.abs(r.rho)>1)))return fail()}
 return d;
}
export async function loadDashboard():Promise<Dashboard>{
 const r=await fetch('/data/dashboard.json',{cache:'no-store'});
 if(!r.ok)throw new Error('Dashboard export could not be loaded. Run the research rebuild.');
 const d=validateDashboard(await r.json());
 return {...d,sources:Object.fromEntries(Object.entries(d.sources).map(([k,s])=>[k,{...s,status:s.status==='current'?freshness(s.latest,d.freshness_threshold_days):s.status}])) as Dashboard['sources']};
}
