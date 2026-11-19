// Extend fully specified neighborhoods by exact bounded multicover, retaining pair quotas.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
#include <vector>
using namespace std;
using Bits=unsigned __int128;
Bits bit(int i){return (Bits)1<<i;}
int low(Bits x){return (uint64_t)x?__builtin_ctzll((uint64_t)x):64+__builtin_ctzll((uint64_t)(x>>64));}
int pop(Bits x){return __builtin_popcountll((uint64_t)x)+__builtin_popcountll((uint64_t)(x>>64));}
struct Search{
    int n,k,cap,limit,nodes=0,best=0;
    mt19937 rng;
    array<Bits,100> banned{},answer{};
    Bits all;
    bool twins=true;
    struct State{
        array<Bits,100> known{},signature{},positive{},once{},twice{},eligible{},conflict{},twins{};
        Bits core,outer;
    };
    void rows(const State &s,int x,Bits selected,Bits available,Bits need1,Bits need2,int slots,vector<Bits>&output){
        if((int)output.size()>=cap||slots<0||pop(available)<slots)return;
        if(!(need1|need2)){
            for(Bits m=available;m;m&=m-1)if(s.signature[low(m)])available&=~bit(low(m));
            if(pop(available)<slots)return;
            if(twins){
                while(slots--){int v=low(available);selected|=bit(v);available&=available-1;}
                output.push_back(selected);
            }else if(!slots)output.push_back(selected);
            else{
                for(Bits m=available;m;m&=m-1){
                    int j=low(m);rows(s,x,selected|bit(j),(m&(m-1))&~s.conflict[j],0,0,slots-1,output);
                    if((int)output.size()>=cap)return;
                }
            }
            return;
        }
        if(!slots)return;
        int bestWays=100000,b=-1;
        for(Bits m=need1|need2;m;m&=m-1){
            int i=low(m),a=pop(available&s.known[i]),r=(need2&bit(i))?2:1;
            if(a<r)return;int ways=r==1?a:a*(a-1)/2;
            if(ways<bestWays){b=i;bestWays=ways;}
        }
        Bits active=available&s.known[b];available&=~active;
        for(Bits m=active;m;m&=m-1){
            int j=low(m);if(twins&&(s.twins[j]&active&(bit(j)-1)))continue;
            Bits sj=s.signature[j],zero=sj&need1,next1=(need1&~sj)|(need2&sj),next2=need2&~sj;
            Bits avail=available&~s.conflict[j];
            for(Bits z=zero;z;z&=z-1)avail&=~s.known[low(z)];
            if(need1&bit(b)){
                rows(s,x,selected|bit(j),avail,next1,next2,slots-1,output);
            }else{
                for(Bits w=(m&(m-1))&~s.conflict[j];w;w&=w-1){
                    int l=low(w);if(twins&&(s.twins[l]&active&~bit(j)&(bit(l)-1)))continue;
                    Bits sl=s.signature[l];if(sl&~(next1|next2))continue;
                    Bits alt=avail&~s.conflict[l];
                    for(Bits z=sl&next1;z;z&=z-1)alt&=~s.known[low(z)];
                    rows(s,x,selected|bit(j)|bit(l),alt,(next1&~sl)|(next2&sl),next2&~sl,slots-2,output);
                    if((int)output.size()>=cap)return;
                }
            }
            if((int)output.size()>=cap)return;
        }
    }
    bool visit(State &s){
        if(nodes>=limit)return false;
        nodes++;best=max(best,pop(s.core));
        if(!s.outer){
            for(int i=0;i<n;i++)for(int j=0;j<=i;j++){
                if(((s.known[i]>>j)&1)!=((s.known[j]>>i)&1))abort();
                int t=pop(s.known[i]&s.known[j]);if(t!=(i==j?k:2-(int)((s.known[i]>>j)&1)))abort();
            }
            answer=s.known;return true;
        }
        for(Bits z=s.outer;z;z&=z-1){
            int i=low(z);s.signature[i]=s.known[i]&s.core;s.once[i]=s.twice[i]=s.eligible[i]=s.conflict[i]=s.twins[i]=0;
            for(Bits h=s.core;h;h&=h-1){
                int j=low(h),v=2-(int)((s.signature[i]>>j)&1)-pop(s.signature[i]&s.known[j]);
                if(v<0)return false;
                if(v==1)s.once[i]|=bit(j);if(v==2)s.twice[i]|=bit(j);
            }
            s.positive[i]=s.once[i]|s.twice[i];
        }
        for(Bits a=s.outer;a;a&=a-1){
            int i=low(a);
            for(Bits b=a&(a-1);b;b&=b-1){
                int j=low(b),v=pop(s.signature[i]&s.signature[j]);
                if(twins&&s.signature[i]==s.signature[j]){s.twins[i]|=bit(j);s.twins[j]|=bit(i);}
                if(v>2)return false;
                if(v==2){s.conflict[i]|=bit(j);s.conflict[j]|=bit(i);continue;}
                if((banned[i]&bit(j))||(s.signature[i]&~s.positive[j])||(s.signature[j]&~s.positive[i]))continue;
                s.eligible[i]|=bit(j);s.eligible[j]|=bit(i);
            }
        }
        vector<pair<int,int>> candidates;
        for(Bits m=s.outer;m;m&=m-1){
            int i=low(m),slack=pop(s.eligible[i])-k+pop(s.signature[i]);if(slack<0)return false;
            int tight=99;
            for(Bits t=s.positive[i];t;t&=t-1){
                int j=low(t),c=pop(s.eligible[i]&s.known[j])-1-(int)((s.twice[i]>>j)&1);
                if(c<0)return false;tight=min(tight,c);
            }
            candidates.push_back({tight*5+slack,i});
        }
        sort(candidates.begin(),candidates.end());int x=-1;vector<Bits> chosen;
        for(auto [score,i]:candidates){
            vector<Bits> result;
            rows(s,i,0,s.eligible[i],s.once[i],s.twice[i],k-pop(s.signature[i]),result);
            if(result.empty())return false;
            if(x<0||result.size()<chosen.size()){x=i;chosen=move(result);}
        }
        shuffle(chosen.begin(),chosen.end(),rng);
        for(Bits v:chosen){
            if(nodes>=limit)break;
            State child=s;child.outer^=bit(x);child.core|=bit(x);child.known[x]|=v;
            for(Bits a=v;a;a&=a-1)child.known[low(a)]|=bit(x);
            if(visit(child))return true;
        }
        return false;
    }
};
int main(int argc,char**argv){
    if(argc!=6)return 2;
    ifstream f(argv[1]);Search e;int c;f>>e.n>>e.k>>c;
    if(e.n>99||!f)return 3;
    e.all=bit(e.n)-1;e.limit=atoi(argv[3]);e.cap=atoi(argv[4]);e.rng.seed(atoi(argv[5]));
    Search::State s{};s.core=bit(c)-1;s.outer=e.all^s.core;
    for(int i=0;i<e.n;i++)for(int j=0;j<e.n;j++){
        int v;f>>v;if(v==1)s.known[i]|=bit(j);if(v<0){e.banned[i]|=bit(j);e.twins=false;}
    }
    bool ok=e.visit(s);cout<<"search nodes "<<e.nodes<<" deepest complete neighborhoods "<<e.best<<" graph "<<ok<<endl;
    if(ok){ofstream out(argv[2]);for(int i=0;i<e.n;i++){for(int j=0;j<e.n;j++)out<<(int)((e.answer[i]>>j)&1)<<' ';out<<'\n';}}
}
