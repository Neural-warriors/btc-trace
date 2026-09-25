#include "io.hpp"
#include "features.hpp"
#include <iostream>
#include <chrono>
#include <string>

using namespace btc_trace;

void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " <command> [options]\n"
              << "\nCommands:\n"
              << "  build <input.csv> <output_prefix>  Build graph and extract features\n"
              << "  info  <input.csv>                  Show graph statistics\n"
              << "  query <input.csv> <entity_label>   Query entity neighborhood\n"
              << std::endl;
}

int cmd_build(const std::string& input, const std::string& prefix) {
    auto t0 = std::chrono::high_resolution_clock::now();

    auto graph = load_transaction_csv(input);

    auto t1 = std::chrono::high_resolution_clock::now();
    auto load_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();
    std::cout << "Graph loaded in " << load_ms << " ms\n";
    std::cout << "  Nodes: " << graph.num_nodes() << "\n";
    std::cout << "  Edges: " << graph.num_edges() << "\n";

    // Extract features
    auto features = extract_graph_features(graph);

    auto t2 = std::chrono::high_resolution_clock::now();
    auto feat_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
    std::cout << "Features extracted in " << feat_ms << " ms\n";

    // Export
    export_features_csv(prefix + "_features.csv", graph, features);
    export_edgelist_csv(prefix + "_edgelist.csv", graph);

    // Component stats
    auto components = connected_components(graph);
    std::cout << "Connected components: " << components.size() << "\n";

    // Type distribution
    uint32_t n_tx = 0, n_wallet = 0, n_ip = 0, n_asn = 0, n_country = 0;
    for (uint32_t i = 0; i < graph.num_nodes(); i++) {
        switch (graph.node(i).type) {
            case NodeType::Transaction: n_tx++; break;
            case NodeType::Wallet:      n_wallet++; break;
            case NodeType::IP:          n_ip++; break;
            case NodeType::ASN:         n_asn++; break;
            case NodeType::Country:     n_country++; break;
        }
    }
    std::cout << "Node types: TX=" << n_tx << " Wallet=" << n_wallet
              << " IP=" << n_ip << " ASN=" << n_asn
              << " Country=" << n_country << "\n";

    auto t3 = std::chrono::high_resolution_clock::now();
    auto total_ms = std::chrono::duration_cast<std::chrono::milliseconds>(t3 - t0).count();
    std::cout << "Total time: " << total_ms << " ms\n";

    return 0;
}

int cmd_info(const std::string& input) {
    auto graph = load_transaction_csv(input);
    std::cout << "Nodes: " << graph.num_nodes() << "\n";
    std::cout << "Edges: " << graph.num_edges() << "\n";

    auto components = connected_components(graph);
    std::cout << "Connected components: " << components.size() << "\n";

    // Find largest component
    size_t max_comp = 0;
    for (const auto& c : components) {
        max_comp = std::max(max_comp, c.size());
    }
    std::cout << "Largest component: " << max_comp << " nodes\n";

    return 0;
}

int cmd_query(const std::string& input, const std::string& label) {
    auto graph = load_transaction_csv(input);

    if (!graph.has_node(label)) {
        std::cerr << "Entity not found: " << label << "\n";
        return 1;
    }

    uint32_t node_id = graph.find_node(label);
    const auto& node = graph.node(node_id);
    std::cout << "Entity: " << node.label << "\n";
    std::cout << "Type: " << node_type_str(node.type) << "\n";
    std::cout << "ID: " << node.id << "\n";

    auto stats = compute_degree_stats(graph, node_id);
    std::cout << "In-degree: " << stats.in_degree << "\n";
    std::cout << "Out-degree: " << stats.out_degree << "\n";
    std::cout << "Fan-in: " << stats.fan_in << "\n";
    std::cout << "Fan-out: " << stats.fan_out << "\n";
    std::cout << "Clustering coefficient: " << clustering_coefficient(graph, node_id) << "\n";

    // Show neighborhood (1-hop BFS)
    auto neighborhood = bfs(graph, node_id, 1);
    std::cout << "\nNeighborhood (1-hop): " << neighborhood.size() << " nodes\n";
    for (uint32_t n : neighborhood) {
        if (n == node_id) continue;
        const auto& nbr = graph.node(n);
        std::cout << "  " << node_type_str(nbr.type) << ": " << nbr.label << "\n";
    }

    return 0;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    std::string cmd = argv[1];

    if (cmd == "build" && argc >= 4) {
        return cmd_build(argv[2], argv[3]);
    } else if (cmd == "info" && argc >= 3) {
        return cmd_info(argv[2]);
    } else if (cmd == "query" && argc >= 4) {
        return cmd_query(argv[2], argv[3]);
    } else {
        print_usage(argv[0]);
        return 1;
    }
}
