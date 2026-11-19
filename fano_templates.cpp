// Enumerate cyclic twofold triple systems and compatible row and column resolutions.
#define COCLIQUE_ROWS_LIBRARY
#include <cassert>
#include "coclique_rows.cpp"
#include <bit>
#include <set>
#include <string>
using std::array;
unsigned rot(unsigned m,int j){
    unsigned a=m&127,b=(m>>7)&127;
    return (m&(1<<14))|((a<<j|a>>(7-j))&127)|(((b<<j|b>>(7-j))&127)<<7);
}
struct Family {
    vector<array<int,15>> coeff;
    vector<array<unsigned,7>> orbit;
    int pairclass[15][15]{};
    long long families=0,resolved=0,templates=0,rowchecks=0;
    int limit,template_cap;ostream &out;
    Family(int limit,int cap,ostream &out):limit(limit),template_cap(cap),out(out){
        set<unsigned> seen;
        for(int a=0;a<15;a++)for(int b=0;b<a;b++)seen.insert(minrot((1u<<a)|(1u<<b)));
        assert(seen.size()==15);vector<unsigned> pairs(seen.begin(),seen.end());
        for(int a=0;a<15;a++)for(int b=0;b<a;b++){
            int i=lower_bound(pairs.begin(),pairs.end(),minrot((1u<<a)|(1u<<b)))-pairs.begin();
            pairclass[a][b]=pairclass[b][a]=i;
        }
        for(int a=0;a<15;a++)for(int b=0;b<a;b++)for(int c=0;c<b;c++){
            unsigned m=(1u<<a)|(1u<<b)|(1u<<c);if(m!=minrot(m))continue;
            array<unsigned,7> o;for(int j=0;j<7;j++)o[j]=rot(m,j);
            array<int,15> v{};v[pairclass[a][b]]++;v[pairclass[a][c]]++;v[pairclass[b][c]]++;
            if(*max_element(v.begin(),v.end())<=2){coeff.push_back(v);orbit.push_back(o);}
        }
    }
    unsigned minrot(unsigned m){unsigned best=m;for(int s=1;s<7;s++)best=min(best,rot(m,s));return best;}
    vector<array<int,10>> labels;array<int,10> placement{};
    void resolutions(const vector<int>& chosen,int i,unsigned once,unsigned twice,unsigned placed[10]){
        if(i==10){if(twice==32767)labels.push_back(placement);return;}
        for(int j=0;j<(i?7:1);j++){
            unsigned m=orbit[chosen[i]][j];if(m&twice)continue;
            bool ok=true;for(int h=0;h<i;h++)if(popcount(m&placed[h])>1){ok=false;break;}
            if(!ok)continue;
            placed[i]=m;placement[i]=j;resolutions(chosen,i+1,once|m,twice|(once&m),placed);
        }
    }
    void assignments(const vector<int>& chosen){
        families++;labels.clear();unsigned placed[10]{};resolutions(chosen,0,0,0,placed);
        if(labels.empty())return;resolved++;
        for(auto &l:labels)for(auto &r:labels){
            array<int,7> ct{};int cols[10],dup=0;bool ok=true;
            for(int i=0;i<10;i++){
                int c=(l[i]-r[i]+7)%7;cols[i]=c;if(++ct[c]>2){ok=false;break;}
            }
            if(!ok||*min_element(ct.begin(),ct.end())==0)continue;
            for(int d=0;d<7;d++)if(ct[d]==2)dup|=1<<d;
            for(int s=1;s<7;s++)if(popcount((unsigned)dup&rot(dup,s))!=1)ok=false;
            if(!ok)continue;
            for(int i=0;i<10;i++)for(int j=0;j<i;j++)
                if(cols[i]==cols[j]&&(orbit[chosen[i]][l[i]]&orbit[chosen[j]][l[j]]))ok=false;
            if(!ok)continue;
            templates++;Enumerator en;en.k=14;en.h=29;en.n=70;
            for(int i=0;i<10;i++)for(int s=0;s<7;s++)
                en.block.push_back(rot(orbit[chosen[i]][l[i]],s)|(1u<<(15+s))|(1u<<(22+(s+cols[i])%7)));
            en.prepare();int completed=0;
            for(int i=0;i<70;i+=7){
                auto block=en.block[i];int b=cols[i/7];Bits avail=(((Bits)1<<70)-1)&~en.conflict[i];
                array<int,32> need{};
                for(int h=0;h<29;h++){
                    int known=h<15?0:(h<22?!((dup>>((b-(h-15)+7)%7))&1):!((dup>>(h-22))&1));
                    need[h]=2-known-((block>>h)&1);
                    if(!need[h])avail&=~en.point[h];
                }
                en.output.clear();en.visit(0,avail,need,9);if(en.output.empty())break;completed++;
            }
            rowchecks+=completed;
            if(completed==10 || templates==1){
                out<<completed<<' '<<dup;
                for(auto block:en.block)out<<' '<<block;out<<endl;
            }
            if(templates>=template_cap)return;
        }
    }
    void design(vector<int> allow,array<int,15> need,vector<int>&chosen){
        if(families>=limit||templates>=template_cap)return;
        if(chosen.size()==10){for(auto v:need)if(v)return;assignments(chosen);return;}
        vector<int> valid;
        for(int z:allow){bool ok=true;for(int k=0;k<15;k++)if(coeff[z][k]>need[k]){ok=false;break;}if(ok)valid.push_back(z);}
        int score=INT_MAX;vector<vector<int>> opts;int target=-1;
        for(int k=0;k<15;k++)if(need[k]){
            vector<vector<int>> trial;vector<int> ones;
            for(int z:valid){
                int x=coeff[z][k];
                if(x==need[k])trial.push_back({z});
                else if(x==1){for(int w:ones)trial.push_back({w,z});ones.push_back(z);}
            }
            if((int)trial.size()<score){score=trial.size();opts.swap(trial);target=k;}
        }
        if(target<0||!score)return;vector<int> remaining;
        for(int z:valid)if(!coeff[z][target])remaining.push_back(z);
        for(auto &add:opts){
            auto n=need;for(int z:add)for(int k=0;k<15;k++)n[k]-=coeff[z][k];
            if(*min_element(n.begin(),n.end())<0)continue;
            for(int z:add)chosen.push_back(z);design(remaining,n,chosen);chosen.resize(chosen.size()-add.size());
            if(families>=limit||templates>=template_cap)return;
        }
    }
};
int main(int argc,char**argv){
    if(argc!=4)return 2;ofstream out(argv[3]);Family f(atoi(argv[1]),atoi(argv[2]),out);
    vector<int> v,c;for(int i=0;i<(int)f.orbit.size();i++)v.push_back(i);
    array<int,15> n;n.fill(2);f.design(v,n,c);
    cout<<f.families<<" families "<<f.resolved<<" with resolutions "<<f.templates<<" candidate arrays "<<f.rowchecks<<" initially realizable row orbits"<<endl;
}
