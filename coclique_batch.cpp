// Check the complete row domains with no symmetry restriction on an exterior graph.
#define COCLIQUE_ROWS_LIBRARY
#include "coclique_rows.cpp"
#include <map>
#include <set>

unsigned translate(unsigned b,int s){unsigned r=0;while(b){int i=__builtin_ctz(b);b&=b-1;r|=1u<<(i/11*11+(i+s)%11);}return r;}
Bits shift(Bits row,int s,int step){Bits r=0;while(row){int j=low(row);row&=row-1;r|=(Bits)1<<(j/step*step+(j+s)%step);}return r;}

bool possible(Enumerator &e,int step=11){
    vector<vector<Bits>> dom(77);
    for(int i=0;i<77;i+=step){
        e.row(i);
        if(e.output.empty())return false;
        for(int s=0;s<step;s++)for(auto x:e.output)dom[i+s].push_back(shift(x,s,step));
        // Test every already-known orbit coherently, without equating translated choices.
        bool changed=true;
        while(changed){
            changed=false;
            for(int a=0;a<=i;a+=step){
                vector<Bits> good;
                for(auto x:dom[a]){
                    bool valid=true;
                    for(int b=0;b<i+step;b++){
                        if(a==b)continue;
                        int t=(x>>b)&1,need=2-__builtin_popcount(e.block[a]&e.block[b])-t;
                        bool match=false;
                        for(auto y:dom[b])if((int)((y>>a)&1)==t && count(x&y)==need){match=true;break;}
                        if(!match){valid=false;break;}
                    }
                    if(valid)good.push_back(x);
                }
                if(good.empty())return false;
                if(good.size()<dom[a].size()){
                    changed=true;
                    for(int s=0;s<step;s++){dom[a+s].clear();for(auto x:good)dom[a+s].push_back(shift(x,s,step));}
                }
            }
        }
    }
    return true;
}

int main(int argc,char**argv){
    if(argc!=3&&argc!=4)return 2;
    int step=argc==4?atoi(argv[3]):11;if(step<1||77%step)return 3;
    ifstream in(argv[1]);ofstream out(argv[2]);int done=0,alive=0;
    while(true){
        vector<unsigned> base(argc==4?77:7);if(!(in>>base[0]))break;for(int j=1;j<(int)base.size();j++)if(!(in>>base[j]))return 3;
        Enumerator e;e.k=14;e.h=22;e.n=77;
        if(argc==3){for(auto b:base)for(int s=0;s<11;s++)e.block.push_back(translate(b,s));}
        else e.block=base;
        // Verify the actual design, independent of difference-family generation.
        for(int i=0;i<22;i++)for(int j=0;j<=i;j++){
            int r=0;for(auto b:e.block)r+=((b>>i)&(b>>j)&1);
            if(r!=(i==j?14:2))return 4;
        }
        for(int i=0;i<77;i++)for(int j=0;j<i;j++)
            if(__builtin_popcount(e.block[i]&e.block[j])>2)return 5;
        e.prepare();
        if(argc==4){
            set<Bits> rows(e.point.begin(),e.point.end());for(auto q:e.point)if(!rows.count(shift(q,1,step)))return 6;
        }
        if(possible(e,step)){for(auto b:base)out<<b<<' ';out<<'\n';alive++;}
        if(++done%1000==0)cout<<done<<" checked, "<<alive<<" remaining"<<endl;
    }
    cout<<done<<" checked, "<<alive<<" remaining"<<endl;
}
