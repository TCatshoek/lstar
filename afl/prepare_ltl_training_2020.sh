#!/bin/bash

rm -rf TrainingSeqLtlRers2020

wget http://rers-challenge.org/2020/problems/sequential/TrainingSeqLtlRers2020.zip
unzip -d TrainingSeqLtlRers2020 TrainingSeqLtlRers2020.zip
rm TrainingSeqLtlRers2020.zip
rm -rf __MACOSX

cd TrainingSeqLtlRers2020 || exit

for problem in *
do
  echo compiling $problem
  python ../patchrersafl.py "$problem"/"$problem".c
  afl-clang-fast -o "$problem"/"$problem" "$problem"/"$problem"_afl.c ../verifier.c
  mkdir "$problem"/input
  echo 0 > "$problem"/input/0.txt
done
