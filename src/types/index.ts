export type SourceKey='network'|'intents'|'price';
export type Metric='signers'|'transactions'|'contracts'|'volume'|'swaps'|'price';
export interface Source {status:'unavailable'|'current'|'stale'|'incomplete';reason:string;latest:string|null;retrieved_at:string|null;provenance?:Record<string,unknown>}
export interface Observation {date:string;[key:string]:string|number|null}
export interface Correlation {pair:string;lag:number;n:number;rho:number|null;p:number|null;start:string|null;end:string|null}
export interface CoverageWindow {start:string|null;end:string|null;observations:number}
export interface Dashboard {generated_at:string|null;window:{start:string|null;end:string|null};sources:Record<SourceKey,Source>;series:Observation[];correlations:Correlation[];verdict:string;daily:Partial<Record<SourceKey,Observation[]>>;assets?:{asset:string;volume:string;share:string|null}[];freshness_threshold_days:number;research_coverage?:{adoption:CoverageWindow;native_and_intents:CoverageWindow;verdict_required:CoverageWindow;paired_daily_changes:number}}
