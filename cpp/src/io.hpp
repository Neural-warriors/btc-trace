#pragma once
#include "graph.hpp"
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <iostream>

namespace btc_trace {

// Parse a CSV line handling quoted fields
inline std::vector<std::string> parse_csv_line(const std::string& line) {
    std::vector<std::string> fields;
    std::string field;
    bool in_quotes = false;

    for (size_t i = 0; i < line.size(); i++) {
        char c = line[i];
        if (c == '"') {
            in_quotes = !in_quotes;
        } else if (c == ',' && !in_quotes) {
            fields.push_back(field);
            field.clear();
        } else {
            field += c;
        }
    }
    fields.push_back(field);
    return fields;
}

// Load transaction CSV and build graph
// Expected CSV columns: txid, src_ip, dst_ip, input_addresses, output_addresses, geo_country, asn
inline CSRGraph load_transaction_csv(const std::string& filepath) {
    GraphBuilder builder;

    std::ifstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file: " + filepath);
    }

    std::string line;
    // Read header
    if (!std::getline(file, line)) {
        throw std::runtime_error("Empty file: " + filepath);
    }

    auto headers = parse_csv_line(line);
    // Find column indices
    int col_txid = -1, col_src_ip = -1, col_dst_ip = -1;
    int col_input_addr = -1, col_output_addr = -1;
    int col_country = -1, col_asn = -1;

    for (int i = 0; i < static_cast<int>(headers.size()); i++) {
        const auto& h = headers[i];
        if (h == "txid") col_txid = i;
        else if (h == "src_ip") col_src_ip = i;
        else if (h == "dst_ip") col_dst_ip = i;
        else if (h == "input_addresses") col_input_addr = i;
        else if (h == "output_addresses") col_output_addr = i;
        else if (h == "geo_country") col_country = i;
        else if (h == "asn") col_asn = i;
    }

    if (col_txid < 0) {
        throw std::runtime_error("Missing required column: txid");
    }

    uint32_t row = 0;
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        auto fields = parse_csv_line(line);
        row++;

        // Extract values (handle missing columns gracefully)
        auto get_field = [&](int col) -> std::string {
            if (col < 0 || col >= static_cast<int>(fields.size())) return "";
            return fields[col];
        };

        std::string txid = get_field(col_txid);
        std::string src_ip = get_field(col_src_ip);
        std::string dst_ip = get_field(col_dst_ip);
        std::string input_addrs = get_field(col_input_addr);
        std::string output_addrs = get_field(col_output_addr);
        std::string country = get_field(col_country);
        std::string asn = get_field(col_asn);

        if (txid.empty()) continue;

        // Create transaction node
        uint32_t tx_node = builder.add_node(NodeType::Transaction, txid);

        // Create IP nodes and edges
        if (!src_ip.empty()) {
            uint32_t ip_node = builder.find_or_add(NodeType::IP, src_ip);
            builder.add_edge(ip_node, tx_node, EdgeType::OBSERVED_WITH);

            // IP -> Country
            if (!country.empty()) {
                uint32_t country_node = builder.find_or_add(NodeType::Country, country);
                builder.add_edge(ip_node, country_node, EdgeType::LOCATED_IN);
            }

            // IP -> ASN
            if (!asn.empty()) {
                uint32_t asn_node = builder.find_or_add(NodeType::ASN, asn);
                builder.add_edge(ip_node, asn_node, EdgeType::BELONGS_TO);
            }
        }

        // Parse semicolon-separated wallet addresses
        auto split_addrs = [](const std::string& s) -> std::vector<std::string> {
            std::vector<std::string> result;
            std::stringstream ss(s);
            std::string addr;
            while (std::getline(ss, addr, ';')) {
                if (!addr.empty()) result.push_back(addr);
            }
            return result;
        };

        // Input wallets -> Transaction
        for (const auto& addr : split_addrs(input_addrs)) {
            uint32_t wallet_node = builder.find_or_add(NodeType::Wallet, addr);
            builder.add_edge(tx_node, wallet_node, EdgeType::INPUT_FROM);
        }

        // Transaction -> Output wallets
        for (const auto& addr : split_addrs(output_addrs)) {
            uint32_t wallet_node = builder.find_or_add(NodeType::Wallet, addr);
            builder.add_edge(tx_node, wallet_node, EdgeType::OUTPUT_TO);
        }
    }

    std::cerr << "[io] Loaded " << row << " rows, built graph: "
              << builder.num_nodes() << " nodes, "
              << builder.num_edges() << " edges" << std::endl;

    return builder.build();
}

// Export graph features to CSV
template<typename Features>
inline void export_features_csv(const std::string& filepath,
                                const CSRGraph& graph,
                                const std::vector<Features>& features) {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open output file: " + filepath);
    }

    file << "node_id,node_type,label,in_degree,out_degree,total_degree,"
         << "fan_in,fan_out,clustering_coeff,component_size,component_id,"
         << "in_degree_norm,out_degree_norm,degree_ratio\n";

    for (const auto& f : features) {
        file << f.node_id << ","
             << node_type_str(f.node_type) << ","
             << graph.node(f.node_id).label << ","
             << f.in_degree << ","
             << f.out_degree << ","
             << f.total_degree << ","
             << f.fan_in << ","
             << f.fan_out << ","
             << f.clustering_coeff << ","
             << f.component_size << ","
             << f.component_id << ","
             << f.in_degree_norm << ","
             << f.out_degree_norm << ","
             << f.degree_ratio << "\n";
    }

    std::cerr << "[io] Exported " << features.size() << " feature rows to " << filepath << std::endl;
}

// Export graph to edge list CSV
inline void export_edgelist_csv(const std::string& filepath, const CSRGraph& graph) {
    std::ofstream file(filepath);
    file << "src_id,src_label,src_type,dst_id,dst_label,dst_type,edge_type\n";

    for (uint32_t i = 0; i < graph.num_nodes(); i++) {
        auto neighbors = graph.out_neighbors(i);
        for (uint32_t j = 0; j < neighbors.size(); j++) {
            uint32_t dst = neighbors.begin_ptr[j];
            file << i << ","
                 << graph.node(i).label << ","
                 << node_type_str(graph.node(i).type) << ","
                 << dst << ","
                 << graph.node(dst).label << ","
                 << node_type_str(graph.node(dst).type) << ","
                 << edge_type_str(neighbors.types_ptr[j]) << "\n";
        }
    }
}

} // namespace btc_trace
