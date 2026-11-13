import {describe,it,expect} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {afterEach} from 'vitest';
import {emptyDashboard,filterRange,freshness,format,validateDashboard,metricAvailability} from '../services/data';
import {Overview,ThesisLab,NetworkActivity,IntentsEconomy,Methodology} from '../pages/ResearchPages';
import {DateRangeSelector} from '../components/ui';
import published from '../../public/data/dashboard.json';
afterEach(cleanup);
describe('Evidence-free dashboard',()=>{
 for(const [name,Page] of Object.entries({Overview,ThesisLab,NetworkActivity,IntentsEconomy,Methodology})){
  it(`${name} renders without credentials or invented metrics`,()=>{render(<MemoryRouter><Page data={emptyDashboard()}/></MemoryRouter>);expect(screen.queryByText(/live data/i)).not.toBeInTheDocument();expect(document.body.textContent).toMatch(/unavailable|Insufficient data/);expect(document.body.textContent).not.toMatch(/\$[0-9]/)})
 }
 it('reports an unresolved thesis',()=>{render(<MemoryRouter><ThesisLab data={emptyDashboard()}/></MemoryRouter>);expect(screen.getByText('Insufficient data')).toBeInTheDocument();expect(screen.getByText(/No verified supporting observations/)).toBeInTheDocument()});
 it('formats missing observations as gaps',()=>{expect(format(null)).toBe('—');expect(format(0)).toBe('0')});
 it('freshness depends on observations',()=>{expect(freshness(null)).toBe('unavailable');expect(freshness('2026-01-01',3,Date.parse('2026-01-08'))).toBe('stale')});
 it('filters calendar ranges',()=>{expect(filterRange([{date:'2026-01-01',volume:1},{date:'2026-02-01',volume:2}],'30')).toHaveLength(1)});
 it('range selection is interactive',()=>{let selected='';render(<DateRangeSelector value="90" onChange={v=>selected=v}/>);fireEvent.click(screen.getByText('30D'));expect(selected).toBe('30')});
 it('rejects malformed dashboard exports',()=>{expect(()=>validateDashboard({series:[]})).toThrow();expect(validateDashboard(emptyDashboard()).verdict).toBe('Insufficient data')});
 it('does not borrow transaction freshness for sparse contract observations',()=>{const data=emptyDashboard();data.series=[{date:'2026-11-09',transactions:10,contracts:5},{date:'2026-11-10',transactions:11,contracts:null}];data.sources.network={status:'current',reason:'Synthetic fixture',latest:'2026-11-10',retrieved_at:'2026-11-13T00:00:00Z'};expect(metricAvailability(data,'contracts').latest).toBe('2026-11-09');expect(metricAvailability(data,'transactions').latest).toBe('2026-11-10')});
 it('labels omitted contracts without turning them into zero',()=>{const data=emptyDashboard();data.series=[{date:'2026-11-10',transactions:10,contracts:null}];expect(metricAvailability(data,'contracts').status).toBe('unavailable');expect(metricAvailability(data,'contracts').reason).toMatch(/not acquired/);expect(format(data.series[0].contracts)).toBe('—')});
});

describe('Published release',()=>{
 const data=validateDashboard(published);
 for(const [name,Page] of Object.entries({Overview,NetworkActivity,IntentsEconomy,ThesisLab,Methodology})){
  it(`${name} renders verified source coverage with methodology access`,()=>{
   render(<MemoryRouter><Page data={data}/></MemoryRouter>);
   expect(screen.queryByRole('alert')).not.toBeInTheDocument();
   expect(document.body.textContent).toMatch(/2026-11-09/);
   expect(document.body.textContent).not.toMatch(/live data/i);
   for(const link of document.querySelectorAll('a[href="/methodology"]'))expect(link).toHaveAttribute('href','/methodology');
   if(name!=='Methodology')expect(document.querySelector('a[href="/methodology"]')).not.toBeNull();
  });
 }
 it('retains six returns, sparse calls and unavailable prices',()=>{
  expect(data.daily.network).toHaveLength(7);expect(data.daily.intents).toHaveLength(7);
  expect(data.series.filter(r=>r.contracts!==null && r.contracts!==undefined)).toHaveLength(1);
  expect(data.sources.price.status).toBe('unavailable');expect(data.daily.price??[]).toHaveLength(0);
  expect(data.research_coverage?.paired_daily_changes).toBe(6);
  expect(data.verdict).toBe('Insufficient data');
 });
 it('keeps price downloads disabled in methodology',()=>{
  render(<MemoryRouter><Methodology data={data}/></MemoryRouter>);
  expect(document.querySelector('a[href="/data/price.csv"]')).toBeNull();
  expect(document.querySelector('a[href="/data/network.csv"]')).not.toBeNull();
  expect(document.querySelector('a[href="/data/intents.csv"]')).not.toBeNull();
 });
});
