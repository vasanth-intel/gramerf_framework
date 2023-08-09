#! /bin/bash

iter=$1
cmd1=$2
if [ "$#" -eq 4 ] 
then
    cmd2=$3
    res_file=$4
    for ((i=1; i<=$iter; i++))
    do
        echo $cmd1
        eval $cmd1 2>&1 | tee -a ${res_file}_s0_iter_${i}.txt &
        echo $cmd2
        eval $cmd2 2>&1 | tee -a ${res_file}_s1_iter_${i}.txt
        sleep 120
    done
elif [ "$#" -eq 3 ]
then
    res_file=$3
    for ((i=1; i<=$iter; i++))
    do
        echo $cmd1
        eval $cmd1 2>&1 | tee -a ${res_file}_s0_iter_${i}.txt
        sleep 120
    done
fi
