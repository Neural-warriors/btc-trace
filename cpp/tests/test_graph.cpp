#include "../src/graph.hpp"
#include "../src/algorithms.hpp"
#include "../src/features.hpp"
#include "../src/io.hpp"
#include <cassert>
#include <iostream>
#include <sstream>

using namespace btc_trace;

void test_graph_builder() {
    std::cout << "test_graph_builder... ";

    GraphBuilder builder;
    uint32_t tx = builder.add_node(NodeType::Transaction, "tx001");
    uint32_t w1 = builder.add_node(NodeType::Wallet, "1ABC");
    uint32_t w2 = builder.add_node(NodeType::Wallet, "1DEF");
    uint32_t ip = builder.add_node(NodeType::IP, "192.168.1.1");
    uint32_t asn = builder.add_node(NodeType::ASN, "AS1234");
    uint32_t country = builder.add_node(NodeType::Country, "US");

    builder.add_edge(ip, tx, EdgeType::OBSERVED_WITH);
    builder.add_edge(tx, w1, EdgeType::INPUT_FROM);
    builder.add_edge(tx, w2, EdgeType::OUTPUT_TO);
    builder.add_edge(ip, asn, EdgeType::BELONGS_TO);
    builder.add_edge(ip, country, EdgeType::LOCATED_IN);

    assert(builder.num_nodes() == 6);
    assert(builder.num_edges() == 5);

    // Test duplicate node prevention
    uint32_t w1_dup = builder.add_node(NodeType::Wallet, "1ABC");
    assert(w1_dup == w1);
    assert(builder.num_nodes() == 6);

    auto graph = builder.build();
    assert(graph.num_nodes() == 6);
    assert(graph.num_edges() == 5);

    std::cout << "PASS\n";
}

void test_csr_graph() {
    std::cout << "test_csr_graph... ";

    GraphBuilder builder;
    uint32_t a = builder.add_node(NodeType::Transaction, "A");
    uint32_t b = builder.add_node(NodeType::Wallet, "B");
    uint32_t c = builder.add_node(NodeType::Wallet, "C");

    builder.add_edge(a, b, EdgeType::OUTPUT_TO);
    builder.add_edge(a, c, EdgeType::OUTPUT_TO);
    builder.add_edge(b, c, EdgeType::CO_SPENT_WITH);

    auto graph = builder.build();

    assert(graph.out_degree(a) == 2);
    assert(graph.out_degree(b) == 1);
    assert(graph.in_degree(b) == 1);
    assert(graph.in_degree(c) == 2);

    assert(graph.has_node("A"));
    assert(graph.has_node("B"));
    assert(!graph.has_node("D"));

    assert(graph.find_node("A") == a);

    auto tx_nodes = graph.nodes_of_type(NodeType::Transaction);
    assert(tx_nodes.size() == 1);

    auto wallet_nodes = graph.nodes_of_type(NodeType::Wallet);
    assert(wallet_nodes.size() == 2);

    std::cout << "PASS\n";
}

void test_bfs() {
    std::cout << "test_bfs... ";

    GraphBuilder builder;
    uint32_t a = builder.add_node(NodeType::Transaction, "A");
    uint32_t b = builder.add_node(NodeType::Wallet, "B");
    uint32_t c = builder.add_node(NodeType::Wallet, "C");
    uint32_t d = builder.add_node(NodeType::IP, "D");

    builder.add_edge(a, b, EdgeType::OUTPUT_TO);
    builder.add_edge(b, c, EdgeType::CO_SPENT_WITH);
    builder.add_edge(a, d, EdgeType::OBSERVED_WITH);

    auto graph = builder.build();

    auto result = bfs(graph, a);
    assert(result.size() == 4);  // All nodes reachable

    auto result_depth1 = bfs(graph, a, 1);
    assert(result_depth1.size() == 3);  // A, B, D

    std::cout << "PASS\n";
}

void test_connected_components() {
    std::cout << "test_connected_components... ";

    GraphBuilder builder;
    // Component 1: A-B-C
    uint32_t a = builder.add_node(NodeType::Transaction, "A");
    uint32_t b = builder.add_node(NodeType::Wallet, "B");
    uint32_t c = builder.add_node(NodeType::Wallet, "C");
    builder.add_edge(a, b, EdgeType::OUTPUT_TO);
    builder.add_edge(b, c, EdgeType::CO_SPENT_WITH);

    // Component 2: D-E (isolated)
    uint32_t d = builder.add_node(NodeType::IP, "D");
    uint32_t e = builder.add_node(NodeType::ASN, "E");
    builder.add_edge(d, e, EdgeType::BELONGS_TO);

    auto graph = builder.build();
    auto comps = connected_components(graph);
    assert(comps.size() == 2);

    std::cout << "PASS\n";
}

