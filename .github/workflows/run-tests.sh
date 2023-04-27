#!/bin/bash

if [ $# -ne 6 ]; then
    echo "Usage: $0 timeout solver-image env-file testdir resultdir extra-args"
    exit 0
fi

to=$1
img=$2
env=$3
testdir=$(readlink -f $4)
resultdir=$5
extra=$6

mkdir -p $resultdir

tests=("hc-power-11" "hc-power-12" "hc-square-01" "hc-square-02" "hc-toyno-01" "hc-toyyes-01")

# setup validator
if [ ! -e validator.py ]; then
    curl -fL https://raw.githubusercontent.com/core-challenge/isr-validator/main/main.py -o validator.py
fi

cat "$LAUNCH_OPTIONS" | while IFS= read -r line
do
    # Ignore lines starting with #
    if [[ $line =~ ^#.* ]]; then
        continue
    fi
    config=$(echo "$line" | cut -d',' -f1)
    params=$(echo "$line" | cut -d',' -f2-)

    ntests=${#tests[@]}
    tfailed=0
    vfailed=0
    efailed=0

    for t in ${tests[@]}
    do
        COLFILE=/tests/${t}.col
        DATFILE=/tests/${t}_01.dat

        # Replace placeholders in parameters
        params=$(echo "$params" | sed "s/TIMEOUT/$TIMEOUT/g")
        params=$(echo "$params" | sed "s/MAX_MEMORY_SIZE/$MAX_MEMORY_SIZE/g")
        params=$(echo "$params" | sed "s/COLFILE/$COLFILE/g")
        params=$(echo "$params" | sed "s/DATFILE/$DATFILE/g")

        timeout 30 \
            docker run --rm -t -v $testdir:/tests --env-file $env $img $extra $params &> $resultdir/${config}-${t}-result.txt \
            ; echo $? > $resultdir/${t}-code
        code=$(cat $resultdir/${t}-code)
        if [ "$code" -eq 0 ]; then
            python3 validator.py $testdir/${t}.col $testdir/${t}_01.dat $resultdir/${t}-result.txt &> $resultdir/${config}-${t}-validator-result.txt \
                ; echo $? > $resultdir/${t}-validator-code
            vcode=$(cat $resultdir/${t}-validator-code)
            if [ "$vcode" -eq 0 ]; then
                echo "${t}: pass"
                echo "| ${t} | :white_check_mark: |" >> $resultdir/${config}.md
            else
                echo "${t}: validation failed"
                echo "| ${t} | :no_entry: |" >> $resultdir/${config}.md
                ((vfailed++))
            fi
        elif [ "$code" -eq 124 ]; then
            echo "${t}: timeout"
            echo "| ${t} | :hourglass_flowing_sand: |" >> $resultdir/${config}.md
            ((tfailed++))
        else
            echo "${t}: execution failed"
            echo "| ${t} | :collision: |" >> $resultdir/${config}.md
            ((efailed++))
        fi
    done

    cat << EOS >> $resultdir/result.md
    # Configuration ${config}
    - #Instances: $ntests
    - Timeout: $to seconds
    - Memory limit: $MAX_MEMORY_SIZE GB

    ## Test results

    | Instance | Result |
    | :------: | :----: |
    $(cat $resultdir/tmp.md)

    Legends:
    - :white_check_mark:: The solver succeeded its execution with valid output
    - :no_entry:: The solver succeeded its execution with invalid output
    - :hourglass_flowing_sand:: The solver failed its execution due to timeout
    - :collision:: The solver failed its execution for other reasons such as internal errors
    EOS

    rm -f $resultdir/tmp.md

    echo "$((ntests-vfailed-tfailed-efailed))/${ntests} passed"

    exit $((vfailed+efailed))
done