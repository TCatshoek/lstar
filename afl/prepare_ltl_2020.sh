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
  python ../patchrersafl.py "$problem"/"$problem".c
  afl-clang-fast -o "$problem"/"$problem" "$problem"/"$problem"_afl.c ../verifier.c
  mkdir "$problem"/input
  echo 0 > "$problem"/input/0.txt
done
