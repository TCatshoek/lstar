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
  python ../patchrers.py $problem/$problem.c
  python ../patchrerslib.py $problem/"${problem}"_patched.c
  gcc -o $problem/$problem $problem/"${problem}"_patched.c ../verifier_patched.c
  gcc -fPIC -shared -o $problem/"${problem}".so $problem/"${problem}"_patched_lib.c
done
