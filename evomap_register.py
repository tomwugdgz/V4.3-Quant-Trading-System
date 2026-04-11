import requests
import json
from datetime import datetime
import hashlib
import random

# EvoMap Hub URL
HUB_URL = "https://evomap.ai"

def generate_message_id():
    """Generate unique message ID"""
    timestamp = int(datetime.now().timestamp() * 1000)
    random_hex = hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
    return f"msg_{timestamp}_{random_hex}"

def register_node():
    """Step 1: Register node with EvoMap Hub"""
    
    # Prepare hello request
    payload = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "hello",
        "message_id": generate_message_id(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "capabilities": {
                "trading": ["forex", "crypto", "mt5"],
                "analysis": ["technical", "fundamental", "quantitative"],
                "risk_management": True,
                "market_scanning": True
            },
            "model": "qwen3.5-plus",
            "env_fingerprint": {
                "platform": "windows",
                "arch": "x64",
                "node_type": "trading_agent"
            }
        }
    }
    
    print("=" * 70)
    print("EvoMap Node Registration")
    print("=" * 70)
    print(f"\nSending hello request to {HUB_URL}/a2a/hello")
    print(f"Message ID: {payload['message_id']}")
    print(f"Timestamp: {payload['timestamp']}")
    
    try:
        # Send POST request
        response = requests.post(
            f"{HUB_URL}/a2a/hello",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if "payload" in result:
                data = result["payload"]
                
                print("\n" + "=" * 70)
                print("[OK] REGISTRATION SUCCESSFUL!")
                print("=" * 70)
                
                # Extract important info
                node_id = data.get("your_node_id", "N/A")
                node_secret = data.get("node_secret", "N/A")
                claim_code = data.get("claim_code", "N/A")
                claim_url = data.get("claim_url", "N/A")
                hub_node_id = data.get("hub_node_id", "N/A")
                credit_balance = data.get("credit_balance", 0)
                heartbeat_interval = data.get("heartbeat_interval_ms", 900000)
                
                print(f"\n📋 Your Node Information:")
                print(f"  Node ID: {node_id}")
                print(f"  Node Secret: {node_secret[:20]}...{node_secret[-20:]}")
                print(f"  Claim Code: {claim_code}")
                print(f"  Claim URL: {claim_url}")
                print(f"  Credit Balance: {credit_balance}")
                print(f"  Heartbeat Interval: {heartbeat_interval/1000:.0f} seconds")
                
                print(f"\n⚠️  IMPORTANT - Save these immediately:")
                print(f"  1. Node ID: {node_id}")
                print(f"  2. Node Secret: {node_secret}")
                print(f"  3. Claim URL: {claim_url}")
                
                print(f"\n🎁 Next Steps:")
                print(f"  1. Visit {claim_url} to bind your EvoMap account")
                print(f"  2. You'll receive 200 starter credits after binding")
                print(f"  3. Start heartbeat to stay online")
                
                # Save to file
                node_info = {
                    "node_id": node_id,
                    "node_secret": node_secret,
                    "claim_code": claim_code,
                    "claim_url": claim_url,
                    "hub_node_id": hub_node_id,
                    "credit_balance": credit_balance,
                    "registered_at": datetime.now().isoformat(),
                    "heartbeat_interval_ms": heartbeat_interval
                }
                
                # Save to JSON file
                with open("trading/evomap-node-info.json", "w", encoding="utf-8") as f:
                    json.dump(node_info, f, indent=2, ensure_ascii=False)
                
                print(f"\n💾 Node info saved to: trading/evomap-node-info.json")
                
                return node_info
            else:
                print(f"\n[ERROR] Unexpected response format")
                print(f"Response: {json.dumps(result, indent=2)}")
                return None
        else:
            print(f"\n[ERROR] Registration failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Network error: {e}")
        return None
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return None

if __name__ == "__main__":
    node_info = register_node()
    
    if node_info:
        print("\n" + "=" * 70)
        print("[SUCCESS] Registration Complete!")
        print("=" * 70)
        print(f"\nPlease visit this URL to claim your account:")
        print(f"URL: {node_info['claim_url']}")
        print(f"\nAfter claiming, you'll receive 200 starter credits!")
    else:
        print("\n" + "=" * 70)
        print("[FAILED] Registration Failed")
        print("=" * 70)
