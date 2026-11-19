// Test all sign refinements on the six pages of an unsigned local color-cycle quotient.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>
using namespace std;using Mask=unsigned;
struct Sign {
    int word[20][6]{},index,maxfound;Mask group[6][6][3]{},delta[6][20][3]{},selected[6]{};
    Mask equal[20]{}; array<vector<Mask>,6>dom;long long nodes=0,limit;int found=0;ostream&out;
    Sign(int i,int f,long long l,ostream&o):index(i),maxfound(f),limit(l),out(o){}
    void prepare(){
        for(int i=0;i<6;i++)for(int j=0;j<6;j++)for(int r=0;r<20;r++)
            group[i][j][(word[r][i]-word[r][j]+3)%3]|=1<<r;
        for(int i=0;i<6;i++)for(int r=0;r<20;r++)for(int s=0;s<20;s++)if(r!=s)delta[i][r][(word[r][i]-word[s][i]+3)%3]|=1<<s;
        for(int r=0;r<20;r++)for(int z=0;z<20;z++){
            bool same=true;for(int i=0;i<6;i++)if(word[r][i]!=word[z][i])same=false;
            if(same)equal[r]|=1<<z;
        }
        for(int i=0;i<6;i++){
            for(Mask s=1023;s<(1<<20);){
                if(s&1){
                    bool ok=true;for(int j=0;j<6;j++)for(auto m:group[i][j])if(2*popcount(s&m)!=popcount(m))ok=false;
                    if(ok)for(int z=0;z<20;z++){
                        int n=popcount(equal[z]),a=popcount(s&equal[z]);
                        if((n==4&&a!=2)||(n==3&&(a==0||a==3)))ok=false;
                    }
                    if(ok)dom[i].push_back(s);
                }
                Mask l=s&-s,h=s+l;s=h|(((h^s)>>2)/l);
            }
        }
    }
    using Count=array<array<Mask,3>,20>;
    void dfs(Mask left,const array<vector<Mask>,6>&D,const Count&one,const Count&two){
        if(nodes++>=limit||found>=maxfound)return;
        if(!left){out<<index;for(auto t:selected)out<<' '<<t;out<<endl;found++;return;}
        int i=-1;for(Mask a=left;a;a&=a-1){int j=countr_zero(a);if(i<0||D[j].size()<D[i].size())i=j;}
        unsigned past=63^left;
        Mask predecessors[20]{};
        for(int r=1;r<20;r++){
            Mask a=equal[r]&((1u<<r)-2);
            for(Mask m=past;m;m&=m-1){auto v=selected[countr_zero(m)];a&=(v>>r&1)?v:~v;}
            predecessors[r]=a;
        }
        left^=1<<i;
        for(auto v:D[i]){
            bool ordered=true;
            for(Mask a=v;a;a&=a-1)if(predecessors[countr_zero(a)]&~v){ordered=false;break;}
            if(!ordered)continue;
            bool ok=true;auto c=one,t=two;
            for(int r=0;r<20&&ok;r++){
                Mask m=(v>>r&1)?v:((1<<20)-1)^v;
                for(int d=0;d<3;d++){Mask b=delta[i][r][d]&m;if(b&t[r][d]){ok=false;break;}t[r][d]|=b&c[r][d];c[r][d]|=b;}
            }
            if(!ok)continue;
            array<vector<Mask>,6> next;
            for(Mask a=left;a;a&=a-1){
                int j=countr_zero(a);
                for(auto w:D[j]){
                    Mask both=v&w;bool valid=true;for(auto m:group[i][j])if(4*popcount(both&m)!=popcount(m))valid=false;
                    if(valid)next[j].push_back(w);
                }
                if(next[j].empty()){ok=false;break;}
            }
            if(ok){selected[i]=v;dfs(left,next,c,t);}
            if(nodes>=limit||found>=maxfound)return;
        }
    }
};
int main(int argc,char**argv){
    if(argc!=5)return 2;ifstream in(argv[1]);ofstream out(argv[2]);int idx=0;
    while(true){
        Sign s(idx,atoi(argv[4]),atoll(argv[3]),out);
        if(!(in>>s.word[0][0]))break;
        for(int k=1;k<120;k++)in>>s.word[k/6][k%6];
        s.prepare();s.dfs(63,s.dom,{},{});
        cout<<idx++<<" "<<s.nodes<<" "<<s.found<<" "<<*min_element(s.selected,s.selected+6)<<" domains";for(auto &d:s.dom)cout<<" "<<d.size();cout<<endl;
    }
}
