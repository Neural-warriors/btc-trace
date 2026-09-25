#include "../src/io.hpp"
#include "../src/features.hpp"
#include <chrono>
#include <iostream>
#include <fstream>
#include <random>

using namespace btc_trace;

// Generate a synthetic CSV for benchmarking
void generate_bench_csv(const std::string& path, uint32_t num_rows) {
    std::ofstream file(path);
    file << "txid,src_ip,dst_ip,input_addresses,output_addresses,geo_country,asn\n";

    std::mt19937 rng(42);
    std::uniform_int_distribution<int> ip_dist(1, 255);
    std::uniform_int_distribution<int> wallet_dist(1, 5000);
    std::uniform_int_distribution<int> asn_dist(1, 100);
    const char* countries[] = {"US","UK","DE","FR","JP","CN","RU","BR","IN","AU"};

    for (uint32_t i = 0; i < num_rows; i++) {
        // txid
        file << std::hex;
        for (int j = 0; j < 8; j++) file << rng();
        file << std::dec << ",";

        // src_ip, dst_ip
        file << ip_dist(rng) << "." << ip_dist(rng) << "." << ip_dist(rng) << "." << ip_dist(rng) << ",";
        file << ip_dist(rng) << "." << ip_dist(rng) << "." << ip_dist(rng) << "." << ip_dist(rng) << ",";

        // input_addresses (1-3)
        int n_in = 1 + rng() % 3;
        for (int j = 0; j < n_in; j++) {
            if (j > 0) file << ";";
            file << "1Addr" << wallet_dist(rng);
        }
        file << ",";

        // output_addresses (1-5)
        int n_out = 1 + rng() % 5;
        for (int j = 0; j < n_out; j++) {
            if (j > 0) file << ";";
            file << "1Addr" << wallet_dist(rng);
        }
        file << ",";

        // country, asn
        file << countries[rng() % 10] << ",AS" << asn_dist(rng) << "\n";
    }
}

int main() {
    std::cout << "=== BTC-TRACE Graph Benchmarks ===\n\n";

    const uint32_t NUM_ROWS = 10000;
    const std::string bench_csv = "/tmp/btc_trace_bench.csv";

    // Generate benchmark data
    std::cout << "Generating " << NUM_ROWS << " synthetic rows...\n";
    auto t0 = std::chrono::high_resolution_clock::now();
    generate_bench_csv(bench_csv, NUM_ROWS);
    auto t1 = std::chrono::high_resolution_clock::now();
    auto gen_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();
    std::cout << "  Generation: " << gen_ms << " ms\n\n";

    // Benchmark graph loading
    std::cout << "Loading graph from CSV...\n";
    auto t2 = std::chrono::high_resolution_clock::now();
    auto graph = load_transaction_csv(bench_csv);
    auto t3 = std::chrono::high_resolution_clock::now();
    auto load_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t3 - t2).count();
    std::cout << "  Load time: " << load_ms << " ms\n";
    std::cout << "  Nodes: " << graph.num_nodes() << "\n";
    std::cout << "  Edges: " << graph.num_edges() << "\n";
    std::cout << "  Rate: " << (NUM_ROWS * 1000 / std::max(load_ms, (long long)1)) << " rows/sec\n\n";

    // Benchmark feature extraction
    std::cout << "Extracting graph features...\n";
    auto t4 = std::chrono::high_resolution_clock::now();
    auto features = extract_graph_features(graph);
    auto t5 = std::chrono::high_resolution_clock::now();
    auto feat_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t5 - t4).count();
    std::cout << "  Feature extraction: " << feat_ms << " ms\n";
    std::cout << "  Features per node: 12\n";
    std::cout << "  Total feature rows: " << features.size() << "\n\n";

    // Benchmark connected components
    std::cout << "Computing connected components...\n";
    auto t6 = std::chrono::high_resolution_clock::now();
    auto components = connected_components(graph);
    auto t7 = std::chrono::high_resolution_clock::now();
    auto comp_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t7 - t6).count();
    std::cout << "  Component detection: " << comp_ms << " ms\n";
    std::cout << "  Components: " << components.size() << "\n\n";

    // Benchmark BFS
    std::cout << "Running BFS (depth 3) from first node...\n";
    auto t8 = std::chrono::high_resolution_clock::now();
    auto bfs_result = bfs(graph, 0, 3);
    auto t9 = std::chrono::high_resolution_clock::now();
    auto bfs_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t9 - t8).count();
    std::cout << "  BFS time: " << bfs_ms << " ms\n";
    std::cout << "  Reachable nodes: " << bfs_result.size() << "\n\n";

    // Memory estimate
    size_t mem_nodes = graph.num_nodes() * sizeof(Node);
    size_t mem_estimate = mem_nodes + graph.num_edges() * 3 * sizeof(uint32_t);
    std::cout << "Estimated memory: " << (mem_estimate / 1024 / 1024) << " MB\n\n";

    // Summary
    std::cout << "=== Benchmark Summary ===\n";
    std::cout << "Graph load:     " << load_ms << " ms\n";
    std::cout << "Feature extract:" << feat_ms << " ms\n";
    std::cout << "Components:     " << comp_ms << " ms\n";
    std::cout << "BFS (depth 3):  " << bfs_ms << " ms\n";

    // Cleanup
    std::remove(bench_csv.c_str());

    return 0;
}
