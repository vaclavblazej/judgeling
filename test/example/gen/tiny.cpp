#include "gen.h"

// Deliberately tiny/fast; exists so tests can exercise the -D dataset regex filter
// against a second, distinctly-named dataset alongside "small".
int main(int argc, char **argv){
    TestcaseGenerator tg(argc, argv);
    tg.newCase();
    ll N=2;
    cout<<N<<endl;
    cout<<3<<" "<<1<<endl;
    return 0;
}
