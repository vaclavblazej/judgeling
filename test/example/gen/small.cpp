#include "../../../gen.h"

int main(int argc, char **argv){
    TestcaseGenerator tg(argc, argv);
    const ll MAX=1000;
    ll N=300;
    for(int i=0; i<10; ++i){
        for(int j=0; j<5; ++j){
            tg.newCase();
            vector<ll> a(N);
            for(int i=0; i<N; ++i)a[i]=rand()%MAX;
            cout<<N<<endl;
            for(ll n:a)cout<<n<<' ';
            cout<<endl;
        }
        N*=1.9;
    }
    return 0;
}

