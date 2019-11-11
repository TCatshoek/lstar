#!/bin/bash

rm -rf TrainingSeqReachRers2019

wget http://rers-challenge.org/2019/problems/sequential/TrainingSeqReachRers2019.zip
unzip TrainingSeqReachRers2019.zip
rm TrainingSeqReachRers2019.zip
rm -rf __MACOSX

cd TrainingSeqReachRers2019

for problem in *
do
  echo compiling $problem
  gcc -o $problem/$problem $problem/$problem.c ../verifier.c
done
