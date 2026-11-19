// Walk among symmetric, zero-diagonal binary projections by orthogonal transvections.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <vector>
using namespace std;
using Bits=unsigned __int128;constexpr int n=99;using Graph=array<Bits,n>;
Bits bit(int i){return (Bits)1<<i;}
int pop(Bits x){return __builtin_popcountll((uint64_t)x)+__builtin_popcountll((uint64_t)(x>>64));}
int low(Bits x){return (uint64_t)x?__builtin_ctzll((uint64_t)x):64+__builtin_ctzll((uint64_t)(x>>64));}
Bits act(const Graph &G,Bits x){Bits v=0;while(x){v^=G[low(x)];x&=x-1;}return v;}
Graph toggle(Graph G,Bits v,Bits w){
    for(Bits x=v;x;x&=x-1)G[low(x)]^=w;
    for(Bits x=w;x;x&=x-1)G[low(x)]^=v;
    return G;
}
struct Score{int defect,degree,miss;};
Score score(const Graph&G){
    Score s{};
    for(int i=0;i<n;i++){
        int d=pop(G[i])-14;s.degree+=d*d;s.defect+=d*d;s.miss+=(d!=0);
        for(int j=0;j<i;j++){int a=pop(G[i]&G[j])+(int)((G[i]>>j)&1)-2;s.defect+=2*a*a;s.miss+=(a!=0);}
    }return s;
}
void save(const Graph&G,const string &out){
    ofstream f(out);for(int i=0;i<n;i++){for(int j=0;j<n;j++)f<<(int)((G[i]>>j)&1)<<' ';f<<'\n';}
}
int main(int argc,char**argv){
    if(argc!=6)return 2;
    ifstream f(argv[1]);Graph G{};for(int i=0;i<n;i++)for(int j=0;j<n;j++){int v;f>>v;if(v)G[i]|=bit(j);}
    mt19937 rng(atoi(argv[3]));int iterations=atoi(argv[4]),r=atoi(argv[5]);
    auto randbit=[&](){return bit(rng()%n);};
    auto proj=[&](bool image,int t){
        Bits x=0;while(pop(x)<t)x^=randbit();Bits a=act(G,x);return image?a:(x^a);
    };
    while(r!=54){
        bool remove=r>54;int minscore=1<<30;Graph good=G;
        for(int it=0;it<3500;it++){
            Bits a=proj(remove,remove?1:2),b=proj(remove,remove?1:2);
            if(!(pop(a&b)&1)||pop(a)%2||pop(b)%2)continue;
            auto H=toggle(G,a,b);auto s=score(H);
            if(s.defect+4*s.degree<minscore){minscore=s.defect+4*s.degree;good=H;}
        }
        if(minscore==(1<<30))return 4;
        r+=remove?-2:2;G=good;
    }
    auto first=score(G);int best=first.defect,accepted=0;Graph bestG=G;
    int cost=first.defect+4*first.degree;save(G,argv[2]);
    for(int t=0;t<iterations;t++){
        if(t&&t%20000==0){G=bestG;auto s=score(G);cost=s.defect+4*s.degree;}
        int style=rng()%10;Bits v,w;
        if(style<6){
            int weight=style==0?6:4;Bits u=0;while(pop(u)<weight)u^=randbit();
            v=act(G,u);w=u^v;
        }else{
            // Generate short independent words in the two orthogonal constituents.
            auto choose=[&](bool image){
                Bits z=0;int wt=100;
                for(int q=0;q<20;q++){
                    int a=image?1+(rng()%3):2+2*(rng()%2);
                    Bits y=proj(image,a);int d=pop(y);if(d>1&&d<wt){wt=d;z=y;}
                }return z;
            };
            v=choose(true);w=choose(false);
        }
        if(!v||!w||v==w)continue;
        if(pop(v& w)%2||pop(w)%2||pop(v)%2)abort();
        auto H=toggle(G,v,w);auto s=score(H);int next=s.defect+4*s.degree;
        double T=20.+125.*(1.-(t%20000)/20000.);
        if(next>cost && (double)rng()/4294967296.>=exp((cost-next)/T))continue;
        G=H;cost=next;accepted++;
        if(s.defect<best){
            best=s.defect;bestG=G;save(G,argv[2]);
            if(!best)break;
        }
    }
    auto last=score(bestG);cout<<"initial exact defect "<<first.defect<<" best "<<best<<" squared degree error "<<last.degree<<" violated upper triangular entries "<<last.miss<<" accepted "<<accepted<<endl;
}
