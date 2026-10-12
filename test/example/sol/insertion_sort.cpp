#include <bits/stdc++.h>
using namespace std;
typedef long long int ll;

int main(){
    ll N;cin>>N;
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    for(ll i=1;i<N;++i){
        ll key=a[i];
        ll j=i-1;
        while(j>=0 && a[j]>key){
            a[j+1]=a[j];
            --j;
        }
        a[j+1]=key;
    }
    for(ll n:a)cout<<n<<' ';
    cout<<endl;
    return 0;
}
