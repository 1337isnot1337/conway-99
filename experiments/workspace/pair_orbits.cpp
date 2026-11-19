// Classify products of two outer-edge variables under signed-axis relabelings.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <vector>

struct Partition {
    std::vector<int> p;
    explicit Partition(int n):p(n,-1){}
    int find(int i){
        int r=i;
        while(p[r]>=0) r=p[r];
        while(i!=r){int j=p[i];p[i]=r;i=j;}
        return r;
    }
    void merge(int a,int b){
        a=find(a);b=find(b);
        if(a==b)return;
        if(p[a]>p[b])std::swap(a,b);
        p[a]+=p[b];p[b]=a;
    }
};
int tri(int a,int b){
    if(a<b)std::swap(a,b);
    return a*(a+1)/2+b;
}
int main(int argc,char**argv){
    int k=argc>1?std::stoi(argv[1]):14;
    std::vector<std::array<int,2>> outer;
    int idx[24][24]={};
    for(int a=0;a<k;a++)for(int b=a+1;b<k;b++)if((a^1)!=b){
        idx[a][b]=idx[b][a]=outer.size();
        outer.push_back({a,b});
    }
    int n=outer.size();
    std::vector<std::array<int,2>> vars{{-1,-1}};
    std::vector<int> eidx(n*n);
    for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){
        eidx[i*n+j]=eidx[j*n+i]=vars.size();vars.push_back({i,j});
    }
    int m=vars.size();
    int pairs=m*(m+1)/2;
    Partition uf(pairs);
    for(int g=0;g<k/2;g++){
        auto anchor=[&](int a){
            if(g==0)return a<2?a^1:a;
            if(a/2==g-1)return a+2;
            if(a/2==g)return a-2;
            return a;
        };
        std::vector<int> sigma(n),perm(m);
        for(int i=0;i<n;i++)sigma[i]=idx[anchor(outer[i][0])][anchor(outer[i][1])];
        for(int i=1;i<m;i++)perm[i]=eidx[sigma[vars[i][0]]*n+sigma[vars[i][1]]];
        for(int i=0;i<m;i++)for(int j=0;j<=i;j++)
            uf.merge(tri(i,j),tri(perm[i],perm[j]));
    }
    std::vector<int> cat(pairs,-1);
    int types=0;
    std::vector<uint16_t> out(pairs);
    for(int i=0;i<pairs;i++){
        int r=uf.find(i);if(cat[r]<0)cat[r]=types++;
        if(cat[r]>65535)return 2;
        out[i]=cat[r];
    }
    std::string path=argc>2?argv[2]:"pair-orbits.bin";
    std::ofstream f(path,std::ios::binary);
    f.write(reinterpret_cast<const char*>(out.data()),out.size()*sizeof(out[0]));
    std::cout<<"k "<<k<<" variables with constant "<<m<<" unordered entries "<<pairs<<" orbit count "<<types<<"\n";
}
