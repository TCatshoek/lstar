#include <pybind11/pybind11.h>
#include <iostream>
#include "RERSConnectorV3.h"

namespace py = pybind11;

PYBIND11_MODULE(connector, m) {
    py::class_<RERSConnectorV3>(m, "RERSConnectorV3")
            .def(py::init<std::string &>())
            .def("interact", &RERSConnectorV3::interact)
            .def("interact_fast", &RERSConnectorV3::interact_fast),


#ifdef VERSION_INFO
    m.attr("__version__") = VERSION_INFO;
#else
    m.attr("__version__") = "dev";
#endif
}