cmake_minimum_required(VERSION 3.16)
project(btc_trace_graph VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Optimization flags
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -fsanitize=address")

# Main library
add_library(btc_graph STATIC
    src/graph.cpp
    src/algorithms.cpp
    src/features.cpp
    src/io.cpp
)
target_include_directories(btc_graph PUBLIC src/)

# CLI executable
add_executable(btc_graph_cli src/main.cpp)
target_link_libraries(btc_graph_cli PRIVATE btc_graph)

# Tests
enable_testing()
add_executable(test_graph tests/test_graph.cpp)
target_link_libraries(test_graph PRIVATE btc_graph)
add_test(NAME GraphTests COMMAND test_graph)

# Benchmark
add_executable(bench_graph tests/bench_graph.cpp)
target_link_libraries(bench_graph PRIVATE btc_graph)

# Install
install(TARGETS btc_graph_cli DESTINATION bin)
