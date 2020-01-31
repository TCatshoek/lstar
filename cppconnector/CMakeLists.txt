cmake_minimum_required(VERSION 2.8.12)
project(connector)

set(CMAKE_CXX_FLAGS "-O3 -fpermissive")
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Build the python bindings
add_subdirectory(pybind11)
pybind11_add_module(connector
        src/connector_py.cpp
        src/RERSConnectorV3.cpp
        src/RERSConnectorV3.h
        src/subprocess.hpp
        src/Trie.cpp
        src/Trie.h
        )

pybind11_add_module(trie
        src/trie_py.cpp
        src/Trie.cpp
        src/Trie.h
        )

# Add googletest directly to our build. This defines
# the gtest and gtest_main targets.
add_subdirectory(test)
