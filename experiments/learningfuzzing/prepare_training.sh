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
  python ../patchrersafl.py "$problem"/"$problem".c
  afl-clang-fast -o "$problem"/"$problem" "$problem"/"$problem"_afl.c ../verifier.c
  mkdir "$problem"/input
  echo 0 > "$problem"/input/0.txt
done