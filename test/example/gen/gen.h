#ifndef __GEN__
#define __GEN__

#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

struct TestcaseGenerator{
    int INVALID_INVOCATION = 2;
    string caseName="";
    string caseExt="in";
    int caseCounter=0;
    string target_folder;
    ll seed;
    FILE *openfile;
    int total_cases=-1;
    int last_ratio=-1;
    TestcaseGenerator(int argc, char **argv, int total_cases=-1){
        if(argc!=3){
            cerr<<"invalid invocation of the _gen file\n";
            cerr<<"    usage: "<<argv[0]<<" <seed> <target_folder>\n";
            exit(1);
        }
        if(total_cases >= 80) this->total_cases = total_cases;
        this->seed = argc > 1 ? atoi(argv[1]) : time(NULL);
        this->target_folder = argc > 2 ? argv[2] : ".";
        srand(seed);
        openfile = 0;
        cerr<<"Generating ";cerr.flush();
    }
    void closeFile(){
        if(openfile)fclose(openfile);
        openfile = 0;
    }
    ~TestcaseGenerator(){
        cerr<<" done"<<endl;
        closeFile();
    }
    void newCase(){
        if(caseCounter%10000==9999){
            cerr<<"warning, this generator created "<<caseCounter<<" tests so far!"<<endl;
            cerr<<"    is this intended?"<<endl;
        }
        char c[]="    ";
        ++caseCounter;
        string file=target_folder;
        file+="/";
        file+=caseName;
        sprintf(c, "%03d", caseCounter);
        file+=string(c);
        file+=".";
        file+=caseExt;
        closeFile();
        openfile=freopen(file.c_str(), "w", stdout);
        if(!openfile){
            cerr<<"unable to open file: "<<file<<endl;
            exit(1);
        }
        if(total_cases != -1){
            int cur_ratio = 100*caseCounter / total_cases;
            if(cur_ratio != last_ratio){
                last_ratio = cur_ratio;
                cerr<<cur_ratio<<endl;
            }
        }else{
            cerr<<".";
            cerr.flush();
        }
    }
};

#endif //__GEN__

