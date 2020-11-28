#!/bin/bash

benchmark=$1
threshold=$2
granularity=$3
preprocess=$4

if [ -z "${benchmark}" ]; then
    echo "benchmark is unset or set to the empty string"
    exit 1;
fi

if [ -z "${preprocess}" ]; then
    echo "No preprocessing"
    preprocess="np"
fi

rm output

if [ "${preprocess}" = "p" ]; then
	datasets=$(cat ./settings.py | grep "DATASETS_DIR" | cut -d '=' -f 2 | cut -d '#' -f 1 | tr -d \'\" | tr -d '[:space:]')
	bcs=$(cat ./settings.py | grep "BCS_DIR" | cut -d '=' -f 2 | cut -d '#' -f 1 | tr -d \'\" | tr -d '[:space:]')
	data=$(cat ./settings.py | grep "DATA_DIR" | cut -d '=' -f 2 | cut -d '#' -f 1 | tr -d \'\" | tr -d '[:space:]')

	rm -rf "$data/$datasets/$benchmark"
	rm -rf "$data/$bcs/$benchmark"
	python __init__.py -p=$benchmark -a=BC
	python __init__.py -p=$benchmark -a=PDG
	python __init__.py -p=$benchmark -a=AS
	python __init__.py -p=$benchmark -a=AS -cws=2
	python __init__.py -p=$benchmark -a=AS -hcf
        python __init__.py -p=$benchmark -a=AS -hcf -cws=2
	python __init__.py -p=$benchmark -a=FE -ft=afs_NN
	python __init__.py -p=$benchmark -a=FE -ft=afs.bb1_NN
	python __init__.py -p=$benchmark -a=FE -ft=afs.bb2_NN
	python __init__.py -p=$benchmark -a=FE -hcf -ft=afs_NN
        python __init__.py -p=$benchmark -a=FE -hcf -ft=afs.bb1_NN
        python __init__.py -p=$benchmark -a=FE -hcf -ft=afs.bb2_NN
fi

if [ "$threshold" = "all" ]; then
	if [ "$granularity" = "all" ]; then
	        python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.70,cc_0.99
        	python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.75,cc_0.99
        	python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.80,cc_0.99
        	python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.85,cc_0.99
        	python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.90,cc_0.99
        	python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.95,cc_0.99
		python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.95,cc_0.99
		python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.95,cc_0.99

		python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.95,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.95,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.95,cc_0.99
	elif [ "$granularity" = "afs" ]; then
		python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.95,cc_0.99

		python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.95,cc_0.99
	elif [ "$granularity" = "afs.bb1" ]; then
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.95,cc_0.99

		python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.95,cc_0.99
	elif [ "$granularity" = "afs.bb2" ]; then
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.95,cc_0.99

		python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.70,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.75,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.80,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.85,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.90,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.95,cc_0.99
	fi

elif [ "$threshold" = "most" ]; then
	if [ "$granularity" = "all" ]; then
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.95,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.95,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.95,cc_0.99

		python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.95,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.95,cc_0.99
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.95,cc_0.99
        elif [ "$granularity" = "afs" ]; then
                python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.95,cc_0.99

		python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -hcf -ca=cc_0.95,cc_0.99
        elif [ "$granularity" = "afs.bb1" ]; then
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.95,cc_0.99

		python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -hcf -ca=cc_0.95,cc_0.99
        elif [ "$granularity" = "afs.bb2" ]; then
                python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -ca=cc_0.95,cc_0.99

		python __init__.py -p=$benchmark -a=MC -cf=afs.bb2_NN,afs.bb2_G2v -hcf -ca=cc_0.95,cc_0.99
        fi
fi

