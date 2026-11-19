// Develop six 6-subsets on three copies of Z/11, with triples as point groups.
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
#include <set>
using namespace std;
using Block=array<int,6>;using Family=array<Block,6>;
int delta(int x,int y){
    if(x>y)swap(x,y);int a=x/11,b=y/11,d=(y%11-x%11+11)%11;assert(d);
    if(a==b)return 5*a+min(d,11-d)-1;
    return 15+10*(a==0?b-1:2)+d-1;
}
int main(int argc,char**argv){
    if(argc!=5)return 2;
    int epochs=atoi(argv[2]),seed=atoi(argv[3]),type=atoi(argv[4]);
    array<array<array<int,3>,6>,5> shape={{
        {{{0,2,4},{1,3,2},{2,4,0},{3,1,2},{3,1,2},{3,1,2}}},
        {{{0,2,4},{1,4,1},{2,2,2},{3,0,3},{3,2,1},{3,2,1}}},
        {{{0,2,4},{2,2,2},{2,2,2},{2,2,2},{2,4,0},{4,0,2}}},
        {{{0,3,3},{1,2,3},{2,3,1},{3,0,3},{3,1,2},{3,3,0}}},
        {{{1,1,4},{1,2,3},{1,4,1},{2,3,1},{3,1,2},{4,1,1}}}}};
    mt19937 rng(seed);Family F{},best{};int bestScore=999,found=0;
    ofstream out(argv[1]);set<array<uint64_t,6>> seen;
    auto coin=[&](){return generate_canonical<double,32>(rng);};
    for(int ep=0;ep<epochs;ep++){
        int freq[45]{};int score=0;
        for(int i=0;i<6;i++){
            array<int,11> points;iota(points.begin(),points.end(),0);shuffle(points.begin(),points.end(),rng);int q=0;
            for(int c=0;c<3;c++)for(int t=0;t<shape[type][i][c];t++){F[i][q]=11*c+points[q];q++;}
        }
        if(ep&&rng()%3!=0)F=best;
        for(auto &r:F)for(int a=0;a<6;a++)for(int b=0;b<a;b++)freq[delta(r[a],r[b])]++;
        for(int f:freq)score+=(f-2)*(f-2);
        for(int step=0;step<9000;step++){
            int i=rng()%6,j=rng()%6;auto &r=F[i];int next=11*(r[j]/11)+rng()%11,other=-1;
            for(int k=0;k<6;k++)if(r[k]%11==next%11)other=k;
            if(other==j||(other>=0&&r[other]/11==r[j]/11))continue;
            Block t=r;t[j]=next;if(other>=0)t[other]=11*(r[other]/11)+r[j]%11;
            int touched[24],change[24],n=0;int previous=score;
            auto edit=[&](int d,int v){score+=2*v*(freq[d]-2)+1;freq[d]+=v;touched[n]=d;change[n++]=v;};
            for(int a=0;a<6;a++)for(int b=0;b<a;b++)if(a==j||b==j||a==other||b==other){
                edit(delta(r[a],r[b]),-1);edit(delta(t[a],t[b]),1);
            }
            double T=1.05*pow(.075,double(step)/9000);
            if(score>previous&&coin()>exp((previous-score)/T)){
                for(int z=0;z<n;z++)freq[touched[z]]-=change[z];score=previous;continue;
            }
            r=t;
            if(score<bestScore){bestScore=score;best=F;cout<<"epoch "<<ep<<" imbalance "<<score<<endl;}
            if(!score){
                array<uint64_t,6> rec;array<uint64_t,66> words{};bool good=true;
                for(int q=0;q<6;q++){
                    for(int sh=0;sh<11;sh++)for(int x:F[q])words[q*11+sh]|=uint64_t(1)<<(11*(x/11)+(x%11+sh)%11);
                    rec[q]=*min_element(words.begin()+11*q,words.begin()+11*(q+1));
                }
                for(int a=0;a<66;a++)for(int b=0;b<a;b++)if(popcount(words[a]&words[b])>2)good=false;
                sort(rec.begin(),rec.end());if(good&&seen.insert(rec).second){for(auto m:rec)out<<m<<' ';out<<endl;found++;}
                break;
            }
        }
    }
    cout<<"verified incidence designs "<<found<<" minimum discrepancy "<<bestScore<<endl;
}
