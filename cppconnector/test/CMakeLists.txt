# 'Google_test' is the subproject name
project(Google_tests)

# 'lib' is the folder with Google Test sources
add_subdirectory(googletest)
include_directories(${gtest_SOURCE_DIR}/include ${gtest_SOURCE_DIR} ../src)

# 'Google_Tests_run' is the target name
# 'test1.cpp tests2.cpp' are source files with tests
add_executable(Google_Tests_run
        test_trie.cpp
        test_connector.cpp
        ../src/RERSConnectorV3.h
        ../src/RERSConnectorV3.cpp
        ../src/Trie.cpp
        ../src/Trie.h
        )
target_link_libraries(Google_Tests_run gtest gtest_main)