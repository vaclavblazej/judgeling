#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
#define check(a) if(!(a)) {cerr<<"Check "<<#a<<" failed!\n";return 1;}

int main(int argc, char **argv){
    if(argc!=3)return 43;
    auto ref_output_file=argv[1];
    auto your_output_file=argv[2];
    freopen(ref_output_file, "r", stdin);
    vector<ll> ref;
    ll n;
    while(cin>>n)ref.push_back(n);
    cin.clear();
    freopen(your_output_file, "r", stdin);
    vector<ll> sol;
    while(cin>>n)sol.push_back(n);
    check(ref.size() == sol.size());
    ll N=ref.size();
    for(ll i=0; i<N; ++i){
        if(ref[i] != sol[i]){
            cerr<<i<<"-th element does not correspond"<<endl;
            check(ref[i] == sol[i]);
        }
    }
    return 0;
}
