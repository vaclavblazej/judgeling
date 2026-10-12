#include <bits/stdc++.h>
using namespace std;
typedef long long int ll;

void quickSort(vector<ll> &a, ll lo, ll hi){
    if(lo>=hi)return;
    ll pivot=a[lo+(hi-lo)/2];
    ll i=lo,j=hi;
    while(i<=j){
        while(a[i]<pivot)++i;
        while(a[j]>pivot)--j;
        if(i<=j){
            swap(a[i],a[j]);
            ++i;--j;
        }
    }
    quickSort(a,lo,j);
    quickSort(a,i,hi);
}

int main(){
    ll N;cin>>N;
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    if(N>0)quickSort(a,0,N-1);
    for(ll n:a)cout<<n<<' ';
    cout<<endl;
    return 0;
}
