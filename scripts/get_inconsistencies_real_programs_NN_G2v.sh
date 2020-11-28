#!/bin/bash

benchmark=$1
preprocess=$2
split=$3

if [ -z "${benchmark}" ]; then
    echo "benchmark is unset or set to the empty string"
    exit 1;
fi

if [ -z "${preprocess}" ]; then
    echo "No preprocessing"
    preprocess="np"
fi

if [ "${preprocess}" = "p" ]; then
	datasets=$(cat ./settings.py | grep "DATASETS_DIR" | cut -d '=' -f 2 | cut -d '#' -f 1 | tr -d \'\" | tr -d '[:space:]')
	bcs=$(cat ./settings.py | grep "BCS_DIR" | cut -d '=' -f 2 | cut -d '#' -f 1 | tr -d \'\" | tr -d '[:space:]')
	data=$(cat ./settings.py | grep "DATA_DIR" | cut -d '=' -f 2 | cut -d '#' -f 1 | tr -d \'\" | tr -d '[:space:]')
	echo "Removing dataset folder of $benchmark"
	rm -rf "$data/$datasets/$benchmark"
	echo "Removing IR folder of $benchmark"
	rm -rf "$data/$bcs/$benchmark"
	python __init__.py -p=$benchmark -a=BC
	python __init__.py -p=$benchmark -a=PDG
	python __init__.py -p=$benchmark -a=AS
	if [ "${split}" = "ns" ]; then
		python __init__.py -p=$benchmark -a=FE -ft=afs_NN
		python __init__.py -p=$benchmark -a=FE -ft=afs.bb1_NN
	else
		python __init__.py -p=$benchmark -a=FE -ft=afs_NN -s=True
                python __init__.py -p=$benchmark -a=FE -ft=afs.bb1_NN -s=True
	fi
fi

python __init__.py -p=$benchmark -a=MC -cf=afs_NN,afs_G2v -ca=cc_0.95,cc_0.98 -sc=online
python __init__.py -p=$benchmark -a=MC -cf=afs.bb1_NN,afs.bb1_G2v -ca=cc_0.95,cc_0.98 -sc=online
