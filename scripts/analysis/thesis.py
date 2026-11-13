def verdict(results):
    # Evaluate prespecified same-day adoption associations relative to price.
    same={r['pair']:r for r in results if r['lag']==0 and r['rho'] is not None and r['n']>=30}
    price=same.get('volume \u2192 price');adoption=[same.get('volume \u2192 '+k) for k in ('signers','transactions','contracts')]
    if price is None or any(r is None for r in adoption):return 'Insufficient data'
    differences=[r['rho']-price['rho'] for r in adoption]
    if all(d>=0.2-1e-12 for d in differences) and all(r['rho']>=0.3 for r in adoption):return 'Evidence supports the hypothesis'
    if all(d<=-0.2+1e-12 for d in differences):return 'Evidence does not support the hypothesis'
    return 'Mixed or inconclusive evidence'
