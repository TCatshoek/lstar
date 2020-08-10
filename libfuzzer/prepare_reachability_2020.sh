#!/bin/bash

rm -rf SeqReachabilityRers2020

wget http://rers-challenge.org/2020/problems/sequential/SeqReachabilityRers2020.zip
unzip -d SeqReachabilityRers2020 SeqReachabilityRers2020.zip
rm SeqReachabilityRers2020.zip
rm -rf __MACOSX

cd SeqReachabilityRers2020

for problem in *
do
  echo compiling $problem
  python ../patchrerslibfuzzer.py "$problem"/"$problem".c
  python ../gendict.py "$problem"/"$problem".c
  clang -g -O1 -fsanitize=fuzzer "$problem"/"$problem"_libfuzzer.c ../verifier.c -o "$problem"/"$problem"_fuzz
  mkdir "$problem"/corpus
done
