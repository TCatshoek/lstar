#!/bin/bash

rm -rf TrainingSeqLtlRers2019

wget http://www.rers-challenge.org/2019/problems/sequential/TrainingSeqLtlRers2019.zip
unzip TrainingSeqLtlRers2019.zip
rm TrainingSeqLtlRers2019.zip
rm -rf __MACOSX

cd TrainingSeqLtlRers2019 || exit

for problem in *
do
  echo compiling $problem
  python ../patchrers.py $problem/$problem.c
  python ../patchrerslib.py $problem/"${problem}"_patched.c
  python ../generate_alphabet_mapping.py "$problem"/constraints-"$problem".txt "$problem"/"$problem"_alphabet_mapping_C_version.txt
  gcc -o $problem/$problem $problem/"${problem}"_patched.c ../verifier_patched.c
  gcc -fPIC -shared -o $problem/"${problem}".so $problem/"${problem}"_patched_lib.c
done
