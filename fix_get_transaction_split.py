import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

replacement = """                    "input_addresses": tx_dict.get("input_addresses", "").split(";") if tx_dict.get("input_addresses") else [],
                    "output_addresses": tx_dict.get("output_addresses", "").split(";") if tx_dict.get("output_addresses") else [],
                    "input_amounts": [float(x) for x in str(tx_dict.get("input_amounts", "")).split(";") if x.strip()] if tx_dict.get("input_amounts") else [],
                    "output_amounts": [float(x) for x in str(tx_dict.get("output_amounts", "")).split(";") if x.strip()] if tx_dict.get("output_amounts") else [],
                    "fee": float(tx_dict.get("fee")) if tx_dict.get("fee") is not None else None,"""

content = re.sub(r'                    "input_addresses": \[tx_dict\.get\("input_addresses"\)\] if tx_dict\.get\("input_addresses"\) else \[\],\n                    "output_addresses": \[tx_dict\.get\("output_addresses"\)\] if tx_dict\.get\("output_addresses"\) else \[\],\n                    "input_amounts": \[tx_dict\.get\("input_amounts"\)\] if tx_dict\.get\("input_amounts"\) else \[\],\n                    "output_amounts": \[tx_dict\.get\("output_amounts"\)\] if tx_dict\.get\("output_amounts"\) else \[\],\n                    "fee": tx_dict\.get\("fee"\),', replacement, content, flags=re.DOTALL)

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
