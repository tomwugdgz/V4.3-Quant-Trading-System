import requests
import json
from datetime import datetime
import hashlib
import random

HUB_URL = "https://evomap.ai"

def generate_message_id():
    timestamp = int(datetime.now().timestamp() * 1000)
    random_hex = hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
    return f"msg_{timestamp}_{random_hex}"

payload = {
    "protocol": "gep-a2a",
    "protocol_version": "1.0.0",
    "message_type": "hello",
    "message_id": generate_message_id(),
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "payload": {
        "capabilities": {
            "supported_types": ["Gene", "Capsule"],
            "trading": ["forex", "crypto"]
        },
        "model": "gpt-4o",
        "env_fingerprint": {
            "platform": "windows",
            "arch": "x64"
        }
    }
}

print("Sending request to EvoMap Hub...")
print(f"URL: {HUB_URL}/a2a/hello")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(f"{HUB_URL}/a2a/hello", json=payload, timeout=30)
    result = response.json()
    
    print(f"Status: {response.status_code}")
    print(f"\n[SUCCESS] Registration Complete!\n")
    
    if "payload" in result:
        data = result["payload"]
        node_id = data.get("your_node_id", "N/A")
        node_secret = data.get("node_secret", "N/A")
        claim_code = data.get("claim_code", "N/A")
        claim_url = data.get("claim_url", "N/A")
        credit_balance = data.get("credit_balance", 0)
        
        print("=" * 70)
        print("Your EvoMap Node Information:")
        print("=" * 70)
        print(f"Node ID: {node_id}")
        print(f"Node Secret: {node_secret}")
        print(f"Claim Code: {claim_code}")
        print(f"Claim URL: {claim_url}")
        print(f"Credit Balance: {credit_balance}")
        print("=" * 70)
        
        # Save to file
        with open("trading/evomap-node-info.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nNode info saved to: trading/evomap-node-info.json")
        print(f"\nNEXT STEP: Visit {claim_url} to bind your account and get 200 credits!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
