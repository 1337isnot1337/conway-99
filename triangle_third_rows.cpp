// Select twelve compatible ten-row neighborhoods for the third fiber of a fixed two-fiber design.
#define COCLIQUE_ROWS_LIBRARY
#include "coclique_rows.cpp"
#include <bit>
#include <cassert>
using Mask=uint64_t;
struct Solver {
    int t;long long nodes=0,limit;vector<Mask> choice,dom[12];vector<unsigned> block;int allowed[60][12]{};
    Solver(int t,long long lim):t(t),limit(lim),choice(12){}
    bool adj(int a,int b){
        if(a>b)swap(a,b);
        if(a/12==b/12)return (b-a)==6;
        if(a/12==1&&b/12==2)return (a+t)%12==b%12;
        return a%12==b%12;
    }
    int cap(int i,int j){
        int r=2-adj(i,j)-int(i/12==j/12);
        for(int k=0;k<36;k++)r-=adj(i,k)&&adj(j,k);return r;
    }
    bool valid(unsigned long long m){
        for(int i=0;i<36;i++){
            int d=(m>>i)&1;
            for(auto a=m;a;a&=a-1)d+=adj(i,countr_zero(a));
            if(d>2)return false;
        }
        for(auto a=m;a;a&=a-1)for(auto b=a&(a-1);b;b&=b-1)if(cap(countr_zero(a),countr_zero(b))<=0)return false;
        return true;
    }
    bool prepare(){
        for(int r=0;r<60;r++)for(int i=0;i<12;i++)for(int j=0;j<i;j++)if(i-j!=6&&valid(block[r]|(1ull<<(24+i))|(1ull<<(24+j)))){
            allowed[r][i]|=1<<j;allowed[r][j]|=1<<i;
        }
        Enumerator e;e.block=block;e.n=60;e.h=24;e.prepare();
        array<int,32>need{};Bits avail=((Bits)1<<60)-1;
        for(int h=0;h<24;h++){
            need[h]=cap(24,h);if(need[h]<0)return false;if(!need[h])avail&=~e.point[h];
        }
        for(int r=0;r<60;r++)if(!allowed[r][0])avail&=~((Bits)1<<r);
        e.visit(0,avail,need,10);
        for(auto a:e.output){
            for(int s=0;s<12;s++){
                Mask b=0;
                for(int g=0;g<5;g++){
                    Mask part=(a>>(12*g))&4095;b|=((part<<s|part>>(12-s))&4095)<<(12*g);
                }
                dom[s].push_back(b);
            }
        }
        return true;
    }
    bool compat(int i,int j,Mask u,Mask v){
        Mask m=u&v;if((i-j+12)%12==6)return !m;
        return m&&!(m&(m-1))&&(allowed[countr_zero(m)][i]>>j&1);
    }
    bool dfs(unsigned left,const vector<vector<int>>&options){
        if(!left)return true;
        if(++nodes>limit)return false;
        int i=-1;for(unsigned a=left;a;a&=a-1){int j=countr_zero(a);if(i<0||options[j].size()<options[i].size())i=j;}
        left^=1u<<i;
        for(int u:options[i]){
            vector<vector<int>> next(12);bool ok=true;
            for(unsigned a=left;a;a&=a-1){int j=countr_zero(a);
                for(int v:options[j])if(compat(i,j,dom[i][u],dom[j][v]))next[j].push_back(v);
                if(next[j].empty()){ok=false;break;}
            }
            if(ok){choice[i]=dom[i][u];if(dfs(left,next))return true;}
            if(nodes>limit)return false;
        }
        return false;
    }
    bool run(){
        if(!prepare()||dom[0].empty())return false;
        vector<vector<int>> opt(12);for(int i=0;i<12;i++)for(int j=0;j<(int)dom[i].size();j++)opt[i].push_back(j);
        return dfs(4095,opt);
    }
};
int main(int argc,char**argv){
    if(argc!=5)return 2;ifstream in(argv[1]);ofstream out(argv[2]),log(argv[3]);long long lim=atoll(argv[4]);
    int t,idx;while(in>>t>>idx){
        Solver s(t,lim);s.block.resize(60);for(auto &v:s.block)in>>v;
        bool ok=s.run();log<<t<<' '<<idx<<' '<<s.dom[0].size()<<' '<<s.nodes<<' '<<(ok?"found":s.nodes>lim?"limit":"excluded")<<endl;
        if(ok){out<<t<<' '<<idx;for(auto a:s.choice)out<<' '<<a;out<<endl;}
    }
}
