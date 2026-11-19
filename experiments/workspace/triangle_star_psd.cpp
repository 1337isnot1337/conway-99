// Condition the two exact-cover searches on the two Gram matrices throughout a star.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <unordered_map>
#include <vector>
using namespace std;using Mask=uint64_t;
struct Point{Mask mask;array<int,6> sites;array<array<double,37>,2> feat;double diag[2];};
struct Search{
    vector<Point>P;vector<int> order;unordered_map<Mask,int> ids;
    int stars[9]{},target;long long nodes=0,cap;int found=0;Mask lo=0,hi=0;
    double L[2][9][9]{};mt19937_64 rng;ofstream&out;
    Search(int seed,int t,long long c,ofstream&o):target(t),cap(c),rng(seed),out(o){}
    double projected(int i,int j,int g){
        auto &f=P[i].feat[g];double x=f[0];for(int h:P[j].sites)x+=f[h+1];return x;
    }
    void read(istream& in,istream&features){
        int n,d;in>>n;for(int h=0;h<36;h++){in>>d;if(d)lo|=Mask(1)<<h;if(d==2)hi|=Mask(1)<<h;}
        P.resize(n+1);order.resize(n);iota(order.begin(),order.end(),1);shuffle(order.begin(),order.end(),rng);
        for(int i=0;i<=n;i++){
            auto &p=P[i];in>>p.mask;int h=0;for(auto t=p.mask;t;t&=t-1)p.sites[h++]=countr_zero(t);assert(h==6);
            features.read((char*)p.feat.data(),2*37*sizeof(double));assert(features);
            if(i)ids[p.mask]=i;
            for(int g=0;g<2;g++)p.diag[g]=projected(i,i,g)+3+g;
        }
        for(int g=0;g<2;g++)L[g][0][0]=sqrt(P[0].diag[g]);
    }
    bool legal(int i,int depth,int zero){
        auto m=P[i].mask;bool z=!(m&P[0].mask);
        if(z&&zero==2)return false;
        for(int h=1;h<=depth;h++){
            auto v=P[stars[h]].mask;auto ov=m&v;if(ov&&(ov&(ov-1)||(z&&!(v&P[0].mask))))return false;
        }
        return true;
    }
    bool add(int i,int depth){
        int p=depth+1;stars[p]=i;
        for(int g=0;g<2;g++){
            double sum=P[i].diag[g];
            for(int h=0;h<p;h++){
                int j=stars[h];bool edge=!h||(!(P[i].mask&P[0].mask)&&!(P[j].mask&P[0].mask));
                double x=projected(i,j,g)+(g?1.0:-1.0)*edge;
                for(int t=0;t<h;t++)x-=L[g][h][t]*L[g][p][t];
                if(L[g][h][h]<1e-7){if(abs(x)>1e-6)return false;L[g][p][h]=0;}
                else L[g][p][h]=x/L[g][h][h];
                sum-=L[g][p][h]*L[g][p][h];if(sum < -1e-7)return false;
            }
            L[g][p][p]=sqrt(max(0.,sum));
        }
        return true;
    }
    void dfs(Mask one,Mask two,int depth,int zero){
        if(nodes++>=cap||found>=target)return;int n=order.size(),start=rng()%n,chosen=0;
        for(int idx=0;idx<n;idx++){
            int i=order[(start+idx)%n];Mask m=P[i].mask;
            if((m&~one)||(depth==6&&(two&~m))||!legal(i,depth,zero))continue;
            Mask next=(one&~m)|two;int z=zero+(!(m&P[0].mask));
            if(depth==6){
                auto it=ids.find(next);
                if(it!=ids.end()&&legal(it->second,7-1,zero)){
                    if(!add(i,6))continue;int j=it->second;
                    if(!legal(j,7,z)||z+(!(next&P[0].mask))!=2||!add(j,7))continue;
                    for(int h=1;h<=8;h++)out<<P[stars[h]].mask<<' ';out<<'\n';found++;return;
                }
            }else{
                if(!add(i,depth))continue;
                dfs(next,two&~m,depth+1,z);
                if(++chosen>=2||nodes>=cap||found>=target)return;
            }
        }
    }
};
int main(int argc,char**argv){
    if(argc!=7)return 2;ifstream in(argv[1]),feat(argv[2],ios::binary);ofstream out(argv[3]);Search s(atoi(argv[4]),atoi(argv[5]),atoll(argv[6]),out);s.read(in,feat);
    for(int i=0;s.nodes<s.cap&&s.found<s.target;i++){if(i%50==0)shuffle(s.order.begin(),s.order.end(),s.rng);s.dfs(s.lo,s.hi,0,0);}
    cout<<"nodes "<<s.nodes<<" positive covers "<<s.found<<endl;
}
