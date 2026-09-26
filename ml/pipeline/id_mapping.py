import json
from pathlib import Path
from typing import Union, Dict, Any

class EntityMapper:
    def __init__(self):
        self.mappings: Dict[str, Dict[str, int]] = {
            "wallet_address": {},
            "ip_address": {},
            "txid": {},
            "asn": {},
            "country": {}
        }
        
    def get_or_create(self, entity_type: str, entity_value: str) -> int:
        if entity_type not in self.mappings:
            raise ValueError(f"Unknown entity type: {entity_type}")
            
        entity_map = self.mappings[entity_type]
        if entity_value not in entity_map:
            # Deterministic mapping strategy: simply assign next available integer
            # If sorted order is strictly required across distributed systems, more complex logic is needed.
            entity_map[entity_value] = len(entity_map)
            
        return entity_map[entity_value]

    def save(self, path: Union[str, Path]):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.mappings, f, indent=2)
            
    def load(self, path: Union[str, Path]):
        path = Path(path)
        if not path.exists():
            return
        with open(path, 'r') as f:
            self.mappings = json.load(f)

    def build_from_dataframe(self, df: Any) -> None:
        """Extract all entities from a DataFrame and assign IDs."""
        import pandas as pd
        # Wallets from input_addresses and output_addresses
        for col in ["input_addresses", "output_addresses"]:
            if col in df.columns:
                for val in df[col].dropna():
                    for addr in str(val).split(";"):
                        addr = addr.strip()
                        if addr:
                            self.get_or_create("wallet_address", addr)

        # IPs
        for col in ["src_ip", "dst_ip"]:
            if col in df.columns:
                for val in df[col].dropna().unique():
                    self.get_or_create("ip_address", str(val))

        # TXIDs
        if "txid" in df.columns:
            for val in df["txid"].dropna().unique():
                self.get_or_create("txid", str(val))

        # ASNs
        if "asn" in df.columns:
            for val in df["asn"].dropna().unique():
                self.get_or_create("asn", str(val))

        # Countries
        if "geo_country" in df.columns:
            for val in df["geo_country"].dropna().unique():
                self.get_or_create("country", str(val))

    def total_entities(self) -> int:
        """Return total count of all mapped entities."""
        return sum(len(m) for m in self.mappings.values())

