#include <stdio.h>
#include <gmp.h>
#include <cddlib/setoper.h>
#include <cddlib/cdd.h>
int main(int argc,char **argv) {
    dd_set_global_constants();
    dd_ErrorType e=dd_NoError;
    FILE *f=fopen(argv[1],"r"); if (!f) return 2;
    dd_MatrixPtr m=dd_PolyFile2Matrix(f,&e); if (e!=dd_NoError) return 3;
    dd_LPPtr lp=dd_Matrix2Feasibility(m,&e); if(e!=dd_NoError)return 4;
    dd_LPSolve(lp,dd_DualSimplex,&e);
    if(e!=dd_NoError) {dd_WriteErrorMessages(stderr,e);return 5;}
    dd_WriteLPResult(stdout,lp,e);
    return 0;
}
