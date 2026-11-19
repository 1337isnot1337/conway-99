// Enumerate signless-incidence support possibilities for the non-grid pairs of axes.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <iostream>
using namespace std;
int main(){
    constexpr int full=(1<<21)-1;
    array<int,21>a,b,dis;int k=0;
    for(int i=0;i<7;i++)for(int j=i+1;j<7;j++){a[k]=i;b[k++]=j;}
    for(int e=0;e<21;e++){
        dis[e]=0;
        for(int f=0;f<e;f++)if(a[e]!=a[f]&&a[e]!=b[f]&&b[e]!=a[f]&&b[e]!=b[f])dis[e]|=1<<f;
    }
    static unsigned char bip[full+1];int minima[22],num[22]{};
    fill(minima,minima+22,999);
    for(int m=0;m<=full;m++){
        int adj[7]{};
        for(unsigned h=m;h;h&=h-1){int e=countr_zero(h);adj[a[e]]|=1<<b[e];adj[b[e]]|=1<<a[e];}
        int todo=127,bc=0;
        while(todo){
            int x=todo&-todo,left=x,right=0,seen=0;bool ok=true;
            while(x){
                seen|=x;int y=0;
                for(unsigned z=x;z;z&=z-1)y|=adj[countr_zero(z)];
                if(y&left)ok=false;
                swap(left,right);x=y&~seen;left|=x;
            }
            todo&=~seen;bc+=ok;
        }
        bip[m]=bc;
        bool keep=true;
        for(unsigned h=m;h;h&=h-1)if(bip[m^(h&-h)]>bc){keep=false;break;}
        if(!keep)continue;
        unsigned d=full^m;int e=popcount(d),t=0;
        for(unsigned h=d;h;h&=h-1)t+=popcount(d&dis[countr_zero(h)]);
        minima[e]=min(minima[e],t);num[e]++;
    }
    for(int i=0;i<22;i++)cout<<i<<" "<<minima[i]<<" "<<num[i]<<'\n';
}
