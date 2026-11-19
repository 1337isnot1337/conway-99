// Globally minimize the SRG error among all ways to redistribute one pair of adjacency rows.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>
using namespace std;
struct Fit{
    int n,k;vector<vector<int>> A,C;
    mt19937 rng;
    long long score(){
        C.assign(n,vector<int>(n,0));long long s=0;
        for(int i=0;i<n;i++)for(int j=i;j<n;j++){
            int c=0;for(int l=0;l<n;l++)c+=A[i][l]*A[j][l];C[i][j]=C[j][i]=c;
            if(i==j)assert(c==k);else{s+=(c+A[i][j]-2)*(c+A[i][j]-2);}
        }
        return s;
    }
    using Table=vector<vector<int>>;
    int fit(int u,int v,bool apply=true){
        vector<int>D,old;for(int i=0;i<n;i++)if(i!=u&&i!=v&&A[u][i]!=A[v][i]){D.push_back(i);old.push_back(2*A[u][i]-1);}
        int d=D.size();if(d<4)return 0;
        assert(d%2==0);int W[32][32]{},past=0;
        for(int i=0;i<d;i++)for(int j=0;j<i;j++){
            int t=2*(C[D[i]][D[j]]-int(old[i]==old[j])-2)+(3-2*A[u][v])*A[D[i]][D[j]];
            W[i][j]=W[j][i]=t;past+=t*old[i]*old[j];
        }
        array<int,4> b={0,d/3,(2*d)/3,d};array<vector<int>,3> energy;
        array<vector<vector<int>>,3> bycount;
        for(int p=0;p<3;p++){
            int s=b[p+1]-b[p];energy[p].resize(1<<s);bycount[p].resize(s+1);
            for(int mask=0;mask<(1<<s);mask++){
                for(int i=0;i<s;i++)for(int j=0;j<i;j++)energy[p][mask]+=W[b[p]+i][b[p]+j]*(((mask>>i^mask>>j)&1)?-1:1);
                bycount[p][popcount(unsigned(mask))].push_back(mask);
            }
        }
        auto cross=[&](int p,int q){
            int s=b[p+1]-b[p],t=b[q+1]-b[q];Table M(1<<s,vector<int>(1<<t));
            for(int a=0;a<(1<<s);a++){
                int field[16]{};
                for(int j=0;j<t;j++)for(int i=0;i<s;i++)field[j]+=W[b[p]+i][b[q]+j]*(a>>i&1?1:-1);
                M[a][0]=-accumulate(field,field+t,0);
                for(unsigned h=1;h<(1u<<t);h++)M[a][h]=M[a][h&(h-1)]+2*field[countr_zero(h)];
            }
            return M;
        };
        auto ab=cross(0,1),ac=cross(0,2),bc=cross(1,2);
        int best=past;array<int,3> win{};
        for(int i=0;i<(int)ac.size();i++)for(int j=0;j<(int)ac[i].size();j++)ac[i][j]+=energy[2][j];
        for(int a=1;a<(int)energy[0].size();a+=2)for(int c=0;c<(int)energy[1].size();c++){
            int req=d/2-popcount(unsigned(a))-popcount(unsigned(c));if(req<0||req>b[3]-b[2])continue;
            int start=energy[0][a]+energy[1][c]+ab[a][c];
            for(int e:bycount[2][req]){
                int val=start+ac[a][e]+bc[c][e];
                if(val<best){best=val;win={a,c,e};}
            }
        }
        if(apply&&best<past){
            for(int p=0;p<3;p++)for(int i=b[p];i<b[p+1];i++){
                int h=(win[p]>>(i-b[p]))&1;A[u][D[i]]=A[D[i]][u]=h;A[v][D[i]]=A[D[i]][v]=1-h;
            }
        }
        return best-past;
    }
};
int main(int argc,char**argv){
    if(argc!=6)return 2;
    Fit f;ifstream in(argv[1]);in>>f.n>>f.k;f.A.assign(f.n,vector<int>(f.n));
    for(auto&r:f.A)for(int &a:r)in>>a;
    f.rng.seed(atoi(argv[4]));int passes=atoi(argv[3]);vector<pair<int,int>> pairs;
    if(string(argv[5])=="all"){for(int i=0;i<f.n;i++)for(int j=0;j<i;j++)pairs.push_back({i,j});}
    else{ifstream p(argv[5]);int i,j;while(p>>i>>j)pairs.push_back({i,j});}
    auto save=[&](){ofstream o(argv[2]);o<<f.n<<" "<<f.k<<'\n';for(auto&r:f.A){for(int a:r)o<<a<<" ";o<<'\n';}};
    long long val=f.score();cout<<"initial residual "<<val<<" pair blocks "<<pairs.size()<<endl;save();
    for(int iter=0;iter<passes&&val;iter++){
        shuffle(pairs.begin(),pairs.end(),f.rng);int improvements=0;
        for(auto [i,j]:pairs){
            int gain=f.fit(i,j);if(!gain)continue;
            long long check=f.score();assert(check==val+gain);val=check;save();improvements++;
            cout<<"pass "<<iter<<" pair "<<i<<","<<j<<" residual "<<val<<endl;
            if(!val)break;
        }
        cout<<"end pass "<<iter<<" improvements "<<improvements<<" residual "<<val<<endl;
        if(!improvements)break;
    }
}
