#include <bits/stdc++.h>
using namespace std;
typedef long long int ll;

int main(){
    ll N;cin>>N;
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    for(ll i=0;i<N;++i){
        ll m=i;
        for(ll j=i+1;j<N;++j)if(a[j]<a[m])m=j;
        swap(a[i],a[m]);
    }
    for(ll n:a)cout<<n<<' ';
    cout<<endl;
    return 0;
}
