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

ntests=${#tests[@]}
tfailed=0
vfailed=0
efailed=0

for t in ${tests[@]}
do
    timeout 30 \
        docker run --rm -t -v $testdir:/tests --env-file $env $img $extra /tests/${t}.col /tests/${t}_01.dat &> $resultdir/${t}-result.txt \
        ; echo $? > $resultdir/${t}-code
    code=$(cat $resultdir/${t}-code)
    if [ "$code" -eq 0 ]; then
        python3 validator.py $testdir/${t}.col $testdir/${t}_01.dat $resultdir/${t}-result.txt &> $resultdir/${t}-validator-result.txt \
            ; echo $? > $resultdir/${t}-validator-code
        vcode=$(cat $resultdir/${t}-validator-code)
        if [ "$vcode" -eq 0 ]; then
            echo "${t}: pass"
            echo "| ${t} | :white_check_mark: |" >> $resultdir/tmp.md
        else
            echo "${t}: validation failed"
            echo "| ${t} | :no_entry: |" >> $resultdir/tmp.md
            ((vfailed++))
        fi
    elif [ "$code" -eq 124 ]; then
        echo "${t}: timeout"
        echo "| ${t} | :hourglass_flowing_sand: |" >> $resultdir/tmp.md
        ((tfailed++))
    else
        echo "${t}: execution failed"
        echo "| ${t} | :collision: |" >> $resultdir/tmp.md
        ((efailed++))
    fi
done

cat << EOS > $resultdir/result.md
# Configuration
- #Instances: $ntests
- Timeout: $to seconds

# Test results

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
