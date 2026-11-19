// Complete the third triangle fiber with its internal matching and its incidence rows free.
#define COCLIQUE_ROWS_LIBRARY
#include "coclique_rows.cpp"
#include <bit>
#include <cassert>
using Mask=uint64_t;
struct MatchChoice{int i,j;Mask a,b;};
struct Finish {
    array<Mask,36> near{};int need[12][24]{},bases[60][12]{};
    vector<unsigned> block;vector<MatchChoice> options;
    array<Mask,12> solution{};array<int,12> mate{};long long nodes=0,limit;int numpairs=0;
    Finish(const vector<unsigned>&data,const array<Mask,36>&adj,long long budget):near(adj),block(data),limit(budget){
        for(int i=0;i<12;i++)for(int h=0;h<24;h++)
            need[i][h]=2-((near[24+i]>>h)&1)-popcount(near[h]&near[24+i]);
        for(int i=0;i<60;i++)for(int c=0;c<12;c++)bases[i][c]=popcount(Mask(block[i])&near[24+c]);
    }
    void add_edge(int i,int j,vector<Mask>&d,Enumerator&e){
        array<int,32> n{};Bits available=((Bits)1<<60)-1;
        for(int h=0;h<24;h++){
            n[h]=need[i][h]-int((near[24+j]>>h)&1);
            if(n[h]<0)return;if(!n[h])available&=~e.point[h];
        }
        for(int r=0;r<60;r++){
            bool ok=bases[r][i]<=1&&bases[r][j]<=1;
            for(int h=0;h<24&&ok;h++)if((near[h]>>(24+i))&1){
                if(popcount(Mask(block[r])&near[h])+int((block[r]>>h)&1)>=2)ok=false;
            }
            if(!ok)available&=~((Bits)1<<r);
        }
        e.output.clear();e.visit(0,available,n,10);
        for(auto m:e.output)d.push_back((Mask)m);
    }
    bool local(int r,int i,int j,int k,int l){
        Mask s=Mask(block[r])|(Mask(1)<<(24+i))|(Mask(1)<<(24+k));
        for(int h=0;h<24;h++)if(popcount(near[h]&s)+int((s>>h)&1)>2)return false;
        for(int h=0;h<12;h++)if(bases[r][h]+(h==i||h==j||h==k||h==l)>2)return false;
        return true;
    }
    bool compatible(const MatchChoice &a,const MatchChoice &b){
        int i[]={a.i,a.j},j[]={b.i,b.j};Mask u[]={a.a,a.b},v[]={b.a,b.b};
        for(int h=0;h<2;h++)for(int k=0;k<2;k++){
            Mask meet=u[h]&v[k];if(!has_single_bit(meet))return false;
            if(!local(countr_zero(meet),i[h],i[1-h],j[k],j[1-k]))return false;
        }
        return true;
    }
    bool dfs(unsigned left,const vector<int>&pool){
        if(!left)return true;if(++nodes>limit)return false;
        array<vector<int>,12> sets;
        for(auto k:pool){sets[options[k].i].push_back(k);sets[options[k].j].push_back(k);}
        int h=-1;for(unsigned a=left;a;a&=a-1){int j=countr_zero(a);if(h<0||sets[j].size()<sets[h].size())h=j;}
        for(int k:sets[h]){
            auto e=options[k];unsigned rem=left^(1u<<e.i)^(1u<<e.j);vector<int> next;unsigned cover=0;
            for(int j:pool){auto&f=options[j];unsigned ids=(1u<<f.i)|(1u<<f.j);if((ids&rem)==ids&&compatible(e,f)){next.push_back(j);cover|=ids;}}
            if(cover!=rem)continue;
            solution[e.i]=e.a;solution[e.j]=e.b;mate[e.i]=e.j;mate[e.j]=e.i;
            if(dfs(rem,next))return true;if(nodes>limit)return false;
        }
        return false;
    }
    bool run(int symmetry=1){
        Enumerator e;e.block=block;e.h=24;e.n=60;e.prepare();
        vector<int> pool;
        bool seen_edge[12][12]{};
        auto step=[&](int i,int s){return i/symmetry*symmetry+(i+s)%symmetry;};
        auto shift=[&](Mask a,int s){
            Mask v=0;for(;a;a&=a-1)v|=Mask(1)<<step(countr_zero(a),s);
            return v;
        };
        for(int i=0;i<12;i++)for(int j=0;j<i;j++){
            if(seen_edge[i][j])continue;
            vector<int> spins;
            for(int s=0;s<symmetry;s++){
                int x=step(i,s),y=step(j,s);
                if(!seen_edge[x][y]){seen_edge[x][y]=seen_edge[y][x]=true;spins.push_back(s);}
            }
            vector<Mask>a,b;add_edge(i,j,a,e);if(a.empty())continue;
            add_edge(j,i,b,e);bool seen=false;
            for(auto x:a)for(auto y:b)if(!(x&y)){for(int s:spins){pool.push_back(options.size());options.push_back({step(i,s),step(j,s),shift(x,s),shift(y,s)});}seen=true;}
            numpairs+=seen;
        }
        return dfs(4095,pool);
    }
};
#ifndef TRIANGLE_MATE_LIBRARY
int main(int argc,char**argv){
    if(argc!=4)return 2;ifstream in(argv[1]);ofstream out(argv[2]),log(argv[3]);
    int t,idx;while(in>>t>>idx){
        vector<unsigned> block(60);for(auto &v:block)in>>v;array<Mask,36> adj{};
        auto edge=[&](int i,int j){adj[i]|=Mask(1)<<j;adj[j]|=Mask(1)<<i;};
        for(int i=0;i<12;i++){
            edge(i,(i+6)%12);edge(12+i,12+(i+6)%12);edge(i,12+i);edge(i,24+i);edge(12+i,24+(i+t)%12);
        }
        Finish s(block,adj,1000000);bool ok=s.run();log<<t<<' '<<idx<<' '<<s.numpairs<<' '<<s.options.size()<<' '<<s.nodes<<' '<<(ok?"found":s.nodes>s.limit?"limit":"excluded")<<endl;
        if(ok){out<<t<<' '<<idx;for(auto a:s.mate)out<<' '<<a;for(auto a:s.solution)out<<' '<<a;out<<endl;}
    }
}
#endif
