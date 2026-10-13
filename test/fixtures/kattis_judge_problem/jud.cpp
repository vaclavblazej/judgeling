#include <bits/stdc++.h>
using namespace std;

// Kattis-style custom judge: judge <input> <answer> <feedback_dir>, solution output on stdin, exit 42=AC/43=WA.
int main(int argc, char **argv){
    if(argc!=4)return 1; // bad invocation; not in result_codes, so judgeling reports BAD_INVOCATION
    ifstream answer_file(argv[2]);
    vector<long long> answer;
    long long x;
    while(answer_file>>x)answer.push_back(x);
    vector<long long> output;
    while(cin>>x)output.push_back(x);
    if(answer==output)return 42;
    return 43;
}
