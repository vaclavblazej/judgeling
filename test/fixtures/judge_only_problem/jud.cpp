#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

int main(int argc, char **argv){
    if(argc!=3)return 43;
    auto input_file=argv[1];
    auto your_output_file=argv[2];
    freopen(input_file, "r", stdin);
    ll N;cin>>N;
    freopen(your_output_file, "r", stdin);
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    for(ll i=1; i<N; ++i){
        if(a[i-1] > a[i])return 1;
    }
    return 0;
}
