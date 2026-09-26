import re

with open("backend/services/data_service.py", "r") as f:
    content = f.read()

content = content.replace('"input_amounts": [tx_dict.get("amount_input")] if tx_dict.get("amount_input") else [],', '"input_amounts": [tx_dict.get("input_amounts")] if tx_dict.get("input_amounts") else [],')
content = content.replace('"output_amounts": [tx_dict.get("amount_output")] if tx_dict.get("amount_output") else [],', '"output_amounts": [tx_dict.get("output_amounts")] if tx_dict.get("output_amounts") else [],')
content = content.replace('"fee": tx_dict.get("amount_fee"),', '"fee": tx_dict.get("fee"),')

with open("backend/services/data_service.py", "w") as f:
    f.write(content)
