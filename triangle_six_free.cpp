#define TRIANGLE_MATE_LIBRARY
#include "triangle_free_mates.cpp"
#define TRIANGLE_SIX_LIBRARY
#include "triangle_six.cpp"
struct FreeSearch:Search{
    using Search::Search;
    long long matchpairs=0,steps=0,limited=0;
    void complete() override{
        vector<unsigned> block;array<Mask,36> adj{};
        for(int i=0;i<36;i++)for(int j=0;j<36;j++)if((i<24||j<24)&&g[i+3][j+3])adj[i]|=Mask(1)<<j;
        for(int i=0;i<10;i++)for(int s=0;s<6;s++)block.push_back(rot(edges[i]|(first[i].word<<12),s));
        Finish f(block,adj,200000);bool ok=f.run(6);matchpairs+=f.numpairs;steps+=f.nodes;limited+=f.nodes>f.limit;
        if(ok){inc++;for(auto a:block)out<<a<<' ';for(auto a:f.mate)out<<a<<' ';for(auto a:f.solution)out<<a<<' ';out<<endl;}
    }
};
int main(int argc,char**argv){
    if(argc!=7)return 2;ofstream out(argv[6]);FreeSearch s(atoi(argv[1]),atoi(argv[2]),atoi(argv[3]),atoi(argv[4]),atoi(argv[5]),out);s.run();
    cout<<"pair designs "<<s.paired<<" realizable mate orbits "<<s.matchpairs<<" nodes "<<s.steps<<" limits "<<s.limited<<" full incidences "<<s.inc<<endl;
}
