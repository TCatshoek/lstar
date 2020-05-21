#!/bin/bash

rm -rf IndReachabilityRers2019

wget http://rers-challenge.org/2019/problems/industrial/IndReachabilityRers2019_mar_13th.zip
unzip IndReachabilityRers2019_mar_13th.zip
rm IndReachabilityRers2019_mar_13th.zip
rm -rf __MACOSX


for problem in IndReachabilityRers2019/arithmetic/*
do
  echo compiling $problem
  python patchrers.py "$problem/$(basename $problem)"_Reach.c
  gcc -o $problem/$(basename $problem)_Reach "$problem/$(basename $problem)"_Reach_patched.c verifier_patched.c
done
