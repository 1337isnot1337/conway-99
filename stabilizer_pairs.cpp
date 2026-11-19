// Unordered pair orbits of a supplied permutation group, in triangular ordering.
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <vector>

struct Partition{
    std::vector<int> parent;
    explicit Partition(int n):parent(n,-1){}
    int root(int i){
        int r=i;
        while(parent[r]>=0)r=parent[r];
        while(i!=r){int j=parent[i];parent[i]=r;i=j;}
        return r;
    }
    void merge(int i,int j){
        i=root(i);j=root(j);
        if(i==j)return;
        if(parent[i]>parent[j])std::swap(i,j);
        parent[i]+=parent[j];parent[j]=i;
    }
};
int packed(int i,int j){
    if(i<j)std::swap(i,j);
    return i*(i+1)/2+j;
}
int main(int argc,char**argv){
    if(argc!=4)return 1;
    int m=std::stoi(argv[1]),len=packed(m-1,m-1)+1;
    std::ifstream in(argv[2],std::ios::binary);
    std::vector<uint16_t> perm(m);
    Partition sets(len);
    while(in.read(reinterpret_cast<char*>(perm.data()),m*sizeof(uint16_t))){
        for(int i=0,n=0;i<m;i++)
            for(int j=0;j<=i;j++,n++)
                sets.merge(n,packed(perm[i],perm[j]));
    }
    std::vector<int> names(len,-1);
    std::vector<uint32_t> result(len);
    int count=0;
    for(int i=0;i<len;i++){
        int r=sets.root(i);
        if(names[r]<0)names[r]=count++;
        result[i]=names[r];
    }
    std::ofstream out(argv[3],std::ios::binary);
    out.write(reinterpret_cast<char*>(result.data()),result.size()*sizeof(uint32_t));
    std::cout<<count<<" pair orbits\n";
}
