#include <bits/stdc++.h>
using namespace std;
typedef long long int ll;

int main(){
    ll N;cin>>N;
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    for(ll i=0;i<N;++i){
        bool swapped=false;
        for(ll j=0;j<N-1-i;++j){
            if(a[j]>a[j+1]){
                swap(a[j],a[j+1]);
                swapped=true;
            }
        }
        if(!swapped)break;
    }
    for(ll n:a)cout<<n<<' ';
    cout<<endl;
    return 0;
}
