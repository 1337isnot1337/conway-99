"""Apply the zero-grid triangle capacity inequality to near-minimal covers."""

from functools import lru_cache

from low_triangle_cover import SPECIAL, degree_profiles, low


def weight(d):
    e = sum(d)//2
    disjoint = (e*(e-1)-sum(x*(x-1) for x in d))//2
    capacity = 2*disjoint-sum(min(2,x)*(6-x) for x in d)+2*d.count(2)
    z = d.count(0)
    return 4*capacity+z*z+16*z-6*max(0,z-1)


def verify():
    options = sorted(d for d in degree_profiles() if low(d) > 1)
    charges = [(low(d)-1,d.count(0)-1,weight(d)-17) for d in options]

    @lru_cache(None)
    def minimum(i, excess, zeros):
        if not excess:
            return 0 if not zeros else float('inf')
        if i == len(options) or abs(zeros) > excess:
            return float('inf')
        best = minimum(i+1,excess,zeros)
        cost,change,w = charges[i]
        if cost <= excess:
            best = min(best,w+minimum(i,excess-cost,zeros-change))
        return best

    def populations(i, excess, zeros, allowance, chosen):
        if minimum(i,excess,zeros) > allowance:
            return
        if not excess:
            yield chosen
            return
        for j in range(i,len(options)):
            cost,change,w = charges[j]
            if cost <= excess:
                yield from populations(j,excess-cost,zeros-change,allowance-w,chosen+(options[j],))

    for count in range(33,39):
        excess = 3*count-99
        raw = arithmetic = 0
        for zeros in range(-excess,excess+1):
            total = 99+zeros
            if total % 3:
                continue
            for ds in populations(0,excess,zeros,total*total//9-17*99,()):
                raw += 1
                if any(2*sum(x in SPECIAL for x in d) >= len(ds) for d in ds):
                    continue
                if any(sum(d.count(z) for d in ds)%3 or
                       (any(z in d for d in ds) and sum(z in d for d in ds) < 3)
                       for z in SPECIAL):
                    continue
                h = [9-sum(d)//2 for d in ds]
                if sum(h)%9:
                    continue
                arithmetic += 1
                assert min(h) >= 0 and max(h) > sum(h)//9 and sum(x > 0 for x in h) < 15
        assert (raw,arithmetic) == ((244,18) if count == 38 else (0,0))
        print(f'{count} low triangles: {raw} multisets satisfy the capacity inequality, '
              f'{arithmetic} pass the arithmetic, none extend.')


if __name__ == '__main__':
    verify()
