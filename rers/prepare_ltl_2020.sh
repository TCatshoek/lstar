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
  python ../patchrers.py $problem/$problem.c
  python ../patchrerslib.py $problem/"${problem}"_patched.c
  gcc -o $problem/$problem $problem/"${problem}"_patched.c ../verifier_patched.c
  gcc -fPIC -shared -o $problem/"${problem}".so $problem/"${problem}"_patched_lib.c
done
