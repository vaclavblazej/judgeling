#include <bits/stdc++.h>
using namespace std;
typedef long long int ll;

void mergeSort(vector<ll> &a, ll lo, ll hi){
    if(lo>=hi)return;
    ll mid=(lo+hi)/2;
    mergeSort(a,lo,mid);
    mergeSort(a,mid+1,hi);
    vector<ll> merged;
    merged.reserve(hi-lo+1);
    ll i=lo,j=mid+1;
    while(i<=mid && j<=hi){
        if(a[i]<=a[j])merged.push_back(a[i++]);
        else merged.push_back(a[j++]);
    }
    while(i<=mid)merged.push_back(a[i++]);
    while(j<=hi)merged.push_back(a[j++]);
    for(ll k=0;k<(ll)merged.size();++k)a[lo+k]=merged[k];
}

int main(){
    ll N;cin>>N;
    vector<ll> a(N);
    for(ll &n:a)cin>>n;
    if(N>0)mergeSort(a,0,N-1);
    for(ll n:a)cout<<n<<' ';
    cout<<endl;
    return 0;
}
