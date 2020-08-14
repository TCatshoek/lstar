#!/bin/bash

rm -rf SeqReachabilityRers2019

wget http://rers-challenge.org/2019/problems/sequential/SeqReachabilityRers2019_Mar_9th.zip
unzip SeqReachabilityRers2019_Mar_9th.zip
rm SeqReachabilityRers2019_Mar_9th.zip
rm -rf __MACOSX

cd SeqReachabilityRers2019 || exit

for problem in *
do
  echo compiling $problem
  python ../patchrerslibfuzzer.py "$problem"/"$problem".c
  python ../gendict.py "$problem"/"$problem".c
  clang -g -O1 -fsanitize=fuzzer "$problem"/"$problem"_libfuzzer.c ../verifier.c -o "$problem"/"$problem"_fuzz
  mkdir "$problem"/corpus
done
