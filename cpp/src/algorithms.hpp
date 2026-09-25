#pragma once
#include "graph.hpp"
#include <queue>
#include <limits>
#include <functional>

namespace btc_trace {

// BFS from a source node, returns visited nodes up to max_depth
inline std::vector<uint32_t> bfs(const CSRGraph& graph, uint32_t source, uint32_t max_depth = std::numeric_limits<uint32_t>::max()) {
    std::vector<uint32_t> visited;
    std::vector<bool> seen(graph.num_nodes(), false);
    std::queue<std::pair<uint32_t, uint32_t>> q; // (node, depth)

    q.push({source, 0});
    seen[source] = true;

    while (!q.empty()) {
        auto [node, depth] = q.front();
        q.pop();
        visited.push_back(node);

        if (depth >= max_depth) continue;

        auto neighbors = graph.out_neighbors(node);
        for (uint32_t i = 0; i < neighbors.size(); i++) {
            uint32_t neighbor = neighbors.begin_ptr[i];
            if (!seen[neighbor]) {
                seen[neighbor] = true;
                q.push({neighbor, depth + 1});
            }
        }

        auto in_neighbors = graph.in_neighbors(node);
        for (uint32_t i = 0; i < in_neighbors.size(); i++) {
            uint32_t neighbor = in_neighbors.begin_ptr[i];
            if (!seen[neighbor]) {
                seen[neighbor] = true;
                q.push({neighbor, depth + 1});
            }
        }
    }

    return visited;
}

// Find connected components using BFS
inline std::vector<std::vector<uint32_t>> connected_components(const CSRGraph& graph) {
    std::vector<std::vector<uint32_t>> components;
    std::vector<bool> visited(graph.num_nodes(), false);

    for (uint32_t i = 0; i < graph.num_nodes(); i++) {
        if (!visited[i]) {
            auto component = bfs(graph, i);
            for (uint32_t node : component) {
                visited[node] = true;
            }
            components.push_back(std::move(component));
        }
    }

    return components;
}

// Bounded path search: find all paths from src to dst with max length
inline std::vector<std::vector<uint32_t>> bounded_paths(
    const CSRGraph& graph, uint32_t src, uint32_t dst,
    uint32_t max_length = 5, uint32_t max_paths = 100)
{
    std::vector<std::vector<uint32_t>> result;
    std::vector<uint32_t> current_path = {src};
    std::vector<bool> in_path(graph.num_nodes(), false);
    in_path[src] = true;

    std::function<void(uint32_t, uint32_t)> dfs = [&](uint32_t node, uint32_t depth) {
        if (result.size() >= max_paths) return;
        if (node == dst && depth > 0) {
            result.push_back(current_path);
            return;
        }
        if (depth >= max_length) return;

        auto neighbors = graph.out_neighbors(node);
        for (uint32_t i = 0; i < neighbors.size(); i++) {
            uint32_t next = neighbors.begin_ptr[i];
            if (!in_path[next]) {
                in_path[next] = true;
                current_path.push_back(next);
                dfs(next, depth + 1);
                current_path.pop_back();
                in_path[next] = false;
            }
        }
    };

    dfs(src, 0);
    return result;
}

// Compute degree statistics for a node
struct DegreeStats {
    uint32_t in_degree;
    uint32_t out_degree;
    uint32_t total_degree;
    uint32_t fan_in;   // in-degree from unique node types
    uint32_t fan_out;  // out-degree to unique node types
};

inline DegreeStats compute_degree_stats(const CSRGraph& graph, uint32_t node_id) {
    DegreeStats stats{};
    stats.in_degree = graph.in_degree(node_id);
    stats.out_degree = graph.out_degree(node_id);
    stats.total_degree = stats.in_degree + stats.out_degree;

    // Fan-in: count unique source node types
    std::unordered_set<uint8_t> in_types, out_types;
    auto in_nbrs = graph.in_neighbors(node_id);
    for (uint32_t i = 0; i < in_nbrs.size(); i++) {
        in_types.insert(static_cast<uint8_t>(graph.node(in_nbrs.begin_ptr[i]).type));
    }
    auto out_nbrs = graph.out_neighbors(node_id);
    for (uint32_t i = 0; i < out_nbrs.size(); i++) {
        out_types.insert(static_cast<uint8_t>(graph.node(out_nbrs.begin_ptr[i]).type));
    }
    stats.fan_in = static_cast<uint32_t>(in_types.size());
    stats.fan_out = static_cast<uint32_t>(out_types.size());

    return stats;
}

// Compute local clustering coefficient for a node (undirected)
inline double clustering_coefficient(const CSRGraph& graph, uint32_t node_id) {
    // Get all neighbors (both directions)
    std::unordered_set<uint32_t> neighbor_set;
    auto out_nbrs = graph.out_neighbors(node_id);
    for (uint32_t i = 0; i < out_nbrs.size(); i++) {
        neighbor_set.insert(out_nbrs.begin_ptr[i]);
    }
    auto in_nbrs = graph.in_neighbors(node_id);
    for (uint32_t i = 0; i < in_nbrs.size(); i++) {
        neighbor_set.insert(in_nbrs.begin_ptr[i]);
    }

    uint32_t k = static_cast<uint32_t>(neighbor_set.size());
    if (k < 2) return 0.0;

    // Count edges between neighbors
    uint32_t edge_count = 0;
    std::vector<uint32_t> neighbors(neighbor_set.begin(), neighbor_set.end());
    for (uint32_t i = 0; i < neighbors.size(); i++) {
        auto nbrs_of_i = graph.out_neighbors(neighbors[i]);
        for (uint32_t j = 0; j < nbrs_of_i.size(); j++) {
            if (neighbor_set.count(nbrs_of_i.begin_ptr[j])) {
                edge_count++;
            }
        }
    }

    return static_cast<double>(edge_count) / (static_cast<double>(k) * (k - 1));
}

} // namespace btc_trace
