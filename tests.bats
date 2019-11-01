#!/usr/bin/env bats

function setup {
    r="$(pwd)/run.sh"
}

@test "usage is invoked by default" {
    result="$($r)"
    [[ "$result" = usage:* ]]
}

@test "help: flag -h" {
    result="$($r -h)"
    [[ "$result" = usage:* ]]
}

@test "color: flag -c" {
    result="$($r -c)"
    [[ "$result" = usage:* ]]
}

@test "list problems: flag -l" {
    result="$($r -l)"
    [[ "$result" = List* ]]
}

@test "debug output: flag -d" {
    result="$($r -d)"
    [[ "$result" = "Debug mode!"* ]]
}

@test "invalid problem: flag -p" {
    result="$($r -p invalid_problem)"
    echo "$result"
    [[ "$result" = "No unique problem with this ID!"* ]]
}

@test "valid problem print: flag -p" {
    result="$($r -p lis)"
    echo "$result"
    [[ "$result" = "Problem definition"* ]]
}




