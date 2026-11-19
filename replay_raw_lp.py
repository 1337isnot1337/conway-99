"""Check a SoPlex rational primal solution against every row of the source LP."""
from fractions import Fraction as F
from pathlib import Path
import sys
def replay(base):
    report=Path(base+'.spx').read_text()
    assert 'SoPlex status       : problem is solved [optimal]' in report
    point=report.split('Primal solution (name, value):')[1].split('All other variables are zero.')[0]
    vars={}
    for line in point.splitlines():
        if line.strip():
            k,v=line.split();vars[k]=F(v)
    rows=0
    with open(base+'.lp') as f:
        for line in f:
            if line.startswith('Bounds'):break
            if ':' not in line or line.startswith(' obj'):continue
            lhs=line.split(':',1)[1].strip().split()
            rel,rhs=lhs[-2:];parts=lhs[:-2];v=F(0)
            for j in range(0,len(parts),3):
                sign,a,x=parts[j:j+3];v+=(1 if sign=='+' else -1)*F(a)*vars.get(x,0)
            assert (v==F(rhs) if rel=='=' else v>=F(rhs)),(line[:30],v,rhs);rows+=1
    print('rational primal verified against',rows,'raw linear constraints',flush=True)
if __name__=='__main__':replay(sys.argv[1])
