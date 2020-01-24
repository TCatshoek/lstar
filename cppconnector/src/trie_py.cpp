#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <iostream>
#include "Trie.h"

namespace py = pybind11;

PYBIND11_MODULE(trie, m) {
    py::class_<Trie>(m, "Trie")
            .def(py::init<std::vector<std::string>, char>())
            .def("get", &Trie::get)
            .def("put", &Trie::put)
            .def("__getitem__", &Trie::get)
            .def("__setitem__", &Trie::put),


#ifdef VERSION_INFO
                    m.attr("__version__") = VERSION_INFO;
#else
                    m.attr("__version__") = "dev";
#endif
}