void test_bounded_paths() {
    std::cout << "test_bounded_paths... ";

    GraphBuilder builder;
    uint32_t a = builder.add_node(NodeType::Transaction, "A");
    uint32_t b = builder.add_node(NodeType::Wallet, "B");
    uint32_t c = builder.add_node(NodeType::Wallet, "C");
    uint32_t d = builder.add_node(NodeType::Transaction, "D");

    builder.add_edge(a, b, EdgeType::OUTPUT_TO);
    builder.add_edge(b, c, EdgeType::CO_SPENT_WITH);
    builder.add_edge(c, d, EdgeType::INPUT_FROM);
    builder.add_edge(a, c, EdgeType::OUTPUT_TO);  // Shortcut

    auto graph = builder.build();
    auto paths = bounded_paths(graph, a, d, 5);
    assert(paths.size() >= 1);  // At least one path A->...->D

    std::cout << "PASS\n";
}

void test_degree_stats() {
    std::cout << "test_degree_stats... ";

    GraphBuilder builder;
    uint32_t center = builder.add_node(NodeType::Transaction, "center");
    for (int i = 0; i < 5; i++) {
        uint32_t w = builder.add_node(NodeType::Wallet, "w" + std::to_string(i));
        builder.add_edge(center, w, EdgeType::OUTPUT_TO);
    }
    for (int i = 0; i < 3; i++) {
        uint32_t ip = builder.add_node(NodeType::IP, "ip" + std::to_string(i));
        builder.add_edge(ip, center, EdgeType::OBSERVED_WITH);
    }

    auto graph = builder.build();
    auto stats = compute_degree_stats(graph, center);

    assert(stats.out_degree == 5);
    assert(stats.in_degree == 3);
    assert(stats.total_degree == 8);
    assert(stats.fan_out >= 1);  // At least Wallet type
    assert(stats.fan_in >= 1);   // At least IP type

    std::cout << "PASS\n";
}

void test_clustering_coefficient() {
    std::cout << "test_clustering_coefficient... ";

    GraphBuilder builder;
    uint32_t a = builder.add_node(NodeType::Wallet, "A");
    uint32_t b = builder.add_node(NodeType::Wallet, "B");
    uint32_t c = builder.add_node(NodeType::Wallet, "C");

    // Complete triangle
    builder.add_edge(a, b, EdgeType::CO_SPENT_WITH);
    builder.add_edge(b, c, EdgeType::CO_SPENT_WITH);
    builder.add_edge(a, c, EdgeType::CO_SPENT_WITH);

    auto graph = builder.build();
    double cc = clustering_coefficient(graph, a);
    assert(cc > 0.0);  // Triangle should have non-zero clustering

    std::cout << "PASS\n";
}

void test_features() {
    std::cout << "test_features... ";

    GraphBuilder builder;
    uint32_t tx = builder.add_node(NodeType::Transaction, "tx1");
    uint32_t w1 = builder.add_node(NodeType::Wallet, "w1");
    uint32_t w2 = builder.add_node(NodeType::Wallet, "w2");
    uint32_t ip = builder.add_node(NodeType::IP, "ip1");

    builder.add_edge(ip, tx, EdgeType::OBSERVED_WITH);
    builder.add_edge(tx, w1, EdgeType::INPUT_FROM);
    builder.add_edge(tx, w2, EdgeType::OUTPUT_TO);

    auto graph = builder.build();
    auto features = extract_graph_features(graph);

    assert(features.size() == 4);
    for (const auto& f : features) {
        assert(f.total_degree == f.in_degree + f.out_degree);
        assert(f.degree_ratio >= 0.0 && f.degree_ratio <= 1.0);
        assert(f.in_degree_norm >= 0.0 && f.in_degree_norm <= 1.0);
    }

    std::cout << "PASS\n";
}

void test_csv_parser() {
    std::cout << "test_csv_parser... ";

    auto fields = parse_csv_line("hello,world,\"quoted,field\",last");
    assert(fields.size() == 4);
    assert(fields[0] == "hello");
    assert(fields[1] == "world");
    assert(fields[2] == "quoted,field");
    assert(fields[3] == "last");

    auto empty = parse_csv_line("");
    assert(empty.size() == 1);
    assert(empty[0] == "");

    std::cout << "PASS\n";
}

int main() {
    std::cout << "=== BTC-TRACE Graph Engine Tests ===\n\n";

    test_graph_builder();
    test_csr_graph();
    test_bfs();
    test_connected_components();
    test_bounded_paths();
    test_degree_stats();
    test_clustering_coefficient();
    test_features();
    test_csv_parser();

    std::cout << "\n=== All tests passed! ===\n";
    return 0;
}
