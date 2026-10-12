#include <bits/stdc++.h>
using namespace std;
typedef long long int ll;

void siftDown(vector<ll> &a, ll n, ll i){
    while(true){
        ll largest=i, l=2*i+1, r=2*i+2;
        if(l<n && a[l]>a[largest])largest=l;
        if(r<n && a[r]>a[largest])largest=r;
        if(largest==i)break;
        swap(a[i],a[largest]);
        i=largest;
    }
}

int main(){
    ll N;cin>>N;
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    for(ll i=N/2-1;i>=0;--i)siftDown(a,N,i);
    for(ll i=N-1;i>0;--i){
        swap(a[0],a[i]);
        siftDown(a,i,0);
    }
    for(ll n:a)cout<<n<<' ';
    cout<<endl;
    return 0;
}
