from ctypes import *

so_file = "/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem11/Problem11.so"

problem11 = CDLL(so_file)
problem11.reset.restype = None
problem11.calculate_output.argtypes = [c_int]
problem11.calculate_output.restype = c_int

problem11.reset()
problem11.calculate_output(4)