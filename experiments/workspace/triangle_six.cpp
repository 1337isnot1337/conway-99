// Locally cyclic order-six triangle interfaces with a general residual graph.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace std;
using Mask=uint64_t;
using Dist=array<int,24>;
int rotate12(int x,int s){return x/6*6+(x+s)%6;}
int turn(int x){return x/6*6+(x+3)%6;}
Mask rot(Mask x,int s){
    Mask y=0;for(int i=0;i<6;i++){unsigned v=(x>>(6*i))&63;y|=Mask((v<<s|v>>(6-s))&63)<<(6*i);}return y;
}
int cls(int x,int y){return (x/6*2+y/6)*6+(y-x+12)%6;}
struct Step{
    int i,j;array<int,4> d,e{};Mask word=0;array<Mask,6> translates{};
};
bool consume(Dist& v,array<int,4> const&d){
    bool ok=true;for(int h:d)if(--v[h]<0)ok=false;return ok;
}
bool fits(Dist const& v,array<int,4> const&d){
    for(int i=0;i<4;i++){int need=1;for(int j=0;j<i;j++)need+=(d[j]==d[i]);if(v[d[i]]<need)return false;}return true;
}
struct Search{
    int g[39][39]{},M[39][39]{},limit,cap;vector<Mask> edges;long long paired=0,inc=0;
    array<array<vector<Step>,10>,3> options;array<Dist,3> goals;
    array<Step,10> first,second;ostream &out;
    Search(int swap,int a,int b,int l,int c,ostream &o):limit(l),cap(c),out(o){
        auto join=[&](int i,int j){g[i][j]=g[j][i]=1;};
        join(0,1);join(1,2);join(0,2);
        for(int i=0;i<12;i++){
            for(int h=0;h<3;h++){join(h,3+12*h+i);join(3+12*h+i,3+12*h+turn(i));}
            join(3+i,15+i);join(3+i,27+i);
            join(15+i,27+6*(swap^i/6)+(i+(i/6?b:a))%6);
        }
        for(int i=0;i<39;i++)for(int j=0;j<39;j++){
            int k=(i==j?12:0)+2-g[i][j];for(int h=0;h<39;h++)k-=g[i][h]*g[h][j];M[i][j]=k;
        }
        for(int i=0;i<12;i++)for(int j=0;j<i;j++)if(j!=turn(i)){
            Mask e=(Mask(1)<<i)|(Mask(1)<<j);bool least=true;
            for(int s=1;s<6;s++)if(rot(e,s)<=e)least=false;
            if(least)edges.push_back(e);
        }
        assert(edges.size()==10);
        for(int pair=0;pair<3;pair++){
            int f=pair==2?1:0,h=pair==0?1:2;
            for(int x=0;x<12;x++)for(int y=0;y<12;y++)goals[pair][cls(x,y)]=M[3+12*f+x][3+12*h+y];
            for(int i=0;i<10;i++)for(int j=0;j<10;j++)for(int s=0;s<6;s++){
                Mask e=edges[i],v=rot(edges[j],s);Step op;op.i=i;op.j=j;op.word=v;
                int k=0;for(Mask x=e;x;x&=x-1)for(Mask y=v;y;y&=y-1)op.d[k++]=cls(countr_zero(x),countr_zero(y));
                if(fits(goals[pair],op.d))options[pair][i].push_back(op);
            }
        }
    }
    void extend(const array<vector<Step>,10>& opt,bool last,unsigned todo,unsigned used,Dist a,Dist b,vector<Mask>&placed){
        if((!last&&paired>=limit)||inc>=cap)return;
        if(!todo){
            if(!last){paired++;complete();return;}
            inc++;for(auto &z:second)out<<z.word<<' ';out<<'\n';return;
        }
        int best=-1;vector<const Step*> top;
        for(unsigned t=todo;t;t&=t-1){
            int i=countr_zero(t);vector<const Step*> next;
            for(auto &op:opt[i]){
                if((used>>op.j&1)||!fits(a,op.d))continue;
                if(last){
                    if(!fits(b,op.e))continue;
                    bool ok=true;
                    for(auto x:placed)for(auto y:op.translates)if(popcount(x&y)>2){ok=false;break;}
                    if(!ok)continue;
                }
                next.push_back(&op);
            }
            if(next.empty())return;
            if(best<0||next.size()<top.size()){best=i;top.swap(next);}
        }
        for(auto ptr:top){
            auto &op=*ptr;Dist aa=a,bb=b;consume(aa,op.d);if(last)consume(bb,op.e);
            (last?second:first)[best]=op;if(last)placed.push_back(op.word);
            extend(opt,last,todo^(1<<best),used|(1<<op.j),aa,bb,placed);
            if(last)placed.pop_back();if((!last&&paired>=limit)||inc>=cap)return;
        }
    }
    virtual void complete(){
        array<vector<Step>,10> choices;
        for(int i=0;i<10;i++){
            for(auto &ab:options[1][i]){
                Step op=ab;Mask a=edges[i],b=first[i].word,c=op.word;int k=0;
                for(Mask x=b;x;x&=x-1)for(Mask y=c;y;y&=y-1)op.e[k++]=cls(countr_zero(x),countr_zero(y));
                if(!fits(goals[2],op.e))continue;
                Mask w=a|(b<<12)|(c<<24);bool ok=true;
                for(int h=0;h<36;h++){
                    int n=(w>>h)&1;for(Mask x=w;x;x&=x-1)n+=g[3+h][3+countr_zero(x)];
                    if(n>2)ok=false;
                }
                for(int s=0;s<6;s++){
                    op.translates[s]=rot(w,s);if(s&&popcount(w&op.translates[s])>2)ok=false;
                }
                if(ok){op.word=w;choices[i].push_back(op);}
            }
            if(choices[i].empty())return;
        }
        vector<Mask> used;extend(choices,true,1023,0,goals[1],goals[2],used);
    }
    void run(){
        for(auto g:goals)for(auto x:g)if(x<0)return;
        vector<Mask> p;extend(options[0],false,1023,0,goals[0],{},p);
    }
};
#ifndef TRIANGLE_SIX_LIBRARY
int main(int argc,char**argv){
    if(argc!=7)return 2;ofstream out(argv[6]);
    Search s(atoi(argv[1]),atoi(argv[2]),atoi(argv[3]),atoi(argv[4]),atoi(argv[5]),out);s.run();
    cout<<"pair interfaces "<<s.paired<<" complete 39-star incidences "<<s.inc<<endl;
}

#endif
