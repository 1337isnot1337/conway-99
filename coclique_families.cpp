// Difference-family search under simultaneous translation on two copies of Z/11.
// Enumerate the composition with three blocks of each of types 1 and 3, and one balanced block.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <set>
#include <unordered_map>
#include <vector>
using namespace std;
using Mask=uint32_t;using Key=uint64_t;
Mask move_mask(Mask m,int a,int b,int c,bool swap_layers){
    Mask out=0;
    while(m){int i=__builtin_ctz(m);m&=m-1;int s=i/11;
        out|=1u<<((s^swap_layers)*11+(a*(i%11)+(s?c:b))%11);
    }return out;
}
Mask orbit(Mask m){
    Mask out=m;for(int s=1;s<11;s++)out=min(out,move_mask(m,1,s,s,false));return out;
}
struct B{Mask bits;Key pairs;array<Mask,4> triples;};
bool overlap(const B&a,const B&b){for(auto t:a.triples)for(auto u:b.triples)if(t==u)return true;return false;}
const Key even_bits=0x55555555555ULL;
bool combine(Key a,Key b,Key &c){
    // Each 2-bit digit is at most two, prior to this addition.
    Key ah=(a>>1)&even_bits,bh=(b>>1)&even_bits;
    if((ah&((b|bh)&even_bits))||(bh&((a|ah)&even_bits)))return false;
    c=a+b;return true;
}
struct Three{int a,b,c;};
int main(int argc,char**argv){
    if(argc!=4)return 2;
    bool pure=atoi(argv[3]);
    int limit=atoi(argv[2]);
    vector<B> bs;vector<int> by[5];
    for(Mask m=1;m<(1u<<22);m++){
        if(__builtin_popcount(m)!=4||orbit(m)!=m)continue;
        B v{m,0,{}};int q=0,count[21]={};bool ok=true;
        for(Mask l=m;l;l&=l-1){
            int i=__builtin_ctz(l);v.triples[q++]=orbit(m^(1u<<i));
            for(Mask r=l&(l-1);r;r&=r-1){
                int j=__builtin_ctz(r),t;
                if(i/11==j/11){int d=j-i;t=5*(i/11)+min(d,11-d)-1;}
                else t=10+(j-i)%11;
                if(++count[t]>2)ok=false;
            }
        }
        sort(v.triples.begin(),v.triples.end());
        if(!ok||adjacent_find(v.triples.begin(),v.triples.end())!=v.triples.end())continue;
        for(int t=0;t<21;t++)v.pairs+=((Key)count[t])<<(2*t);
        by[__builtin_popcount(m&2047)].push_back(bs.size());bs.push_back(v);
    }
    ofstream out(argv[1]);int total=0;
    for(int root:by[pure?0:2]){
        Mask r=bs[root].bits;bool least=true;
        // Normalizer modulo common translation. Fix the unique balanced orbit.
        for(int a=1;a<11&&least;a++)for(int b=0;b<11&&least;b++)for(int s=0;s<(pure?1:2);s++)
            if(orbit(move_mask(r,a,0,b,s))<r)least=false;
        if(!least)continue;
        unordered_map<Key,vector<Three>> table;
        for(int side=0;side<2;side++){
            int first=side?3:(pure?2:1), third=(side&&pure)?2:first;
            auto &v=by[first];auto &vc=by[third];
            for(int ai=0;ai<(int)v.size();ai++){
                int a=v[ai];Key ra;if(overlap(bs[root],bs[a])||!combine(bs[root].pairs,bs[a].pairs,ra))continue;
                for(int bi=ai+1;bi<(int)v.size();bi++){
                    int b=v[bi];Key rab;if(overlap(bs[root],bs[b])||overlap(bs[a],bs[b])||!combine(ra,bs[b].pairs,rab))continue;
                    for(int ci=first==third?bi+1:0;ci<(int)vc.size();ci++){
                        int c=vc[ci];Key rabc;if(overlap(bs[root],bs[c])||overlap(bs[a],bs[c])||overlap(bs[b],bs[c])||!combine(rab,bs[c].pairs,rabc))continue;
                        if(side==0){table[rabc].push_back({a,b,c});continue;}
                        const Key goal=((1ULL<<42)-1)/3*2;
                        auto it=table.find(goal-(rabc-bs[root].pairs));if(it==table.end())continue;
                        for(auto v:it->second){
                            if(pure&&c>=v.a)continue;
                            bool ok=true;for(int x:{a,b,c})for(int y:{v.a,v.b,v.c})if(overlap(bs[x],bs[y]))ok=false;
                            if(!ok)continue;
                            for(int x:{root,a,b,c,v.a,v.b,v.c})out<<bs[x].bits<<' ';
                            out<<'\n';total++;
                            if(limit>0&&total>=limit){cout<<"reached limit "<<total<<endl;return 0;}
                        }
                    }
                }
            }
        }
        cout<<"balanced root "<<r<<" cumulative designs "<<total<<endl;
    }
}
