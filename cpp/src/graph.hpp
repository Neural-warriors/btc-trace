#pragma once
#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <memory>
#include <stdexcept>
#include <algorithm>
#include <numeric>
#include <cassert>

namespace btc_trace {

// Entity types in the investigation graph
enum class NodeType : uint8_t {
    Transaction = 0,
    Wallet      = 1,
    IP          = 2,
    ASN         = 3,
    Country     = 4
};

// Edge relationship types
enum class EdgeType : uint8_t {
    OBSERVED_WITH   = 0,  // IP -> Transaction
    INPUT_FROM      = 1,  // Transaction -> Wallet (input)
    OUTPUT_TO       = 2,  // Transaction -> Wallet (output)
    BELONGS_TO      = 3,  // IP -> ASN
    LOCATED_IN      = 4,  // IP -> Country
    CO_SPENT_WITH   = 5   // Wallet -> Wallet (co-spending evidence)
};

inline const char* node_type_str(NodeType t) {
    switch(t) {
        case NodeType::Transaction: return "transaction";
        case NodeType::Wallet:      return "wallet";
        case NodeType::IP:          return "ip";
        case NodeType::ASN:         return "asn";
        case NodeType::Country:     return "country";
        default:                    return "unknown";
    }
}

inline const char* edge_type_str(EdgeType t) {
    switch(t) {
        case EdgeType::OBSERVED_WITH: return "OBSERVED_WITH";
        case EdgeType::INPUT_FROM:    return "INPUT_FROM";
        case EdgeType::OUTPUT_TO:     return "OUTPUT_TO";
        case EdgeType::BELONGS_TO:    return "BELONGS_TO";
        case EdgeType::LOCATED_IN:    return "LOCATED_IN";
        case EdgeType::CO_SPENT_WITH: return "CO_SPENT_WITH";
        default:                      return "UNKNOWN";
    }
}

struct Node {
    uint32_t id;
    NodeType type;
    std::string label;  // original identifier (txid, wallet addr, IP, etc.)
};

struct Edge {
    uint32_t src;
    uint32_t dst;
    EdgeType type;
    float    weight;
};

// CSR (Compressed Sparse Row) graph representation for efficient traversal
class CSRGraph {
public:
    CSRGraph() = default;

    // Build from edge list
    void build(uint32_t num_nodes,
               const std::vector<Node>& nodes,
               const std::vector<Edge>& edges) {
        num_nodes_ = num_nodes;
        nodes_ = nodes;
        num_edges_ = static_cast<uint32_t>(edges.size());

        // Build forward CSR (outgoing edges)
        row_ptr_.assign(num_nodes + 1, 0);
        for (const auto& e : edges) {
            row_ptr_[e.src + 1]++;
        }
        for (uint32_t i = 1; i <= num_nodes; i++) {
            row_ptr_[i] += row_ptr_[i - 1];
        }

        col_idx_.resize(num_edges_);
        edge_types_.resize(num_edges_);
        edge_weights_.resize(num_edges_);
        std::vector<uint32_t> offset(num_nodes, 0);
        for (const auto& e : edges) {
            uint32_t pos = row_ptr_[e.src] + offset[e.src];
            col_idx_[pos] = e.dst;
            edge_types_[pos] = e.type;
            edge_weights_[pos] = e.weight;
            offset[e.src]++;
        }

        // Build reverse CSR (incoming edges)
        rev_row_ptr_.assign(num_nodes + 1, 0);
        for (const auto& e : edges) {
            rev_row_ptr_[e.dst + 1]++;
        }
        for (uint32_t i = 1; i <= num_nodes; i++) {
            rev_row_ptr_[i] += rev_row_ptr_[i - 1];
        }

        rev_col_idx_.resize(num_edges_);
        rev_edge_types_.resize(num_edges_);
        std::fill(offset.begin(), offset.end(), 0);
        for (const auto& e : edges) {
            uint32_t pos = rev_row_ptr_[e.dst] + offset[e.dst];
            rev_col_idx_[pos] = e.src;
            rev_edge_types_[pos] = e.type;
            offset[e.dst]++;
        }

        // Build label-to-id map
        for (const auto& n : nodes_) {
            label_to_id_[n.label] = n.id;
        }
    }

