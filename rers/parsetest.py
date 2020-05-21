from pycparser import c_parser, parse_file

text = r"""
void func(void)
{
  x = 1;
}
"""

path = "/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem11/Problem11.c"

f = parse_file(path, use_cpp=True,
            cpp_path='gcc',
            cpp_args=['-nostdinc', '-E', r'-I/tmp/pycparser/utils/fake_libc_include'])

ast = f
print("Before:")
ast.show(offset=2)

assign = ast.ext[0].body.block_items[0]
assign.lvalue.name = "y"
assign.rvalue.value = 2

print("After:")
ast.show(offset=2)