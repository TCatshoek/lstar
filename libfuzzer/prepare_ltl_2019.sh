#!/bin/bash

rm -rf SeqLtlRers2019

wget http://rers-challenge.org/2019/problems/sequential/SeqLtlRers2019_Mar_9th.zip
unzip SeqLtlRers2019_Mar_9th.zip
rm SeqLtlRers2019_Mar_9th.zip
rm -rf __MACOSX

cd SeqLtlRers2019 || exit

for problem in *
do
  echo compiling $problem
  python ../patchrerslibfuzzer.py "$problem"/"$problem".c
  python ../gendict.py "$problem"/"$problem".c
  clang -g -O1 -fsanitize=fuzzer "$problem"/"$problem"_libfuzzer.c ../verifier.c -o "$problem"/"$problem"_fuzz
  mkdir "$problem"/corpus
done
