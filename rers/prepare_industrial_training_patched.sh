#!/bin/bash

#rm -rf rers_19_industrial_reachability_training
#
#wget http://rers-challenge.org/2019/problems/industrial/rers_19_industrial_reachability_training_Mar_13th.zip
#unzip rers_19_industrial_reachability_training_Mar_13th.zip
#rm rers_19_industrial_reachability_training_Mar_13th.zip
#rm -rf __MACOSX


for problem in rers_19_industrial_reachability_training/arithmetic/*
do
  echo compiling $problem
  python patchrers.py "$problem/$(basename $problem)"_Reach.c
  gcc -o $problem/$(basename $problem)_Reach "$problem/$(basename $problem)"_Reach_patched.c verifier_patched.c
done
