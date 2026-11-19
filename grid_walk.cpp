// Exact optimization of one intergrid matching or one internal grid at a time.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <set>
#include <vector>
using namespace std;
constexpr int n=11,q=9;using Perm=array<uint8_t,q>;using Mat=array<array<int,q>,q>;
struct Construction{
    Perm P[n][n];int R[q][q]{};Mat E[n][n]{};vector<Perm> permutations,frames;
    vector<int> overlap;mt19937 rng;
    Construction(int seed):rng(seed){
        Perm f; iota(f.begin(),f.end(),0);set<uint64_t> orbits;
        for(int x=0;x<q;x++)for(int z=0;z<q;z++)R[x][z]=x!=z&&(x/3==z/3||x%3==z%3);
        do{
            permutations.push_back(f);int a=0,t=0;uint64_t code=0;
            for(int i=0;i<q;i++)for(int j=0;j<i;j++,t++)if(R[f[i]][f[j]]){code|=1ULL<<t;a+=2*R[i][j];}
            overlap.push_back(a);if(orbits.insert(code).second)frames.push_back(f);
        }while(next_permutation(f.begin(),f.end()));
        for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){shuffle(f.begin(),f.end(),rng);setmap(i,j,f);}
    }
    void setmap(int i,int j,const Perm &f){P[i][j]=f;for(int x=0;x<q;x++)P[j][i][f[x]]=x;}
    int score(){
        int s=0;
        for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){
            for(int x=0;x<q;x++)for(int y=0;y<q;y++){
                int v=(P[i][j][x]==y)-2+R[x][P[j][i][y]]+R[P[i][j][x]][y];
                for(int k=0;k<n;k++)if(k!=i&&k!=j)v+=(P[k][j][P[i][k][x]]==y);
                E[i][j][x][y]=E[j][i][y][x]=v;s+=v*v;
            }
        }
        return s;
    }
    Mat linear(int i,int j){
        Mat C{},A{};
        for(int x=0;x<q;x++)for(int y=0;y<q;y++)
            A[x][y]=E[i][j][x][y]-(P[i][j][x]==y)-R[x][P[j][i][y]]-R[P[i][j][x]][y];
        for(int x=0;x<q;x++)for(int y=0;y<q;y++){
            int c=A[x][y];
            for(int z=0;z<q;z++)c+=R[x][z]*A[z][y]+R[z][y]*A[x][z];
            for(int k=0;k<n;k++)if(k!=i&&k!=j){
                c+=E[i][k][x][P[j][k][y]]-(P[i][j][x]==y);
                c+=E[j][k][y][P[i][k][x]]-(P[i][j][x]==y);
            }
            C[x][y]=c;
        }return C;
    }
    int val(const Mat&C,const Perm&f,int ov){
        int z=ov;for(int x=0;x<q;x++)z+=C[x][f[x]];return z;
    }
    int overlap_of(const Perm&f){
        int z=0;for(int x=0;x<q;x++)for(int y=0;y<q;y++)z+=R[x][y]*R[f[x]][f[y]];return z;
    }
    bool matching(int i,int j,int how,int temperature){
        Mat C=linear(i,j);Perm old=P[i][j],best=old;
        int oldval=val(C,old,overlap_of(old)),bestval=oldval,noise=0;
        Mat noisy=C;
        if(temperature)for(auto &row:noisy)for(int &z:row)z+=int(rng()%(2*temperature+1))-temperature;
        bestval=val(noisy,best,overlap_of(best));
        int ties=1;
        if(!how){
            for(int u=0;u<(int)permutations.size();u++){
                auto &f=permutations[u];int z=val(noisy,f,overlap[u]);
                if(z<bestval){best=f;bestval=z;ties=1;}
                else if(z==bestval&&rng()%(++ties)==0)best=f;
            }
        }else{
            for(int a=0;a<q;a++)for(int b=0;b<a;b++){
                Perm f=old;swap(f[a],f[b]);int z=val(noisy,f,overlap_of(f));
                if(z<bestval){best=f;bestval=z;ties=1;}
                else if(z==bestval&&rng()%(++ties)==0)best=f;
            }
        }
        if(old==best)return false;
        setmap(i,j,best);
        return true;
    }
    bool orient(int i,int temp){
        Mat W{};
        for(int x=0;x<q;x++)for(int y=0;y<q;y++){
            for(int j=0;j<n;j++)if(i!=j)W[x][y]+=E[i][j][x][P[i][j][y]]-R[x][y];
            if(temp)W[x][y]+=int(rng()%(2*temp+1))-temp;
        }
        int best=1<<30,ties=0;Perm f{};
        for(auto &g:frames){
            int z=0;for(int x=0;x<q;x++)for(int y=0;y<q;y++)z+=W[x][y]*R[g[x]][g[y]];
            if(z<best){best=z;f=g;ties=1;}
            else if(z==best&&rng()%(++ties)==0)f=g;
        }
        // Change the internal grid and then relabel it canonically. Old vertex x receives new index f[x].
        for(int j=0;j<n;j++)if(i!=j){Perm t;for(int x=0;x<q;x++)t[f[x]]=P[i][j][x];setmap(i,j,t);}
        return true;
    }
    void audit(){
        int initial=score();
        for(int it=0;it<40;it++){
            int i=rng()%n,j=rng()%n;if(i==j){it--;continue;}
            auto old=P[i][j],f=permutations[rng()%permutations.size()];Mat c=linear(i,j);
            int expected=2*(val(c,f,overlap_of(f))-val(c,old,overlap_of(old)));
            setmap(i,j,f);int after=score();if(after-initial!=expected)abort();initial=after;
        }
        for(int i=0;i<n;i++){orient(i,0);int a=score();if(a>initial)abort();initial=a;}
    }
    void save(const char*out){ofstream f(out);for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){for(int a:P[i][j])f<<a<<' ';f<<'\n';}}
};
int main(int argc,char**argv){
    if(argc!=4)return 2;
    int seed=atoi(argv[1]),rounds=atoi(argv[2]);Construction c(seed);c.audit();int best=c.score(),stale=0;
    vector<pair<int,int>> pairs;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)pairs.emplace_back(i,j);
    for(int step=0;step<rounds;step++){
        shuffle(pairs.begin(),pairs.end(),c.rng);int past=best;
        int noise=stale%10==9?8:(stale%4==3?2:0);
        for(auto [i,j]:pairs){c.matching(i,j,step%5!=0,noise);int now=c.score();if(now<best){best=now;c.save(argv[3]);}}
        for(int i=0;i<n;i++){c.orient(i,noise/2);int now=c.score();if(now<best){best=now;c.save(argv[3]);}}
        if(!best)break;stale=best<past?0:stale+1;
        if(step%20==0)cout<<step<<" minimum squared cross-pair defect "<<best<<endl;
    }
    cout<<"final "<<best<<endl;
}