    uint32_t num_nodes() const { return num_nodes_; }
    uint32_t num_edges() const { return num_edges_; }

    const Node& node(uint32_t id) const { return nodes_[id]; }

    // Out-degree
    uint32_t out_degree(uint32_t node_id) const {
        return row_ptr_[node_id + 1] - row_ptr_[node_id];
    }

    // In-degree
    uint32_t in_degree(uint32_t node_id) const {
        return rev_row_ptr_[node_id + 1] - rev_row_ptr_[node_id];
    }

    // Outgoing neighbors
    struct NeighborRange {
        const uint32_t* begin_ptr;
        const uint32_t* end_ptr;
        const EdgeType* types_ptr;
        const float*    weights_ptr;
        uint32_t size() const { return static_cast<uint32_t>(end_ptr - begin_ptr); }
        const uint32_t* begin() const { return begin_ptr; }
        const uint32_t* end() const { return end_ptr; }
    };

    NeighborRange out_neighbors(uint32_t node_id) const {
        uint32_t start = row_ptr_[node_id];
        uint32_t end = row_ptr_[node_id + 1];
        return {
            col_idx_.data() + start,
            col_idx_.data() + end,
            edge_types_.data() + start,
            edge_weights_.data() + start
        };
    }

    NeighborRange in_neighbors(uint32_t node_id) const {
        uint32_t start = rev_row_ptr_[node_id];
        uint32_t end = rev_row_ptr_[node_id + 1];
        return {
            rev_col_idx_.data() + start,
            rev_col_idx_.data() + end,
            rev_edge_types_.data() + start,
            nullptr
        };
    }

    // Lookup by label
    uint32_t find_node(const std::string& label) const {
        auto it = label_to_id_.find(label);
        if (it == label_to_id_.end()) {
            throw std::runtime_error("Node not found: " + label);
        }
        return it->second;
    }

    bool has_node(const std::string& label) const {
        return label_to_id_.count(label) > 0;
    }

    // Get all nodes of a specific type
    std::vector<uint32_t> nodes_of_type(NodeType type) const {
        std::vector<uint32_t> result;
        for (const auto& n : nodes_) {
            if (n.type == type) result.push_back(n.id);
        }
        return result;
    }

private:
    uint32_t num_nodes_ = 0;
    uint32_t num_edges_ = 0;
    std::vector<Node> nodes_;

    // Forward CSR
    std::vector<uint32_t> row_ptr_;
    std::vector<uint32_t> col_idx_;
    std::vector<EdgeType> edge_types_;
    std::vector<float>    edge_weights_;

    // Reverse CSR
    std::vector<uint32_t> rev_row_ptr_;
    std::vector<uint32_t> rev_col_idx_;
    std::vector<EdgeType> rev_edge_types_;

    // Label lookup
    std::unordered_map<std::string, uint32_t> label_to_id_;
};

// Graph builder for incremental construction
class GraphBuilder {
public:
    uint32_t add_node(NodeType type, const std::string& label) {
        auto it = label_to_id_.find(label);
        if (it != label_to_id_.end()) return it->second;

        uint32_t id = static_cast<uint32_t>(nodes_.size());
        nodes_.push_back({id, type, label});
        label_to_id_[label] = id;
        return id;
    }

    void add_edge(uint32_t src, uint32_t dst, EdgeType type, float weight = 1.0f) {
        edges_.push_back({src, dst, type, weight});
    }

    uint32_t find_or_add(NodeType type, const std::string& label) {
        return add_node(type, label);
    }

    CSRGraph build() const {
        CSRGraph g;
        g.build(static_cast<uint32_t>(nodes_.size()), nodes_, edges_);
        return g;
    }

    uint32_t num_nodes() const { return static_cast<uint32_t>(nodes_.size()); }
    uint32_t num_edges() const { return static_cast<uint32_t>(edges_.size()); }

private:
    std::vector<Node> nodes_;
    std::vector<Edge> edges_;
    std::unordered_map<std::string, uint32_t> label_to_id_;
};

} // namespace btc_trace
