#!/bin/bash

rm -rf TrainingSeqReachRers2019

wget http://rers-challenge.org/2019/problems/sequential/TrainingSeqReachRers2019.zip
unzip TrainingSeqReachRers2019.zip
rm TrainingSeqReachRers2019.zip
rm -rf __MACOSX

cd TrainingSeqReachRers2019 || exit

for problem in *
do
  echo compiling $problem
  python ../patchrerslibfuzzer.py "$problem"/"$problem".c
  python ../gendict.py "$problem"/"$problem".c
  clang -g -O1 -fsanitize=fuzzer "$problem"/"$problem"_libfuzzer.c ../verifier.c -o "$problem"/"$problem"_fuzz
  mkdir "$problem"/corpus
done
