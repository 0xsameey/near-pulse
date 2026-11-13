import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,CartesianGrid,Tooltip,Legend} from 'recharts';
import {Link} from 'react-router-dom';
import type {Dashboard,Metric,Observation} from '../types';
import {metricInfo} from '../services/data';
import {EmptyDataState,MethodologyDrawer,ResearchTable,SourceBadge} from './ui';

const candidates:Metric[]=['volume','signers','transactions','contracts','price'];
const colors=['#68e0a1','#b9b3e8','#e4bd83','#7dc8d5','#d5a4b4'];
export function normalizeOverlap(rows:Observation[],metrics:Metric[]){
 const anchor=rows.find(r=>metrics.every(k=>typeof r[k]==='number'&&(r[k] as number)>0));
 if(!anchor)return [];
 return rows.filter(r=>r.date>=anchor.date).map(r=>Object.fromEntries([['date',r.date],...metrics.map(k=>[k,typeof r[k]==='number'?(r[k] as number)/(anchor[k] as number)*100:null])])) as Observation[];
}
export function AdoptionComparison({data,rows}:{data:Dashboard;rows:Observation[]}){
 const metrics=candidates.filter(k=>rows.some(r=>typeof r[k]==='number'));
 const normalized=metrics.length>=2?normalizeOverlap(rows,metrics):[];
 return <section className="panel chart-panel">
  <div className="panel-head"><div><span className="eyebrow">COMMON OBSERVATION DATE · BASE 100 · UTC</span><h3>Indexed adoption comparison</h3></div><MethodologyDrawer/></div>
  <div className="chart-meta">{(['network','intents','price'] as const).filter(k=>metrics.some(m=>metricInfo[m].source===k)).map(k=><SourceBadge key={k} source={k}/>)}{!metrics.includes('price')&&<span>Price unavailable; comparison with price remains untested.</span>}</div>
  {normalized.length?<div className="chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={normalized}><CartesianGrid stroke="#27332d" vertical={false}/><XAxis dataKey="date" minTickGap={50} tick={{fontSize:10,fill:'#9aa89f'}}/><YAxis tick={{fontSize:10,fill:'#9aa89f'}}/><Tooltip contentStyle={{background:'#151c19',border:'1px solid #35463c'}}/><Legend/>{metrics.map((k,i)=><Line key={k} dataKey={k} name={metricInfo[k].label} stroke={colors[i]} strokeDasharray={i%2?'5 3':undefined} dot={normalized.length===1} connectNulls={false} strokeWidth={2}/>)}</LineChart></ResponsiveContainer></div>:<EmptyDataState source={{status:'unavailable',reason:'At least two verified series with a common nonzero starting observation are needed for a fair indexed comparison.',latest:null,retrieved_at:null}}/>}
  <div className="chart-takeaway">{normalized.length?'Series share one observed base date. Relative movement does not establish causal or predictive value.':'No comparable verified history exists; relative performance cannot be measured.'}</div>
  <div className="chart-footer"><span>Period: {normalized.length?`${normalized[0].date} — ${normalized.at(-1)?.date}`:'Unknown'}<br/>{Object.entries(data.sources).map(([k,s])=>`${k}: latest ${s.latest??'unknown'}, retrieved ${s.retrieved_at?.slice(0,10)??'unknown'}`).join(' · ')}</span><Link to="/methodology">Sources & method</Link></div>
  {normalized.length>0&&<details className="chart-table"><summary>Accessible indexed observations</summary><ResearchTable rows={normalized} columns={['date',...metrics]}/></details>}
 </section>
}
