from .bfs import program as bfs
from .reach import program as reach
from .sparse_path import program as sparse_path
from .tc_bin import program as tc_bin
from .tc_linear_left import program as tc_linear_left
from .tc_linear_right import program as tc_linear_right
from .tc_nonlinear import program as tc_nonlinear
from .triangles import program as triangles

PROGRAMS = {"bfs": bfs, "reach": reach, "sparse_path": sparse_path, "tc_bin": tc_bin, "tc_linear_left": tc_linear_left,
            "tc_linear_right": tc_linear_right, "tc_nonlinear": tc_nonlinear, "triangles": triangles}
