#include "../../../gen.h"

int main(int argc, char **argv){
    TestcaseGenerator tg(argc, argv);
    const ll MAX=1000000000;
    ll mn=100;
    ll mx=700;
    for(int i=0; i<20; ++i){
        for(int j=0; j<10; ++j){
            ll N=mn+(rand()%(mx-mn));
            tg.newCase();
            vector<ll> a(N);
            for(int i=0; i<N; ++i)a[i]=rand()%MAX;
            cout<<N<<endl;
            for(ll n:a)cout<<n<<' ';
            cout<<endl;
        }
        mx*=1.5;
    }
    return 0;
}

