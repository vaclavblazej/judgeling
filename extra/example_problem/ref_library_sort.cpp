#include <bits/stdc++.h>
using namespace std;
typedef long long int ll;

int main(){
    ll N;cin>>N;
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    sort(a.begin(),a.end());
    for(ll n:a)cout<<n<<' ';
    cout<<endl;
    return 0;
}

