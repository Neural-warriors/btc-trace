#pragma once
#include "graph.hpp"
#include "algorithms.hpp"
#include <vector>
#include <cmath>

namespace btc_trace {

// Per-node feature vector for ML
struct NodeFeatures {
    uint32_t node_id;
    NodeType node_type;
    uint32_t in_degree;
    uint32_t out_degree;
    uint32_t total_degree;
    uint32_t fan_in;
    uint32_t fan_out;
    double   clustering_coeff;
    uint32_t component_size;
    uint32_t component_id;
    // Normalized versions
    double   in_degree_norm;
    double   out_degree_norm;
    double   degree_ratio;  // out / (in + out)
};

// Extract features for all nodes in the graph
inline std::vector<NodeFeatures> extract_graph_features(const CSRGraph& graph) {
    std::vector<NodeFeatures> features(graph.num_nodes());

    // Compute connected components
    auto components = connected_components(graph);
    std::vector<uint32_t> comp_id(graph.num_nodes());
    std::vector<uint32_t> comp_size(graph.num_nodes());
    for (uint32_t c = 0; c < components.size(); c++) {
        for (uint32_t node : components[c]) {
            comp_id[node] = c;
            comp_size[node] = static_cast<uint32_t>(components[c].size());
        }
    }

    // Find max degree for normalization
    uint32_t max_degree = 1;
    for (uint32_t i = 0; i < graph.num_nodes(); i++) {
        uint32_t d = graph.in_degree(i) + graph.out_degree(i);
        if (d > max_degree) max_degree = d;
    }

    // Extract features per node
    for (uint32_t i = 0; i < graph.num_nodes(); i++) {
        auto& f = features[i];
        f.node_id = i;
        f.node_type = graph.node(i).type;

        auto ds = compute_degree_stats(graph, i);
        f.in_degree = ds.in_degree;
        f.out_degree = ds.out_degree;
        f.total_degree = ds.total_degree;
        f.fan_in = ds.fan_in;
        f.fan_out = ds.fan_out;

        f.clustering_coeff = clustering_coefficient(graph, i);
        f.component_size = comp_size[i];
        f.component_id = comp_id[i];

        f.in_degree_norm = static_cast<double>(f.in_degree) / max_degree;
        f.out_degree_norm = static_cast<double>(f.out_degree) / max_degree;
        f.degree_ratio = (f.total_degree > 0)
            ? static_cast<double>(f.out_degree) / f.total_degree
            : 0.0;
    }

    return features;
}

// Extract features for nodes of a specific type only
inline std::vector<NodeFeatures> extract_features_for_type(const CSRGraph& graph, NodeType type) {
    auto all_features = extract_graph_features(graph);
    std::vector<NodeFeatures> typed;
    for (const auto& f : all_features) {
        if (f.node_type == type) {
            typed.push_back(f);
        }
    }
    return typed;
}

} // namespace btc_trace
