#!/bin/bash

rm -rf SeqLtlRers2020

wget http://rers-challenge.org/2020/problems/sequential/SeqLtlRers2020.zip
unzip -d SeqLtlRers2020 SeqLtlRers2020.zip
rm SeqLtlRers2020.zip
rm -rf __MACOSX

cd SeqLtlRers2020

for problem in *
do
  echo compiling $problem
  python ../patchrerslibfuzzer.py "$problem"/"$problem".c
  python ../gendict.py "$problem"/"$problem".c
  clang -g -O1 -fsanitize=fuzzer "$problem"/"$problem"_libfuzzer.c ../verifier.c -o "$problem"/"$problem"_fuzz
  mkdir "$problem"/corpus
done
