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
  python ../patchrerslibfuzzer.py "$problem"/"$problem".c
  python ../gendict.py "$problem"/"$problem".c
  clang -g -O1 -fsanitize=fuzzer "$problem"/"$problem"_libfuzzer.c ../verifier.c -o "$problem"/"$problem"_fuzz
  mkdir "$problem"/corpus
done
