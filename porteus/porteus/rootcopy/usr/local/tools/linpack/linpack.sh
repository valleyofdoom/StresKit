#!/bin/bash

usage() {
    echo "Usage: $0 [-m <gb>] [-s <samples>]"
}

main() {
    # cd to the directory of the script
    cd "$(dirname "${BASH_SOURCE[0]}")" || {
        echo "failed to cd to script directory"
        return 1
    }

    memory_arg=""
    samples_arg=""

    while getopts "m:s:" opt; do
        case $opt in
        m)
            memory_arg="$OPTARG"
            ;;
        s)
            samples_arg="$OPTARG"
            ;;
        \?)
            echo "error: invalid option: -$OPTARG"
            usage
            return 1
            ;;
        :)
            echo "error: option -$OPTARG requires an argument"
            usage
            return 1
            ;;
        esac
    done

    if [ -n "$memory_arg" ]; then
        memory_in_gb=$memory_arg
    else
        # use MemFree - 150mb of memory by default
        free_mem_total_gb=$(echo "$(grep MemFree /proc/meminfo | awk '{print $2}') / 1048576" | bc)
        memory_in_gb=$(echo "scale=2; $free_mem_total_gb - 0.1" | bc)
    fi

    samples=${samples_arg:-100}

    has_avx=$(grep -q "avx" /proc/cpuinfo && echo 1 || echo 0)
    memory_in_bytes=$(echo "$memory_in_gb * 1073741824" | bc)

    if [ "$has_avx" -eq 1 ]; then
        base=16
        ignore=32
    else
        base=8
        ignore=16
    fi

    psize=$(echo "sqrt($memory_in_bytes / 8)" | bc)
    # no float support so number gets floored
    optimal_psize=$(((($psize + $base - 1) / $ignore) * $ignore + $base))

    # create lininput
    echo -e "\n\n1\n$optimal_psize\n$optimal_psize\n$samples\n4" >"lininput_xeon64"

    # environment variables for linpack
    export KMP_AFFINITY=nowarnings,compact,1,0,granularity=fine

    new_memory_in_bytes=$(($psize ** 2 * 8))
    new_memory_in_gb=$(echo "scale=3; $new_memory_in_bytes / 1073741824" | bc)

    echo "starting linpack with $new_memory_in_gb GB and $samples samples"

    # run linpack
    ./xlinpack_xeon64 lininput_xeon64

    return 0
}

main "$@"
