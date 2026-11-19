// Complete all two-symbol margins of a fixed unsigned book array by binary signs.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>
using namespace std;using Mask=uint64_t;
struct SignSearch {
    Mask support[18]{},partial[18]{};array<vector<Mask>,18> dom;
    long long nodes=0,limit;int found=0,cap;ofstream &out;
    SignSearch(long long max,int c,ofstream &o):limit(max),cap(c),out(o){}
    void prepare(){
        for(int i=0;i<18;i++){
            vector<int> sites;for(auto a=support[i];a;a&=a-1)sites.push_back(countr_zero(a));assert(sites.size()==20);
            for(unsigned s=(1<<10)-1;s<(1<<20);){
                if(s&1){
                    Mask w=0;for(unsigned a=s;a;a&=a-1)w|=Mask(1)<<sites[countr_zero(a)];
                    bool ok=true;for(int j=0;j<18;j++)if(2*popcount(w&support[j])!=popcount(support[i]&support[j])){ok=false;break;}
                    if(ok)dom[i].push_back(w);
                }
                unsigned l=s&-s,h=s+l;s=h|(((h^s)>>2)/l);
            }
        }
    }
    bool compatible(int i,Mask a,int j,Mask b){return 4*popcount(a&b)==popcount(support[i]&support[j]);}
    void dfs(unsigned left,const array<vector<Mask>,18>&D,const array<Mask,60>&twice,const array<Mask,60>&once){
        if(nodes++>=limit||found>=cap)return;
        if(!left){for(int i=0;i<18;i++)out<<partial[i]<<' ';out<<endl;found++;return;}
        int p=-1;for(auto s=left;s;s&=s-1){int i=countr_zero(s);if(p<0||D[i].size()<D[p].size())p=i;}
        unsigned next=left^(1<<p);
        for(auto v:D[p]){
            auto o=once,t=twice;bool good=true;
            for(auto m:{v,support[p]^v}){
                for(Mask a=m;a;a&=a-1){int i=countr_zero(a);Mask b=m&~(Mask(1)<<i);
                    if(t[i]&b){good=false;break;}t[i]|=o[i]&b;o[i]|=b;}
                if(!good)break;
            }
            if(!good)continue;array<vector<Mask>,18> filtered;
            for(unsigned s=next;s;s&=s-1){int j=countr_zero(s);for(auto w:D[j])if(compatible(p,v,j,w))filtered[j].push_back(w);
                if(filtered[j].empty()){good=false;break;}}
            if(good){partial[p]=v;dfs(next,filtered,t,o);}
            if(nodes>=limit||found>=cap)return;
        }
    }
};
int main(int argc,char**argv){
    if(argc!=5)return 2;ifstream in(argv[1]);ofstream out(argv[2]);SignSearch s(atoll(argv[3]),atoi(argv[4]),out);
    for(auto &m:s.support)in>>m;s.prepare();cout<<"domain sizes";for(auto &d:s.dom)cout<<" "<<d.size();cout<<endl;
    s.dfs((1<<18)-1,s.dom,{},{});cout<<"nodes "<<s.nodes<<" designs "<<s.found<<endl;
}
