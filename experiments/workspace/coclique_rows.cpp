// Enumerate all neighborhoods of each block vertex of a prescribed coclique design.
#include <algorithm>
#include <array>
#include <climits>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>
using namespace std;
using Bits=unsigned __int128;
int low(Bits x){return (uint64_t)x?__builtin_ctzll((uint64_t)x):64+__builtin_ctzll((uint64_t)(x>>64));}
int count(Bits x){return __builtin_popcountll((uint64_t)x)+__builtin_popcountll((uint64_t)(x>>64));}
struct Enumerator {
    int k,h,n;
    vector<unsigned> block;
    vector<Bits> point,conflict,output;
    void visit(Bits chosen,Bits available,array<int,32> need,int slots){
        if(slots<0||count(available)<slots)return;
        int p=-1,best=INT_MAX;
        for(int i=0;i<h;i++)if(need[i]){
            int m=count(available&point[i]),r=need[i];if(m<r)return;
            int ways=r==1?m:m*(m-1)/2;if(ways<best){p=i;best=ways;}
        }
        if(p<0){if(!slots)output.push_back(chosen);return;}
        if(!slots)return;
        Bits through=available&point[p];available&=~through;
        for(Bits a=through;a;a&=a-1){
            int i=low(a);Bits f=(Bits)1<<i,alt=available&~conflict[i];
            auto next=need;
            for(unsigned m=block[i];m;m&=m-1){
                int t=__builtin_ctz(m);if(--next[t]==0)alt&=~point[t];
            }
            if(need[p]==1){visit(chosen|f,alt,next,slots-1);continue;}
            Bits later=(a&(a-1))&~conflict[i];
            for(Bits b=later;b;b&=b-1){
                int j=low(b);auto final=next;Bits options=alt&~conflict[j];bool ok=true;
                for(unsigned m=block[j];m;m&=m-1){
                    int t=__builtin_ctz(m);
                    if(--final[t]<0){ok=false;break;}if(!final[t])options&=~point[t];
                }
                if(ok)visit(chosen|f|((Bits)1<<j),options,final,slots-2);
            }
        }
    }
    void prepare(){
        point.assign(h,0);conflict.assign(n,0);
        for(int i=0;i<n;i++){
            for(unsigned m=block[i];m;m&=m-1)point[__builtin_ctz(m)]|=(Bits)1<<i;
            for(int j=0;j<n;j++)if(i==j||__builtin_popcount(block[i]&block[j])>=2)conflict[i]|=(Bits)1<<j;
        }
    }
    void row(int i){
            output.clear();array<int,32> need{};
            for(int p=0;p<h;p++)need[p]=2-((block[i]>>p)&1);
            visit(0,(((Bits)1<<n)-1)&~conflict[i],need,k-__builtin_popcount(block[i]));
    }
    void run(int step,ostream &out){
        prepare();
        for(int i=0;i<n;i+=step){
            row(i);
            out<<i<<' '<<output.size()<<'\n';
            for(auto s:output)out<<(uint64_t)s<<' '<<(uint64_t)(s>>64)<<'\n';
        }
    }
};
#ifndef COCLIQUE_ROWS_LIBRARY
int main(int argc,char**argv){
    if(argc!=3)return 2;
    ifstream in(argv[1]);ofstream out(argv[2]);Enumerator e;int step;in>>e.k>>e.h>>e.n>>step;
    if(e.h>32||e.n>127||step<=0)return 3;
    e.block.resize(e.n);for(auto &b:e.block){in>>b;if(!b)return 4;}
    e.run(step,out);
}

#endif
