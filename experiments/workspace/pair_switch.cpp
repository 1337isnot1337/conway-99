// Swap columns belonging to the same shared-anchor class, maintaining both pair catalogues.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <vector>

using namespace std;
struct Row {int mask,group;};
int main(int argc,char **argv){
    if(argc!=5)return 2;
    ifstream fin(argv[1]);int n,k;fin>>n>>k;
    vector<Row> left(n),right(n);
    for(auto *side:{&left,&right})for(auto &r:*side)fin>>r.group>>r.mask;
    vector<int> target(k*k);for(auto &v:target)fin>>v;
    if(!fin||k>24)return 3;
    vector<int> perm(n),best_permutation;vector<vector<int>> groups(4);
    for(int group=0;group<4;group++){
        vector<int> v;for(int j=0;j<n;j++)if(right[j].group==group)v.push_back(j);
        for(int i=0;i<n;i++)if(left[i].group==group){
            groups[group].push_back(i);perm[i]=v.back();v.pop_back();
        }
    }
    mt19937 rng(atoi(argv[3]));int budget=atoi(argv[4]),best=1000000;
    vector<pair<int,int>> swaps;
    for(auto &g:groups)for(int i:g)for(int j:g)if(i<j)swaps.emplace_back(i,j);
    for(int epoch=0;epoch<budget;epoch++){
        if(epoch==0||epoch%12==0){
            for(auto &g:groups)for(int i=g.size()-1;i>0;i--)swap(perm[g[i]],perm[g[rng()%(i+1)]]);
        }else perm=best_permutation;
        vector<int> d=target;for(int &v:d)v=-v;
        for(int i=0;i<n;i++)for(int x=left[i].mask;x;x&=x-1)for(int y=right[perm[i]].mask;y;y&=y-1)d[__builtin_ctz(x)*k+__builtin_ctz(y)]++;
        int score=0;for(int v:d)score+=v*v;
        double top=(epoch%12==0?2.:0.65+0.06*(epoch%11));
        int steps=150000;
        for(int it=0;it<steps;it++){
            auto [a,b]=swaps[rng()%swaps.size()];
            int lm=left[a].mask^left[b].mask,rm=right[perm[a]].mask^right[perm[b]].mask;
            int delta=0,ll[16],vv[16],nn=0;
            for(int x=lm;x;x&=x-1)for(int y=rm;y;y&=y-1){
                int i=__builtin_ctz(x),j=__builtin_ctz(y),v=(((left[a].mask>>i)^(right[perm[a]].mask>>j))&1)?1:-1;
                ll[nn]=i*k+j;vv[nn++]=v;delta+=2*d[i*k+j]*v+1;
            }
            double temp=top*(1.-(double)it/steps)+.08;
            if(delta>0 && (double)rng()/4294967296.>=exp(-delta/temp))continue;
            for(int h=0;h<nn;h++)d[ll[h]]+=vv[h];
            swap(perm[a],perm[b]);score+=delta;
            if(score<best){
                best=score;best_permutation=perm;
                ofstream of(argv[2]);of<<score<<'\n';for(int j:perm)of<<j<<' ';of<<'\n';
                if(best==0){cout<<"exact cover at epoch "<<epoch<<" move "<<it<<endl;return 0;}
            }
        }
    }
    cout<<"best squared defect "<<best<<endl;
}
