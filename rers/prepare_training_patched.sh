#!/bin/bash

rm -rf TrainingSeqReachRers2019Patched
rm -rf TrainingSeqReachRers2019

wget http://rers-challenge.org/2019/problems/sequential/TrainingSeqReachRers2019.zip
unzip TrainingSeqReachRers2019.zip
rm TrainingSeqReachRers2019.zip
rm -rf __MACOSX

cd TrainingSeqReachRers2019

for problem in *
do
  echo compiling $problem
  python ../patchrers.py $problem/$problem.c
  python ../patchrerslib.py $problem/"${problem}"_patched.c
  gcc -o $problem/$problem $problem/"${problem}"_patched.c ../verifier_patched.c
  gcc -fPIC -shared -o $problem/"${problem}".so $problem/"${problem}"_patched_lib.c
done
