#!/usr/bin/env bash
# if possible keep this file under 1000 lines

# option to define dataset size ?

user_folder=$(pwd)

# commandline flags and solution files
while [ $# -ne 0 ]; do
    case "$1" in
        *)
            solution="$user_folder/$1"
            if [ ! -f "$solution" ]; then
                echo "File $1 does not exist"
            else
                solutions+=("$solution")
            fi
    esac
done

function execute { if [ "$debug_mode" = true ]; then valgrind "$@"; else "$@"; fi; echo ""; }

# function is used for the main functionality because otherwise
#     it is not easy to 'return' out of the script
function main {
    # general list of all the problem definitions
    if [ "$list_problems" = true ] && [ $scan = false ] && [ "${#solutions[@]}" -eq 0 ]; then
        echo "List of problems:"
        problems=( $(find "$script_path/problems/" -type d -exec find "{}" -maxdepth 1 -iname "[^_]*.md" \;) )
        for p in "${problems[@]}"; do
            flag=""
            if grep '\[//]: # (category)' "$p" 1>/dev/null 2>&1; then flag="category"; fi
            if grep '\[//]: # (proposal)' "$p" 1>/dev/null 2>&1; then flag="proposal"; fi
            cnt=$(echo "${p#"$script_path/problems"}" | grep -o "/" | wc -l)
            for _ in $(seq 1 "$cnt"); do echo -n " "; done
            echo -n "$(basename "$p" '.md')"
            if [ "$flag" != "" ]; then flag=" [$flag]"; fi
            test=""
            pf=$(dirname "$p")
            if [ -f "$pf/judge.cpp" ]; then test+="c"; fi
            if [ -f "$pf/solution.cpp" ] && [ -f "$pf/solution.cpp" ]; then test+="s"; fi
            if [ "$test" != "" ]; then test=" |$test|"; fi
            echo "$flag$test" #problem metadata
        done
        return 0
    fi


