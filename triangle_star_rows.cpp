// Sample or enumerate exact eight-row triangle-star covers, retaining one edge between zero-overlap rows.
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <unordered_set>
#include <vector>
using namespace std;using Mask=uint64_t;
struct Cover{
    vector<Mask> rows;unordered_set<Mask> present;array<Mask,8> stars{};
    Mask center=0,lo=0,hi=0;mt19937_64 rand;int target,found=0;long long nodes=0;ofstream &out;
    Cover(int s,int t,ofstream&o):rand(s),target(t),out(o){}
    bool legal(Mask a,int level,int zero){
        bool z=!(a&center);if(z&&zero==2)return false;
        for(int i=0;i<level;i++){
            auto b=stars[i];int h=popcount(a&b);if(h>1||(h&&z&&!(b&center)))return false;
        }
        return true;
    }
    void visit(Mask one,Mask two,int depth,int zero){
        if(found>=target)return;nodes++;
        int n=rows.size(),start=rand()%n,chosen=0;
        for(int idx=0;idx<n;idx++){
            Mask a=rows[(start+idx)%n];
            if(a&~one || (depth==6 && (two&~a)) || !legal(a,depth,zero))continue;
            Mask next=(one&~a)|two;
            int z=zero+(!(a&center));stars[depth]=a;
            if(depth==6){
                if(present.count(next)&&legal(next,depth+1,z)&&z+(!(next&center))==2){
                    stars[7]=next;for(auto w:stars)out<<w<<' ';out<<'\n';found++;return;
                }
            }else{
                visit(next,two&~a,depth+1,z);
                if(found>=target||++chosen>=2)return;
            }
        }
    }
};
int main(int argc,char**argv){
    if(argc!=5)return 2;ifstream in(argv[1]);ofstream out(argv[2]);Cover c(atoi(argv[3]),atoi(argv[4]),out);
    int n,d;in>>n;
    for(int i=0;i<36;i++){in>>d;if(d)c.lo|=Mask(1)<<i;if(d==2)c.hi|=Mask(1)<<i;}
    in>>c.center;c.rows.resize(n);for(auto&r:c.rows){in>>r;c.present.insert(r);}
    shuffle(c.rows.begin(),c.rows.end(),c.rand);
    for(int i=0;i<50000&&c.found<c.target;i++){if(i%50==0)shuffle(c.rows.begin(),c.rows.end(),c.rand);c.visit(c.lo,c.hi,0,0);}
    cout<<"search nodes "<<c.nodes<<" covers "<<c.found<<endl;
}
