#!/bin/bash

#rm -rf IndReachabilityRers2019
#
#wget http://rers-challenge.org/2019/problems/industrial/IndReachabilityRers2019_mar_13th.zip
#unzip IndReachabilityRers2019_mar_13th.zip
#rm IndReachabilityRers2019_mar_13th.zip
#rm -rf __MACOSX
#
#cd IndReachabilityRers2019

for problem in IndReachabilityRers2019/arithmetic/*
do
  echo compiling $problem
  gcc -o $problem/$(basename $problem) "$problem/$(basename $problem)"_Reach.c verifier.c
done
