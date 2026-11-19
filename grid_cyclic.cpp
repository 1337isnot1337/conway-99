// Enumerate translation-invariant linear matching data; internal directions and affine offsets remain free.
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
using namespace std;
using Mat=array<int,4>;
int mod(int x){return (x%3+3)%3;}
Mat compose(Mat a,Mat b){
    return {mod(a[0]*b[0]+a[1]*b[2]),mod(a[0]*b[1]+a[1]*b[3]),mod(a[2]*b[0]+a[3]*b[2]),mod(a[2]*b[1]+a[3]*b[3])};
}
struct Census{
    vector<Mat> g;
    int mult[48][48],conj[48][48],inv[48],perm[48][8],id;
    array<int,11> edge{};
    long long visited=0,modular=0,irreducible=0,local=0;
    ofstream file;
    void init(){
        for(int a=0;a<3;a++)for(int b=0;b<3;b++)for(int c=0;c<3;c++)for(int d=0;d<3;d++)
            if(mod(a*d-b*c))g.push_back({a,b,c,d});
        auto idx=[&](Mat x){return int(find(g.begin(),g.end(),x)-g.begin());};
        id=idx({1,0,0,1});
        for(int a=0;a<48;a++){
            for(int b=0;b<48;b++){mult[a][b]=idx(compose(g[a],g[b]));if(mult[a][b]==id)inv[a]=b;}
            for(int v=1;v<9;v++){
                int x=v/3,y=v%3;
                perm[a][v-1]=3*mod(g[a][0]*x+g[a][1]*y)+mod(g[a][2]*x+g[a][3]*y)-1;
            }
        }
        for(int a=0;a<48;a++)for(int b=0;b<48;b++)conj[a][b]=mult[mult[a][b]][inv[a]];
    }
    int opposite(int v){v++;return 3*mod(-v/3)+mod(-(v%3))-1;}
    void check(){
        visited++;
        int fixed[6][8]{};
        for(int d=1;d<=5;d++){
            int h[9],n=0;
            for(int k=1;k<11;k++)if(k!=d)h[n++]=mult[edge[(d-k+11)%11]][edge[k]];
            for(int x=0;x<8;x++){
                int freq[8]{};
                for(int a:h)freq[perm[a][x]]++;
                for(int f:freq)if(f%3)return;
                fixed[d][x]=freq[perm[edge[d]][x]];
            }
        }
        modular++;
        for(int x=0;x<8;x++){
            bool preserved=true;
            // A line in cell 0 determines all other lines via the direct matching.
            int line[11];for(int i=0;i<11;i++)line[i]=perm[edge[i]][x];
            for(int i=0;i<11;i++)for(int j=i+1;j<11;j++){
                int z=perm[edge[j-i]][line[i]];
                if(z!=line[j]&&z!=opposite(line[j]))preserved=false;
            }
            if(preserved)return;
        }
        irreducible++;
        int possible[11][11][6]{},lines[8]{},L=0;
        for(int x=0;x<8;x++)if(x<opposite(x)){lines[x]=lines[opposite(x)]=L++;}
        vector<int> masks;for(int x=0;x<16;x++)if(popcount((unsigned)x)==2)masks.push_back(x);
        for(int i=0;i<11;i++)for(int d=1;d<=5;d++){
            int j=(i+d)%11;
            for(int a=0;a<6;a++)for(int b=0;b<6;b++){
                bool valid=true;
                for(int x=0;x<8;x++){
                    int t=(masks[a]>>lines[x])&1,u=(masks[b]>>lines[perm[edge[d]][x]])&1;
                    int rhs=3-3*(t+u),m=fixed[d][x];
                    if(m+2*rhs<0||m-rhs<0){valid=false;break;}
                }
                if(valid){possible[i][j][a]|=1<<b;possible[j][i][b]|=1<<a;}
            }
        }
        auto search=[&](auto&&rec,int used,array<int,11> dom)->bool{
            if(used==2047)return true;
            int i=-1;
            for(int k=0;k<11;k++)if(!(used>>k&1)&&(i<0||popcount((unsigned)dom[k])<popcount((unsigned)dom[i])))i=k;
            for(int a=0;a<6;a++)if(dom[i]>>a&1){
                auto next=dom;bool ok=true;
                for(int k=0;k<11;k++)if(k!=i&&!(used>>k&1)){next[k]&=possible[i][k][a];if(!next[k]){ok=false;break;}}
                if(ok&&rec(rec,used|(1<<i),next))return true;
            }
            return false;
        };
        array<int,11> dom;dom.fill(63);
        if(!search(search,0,dom))return;
        local++;
        for(int i=1;i<=5;i++)for(int j=0;j<4;j++)file<<g[edge[i]][j]<<' ';
        file<<'\n';
    }
    void run(int depth,vector<int> aut){
        if(depth==6){check();return;}
        for(int m=0;m<48;m++){
            bool canon=true;vector<int> stabilizer;
            for(int a:aut){
                if(conj[a][m]<m){canon=false;break;}
                if(conj[a][m]==m)stabilizer.push_back(a);
            }
            if(!canon)continue;
            edge[depth]=m;edge[11-depth]=inv[m];run(depth+1,stabilizer);
        }
    }
};
int main(int argc,char**argv){
    if(argc!=2)return 2;
    Census c;c.init();c.file.open(argv[1]);c.edge[0]=c.id;vector<int>a;
    for(int i=0;i<48;i++)a.push_back(i);
    c.run(1,a);
    cout<<"simultaneous conjugacy representatives "<<c.visited<<" modular "<<c.modular<<" irreducible "<<c.irreducible<<" local phases feasible "<<c.local<<endl;
}
