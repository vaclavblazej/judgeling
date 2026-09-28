#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

// Deliberately does not sort; used to verify judgeling detects wrong answers.
int main(){
    ll N;cin>>N;
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    for(ll n:a)cout<<n<<' ';
    cout<<endl;
    return 0;
}
