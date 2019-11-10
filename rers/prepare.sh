#!/bin/bash

#rm -rf SeqReachabilityRers2019
#
#wget http://rers-challenge.org/2019/problems/sequential/SeqReachabilityRers2019_Mar_9th.zip
#unzip SeqReachabilityRers2019_Mar_9th.zip
#rm SeqReachabilityRers2019_Mar_9th.zip
#rm -rf __MACOSX

cd SeqReachabilityRers2019

for problem in *
do
  echo compiling $problem
  gcc -o $problem/$problem $problem/$problem.c ../verifier.c
done
