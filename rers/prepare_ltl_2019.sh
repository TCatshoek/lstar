#!/bin/bash

rm -rf SeqLtlRers2019

wget http://rers-challenge.org/2019/problems/sequential/SeqLtlRers2019_Mar_9th.zip
unzip SeqLtlRers2019_Mar_9th.zip
rm SeqLtlRers2019_Mar_9th.zip
rm -rf __MACOSX

cd SeqLtlRers2019 || exit

for problem in *
do
  echo compiling $problem
  python ../patchrers.py $problem/$problem.c
  python ../patchrerslib.py $problem/"${problem}"_patched.c
  python ../generate_alphabet_mapping.py "$problem"/constraints-"$problem".txt "$problem"/"$problem"_alphabet_mapping_C_version.txt
  gcc -o $problem/$problem $problem/"${problem}"_patched.c ../verifier_patched.c
  gcc -fPIC -shared -o $problem/"${problem}".so $problem/"${problem}"_patched_lib.c
done

# Get results and generate solution files for checking
wget http://rers-challenge.org/2019/results/solution-and-submissions-RERS-2019.zip
unzip solution-and-submissions-RERS-2019.zip
rm solution-and-submissions-RERS-2019.zip
python ../generate_solutions.py solution/Seq_LTL_and_Seq_Reach_solution.csv .
rm -rf solution
rm -rf participant-submissions
