#!/usr/bin/env python3
"""
Hermes 消息队列 - 文件-based 通信方案
旺财 ↔ Hermes 通过 D:\LLM-Wiki\trading\hermes-messages/ 目录交换消息

不需要 RENTAHUMAN_API_KEY，完全依赖 bridge server
"""
import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path

# 配置
WIKI_BASE = Path(r"D:\LLM-Wiki\trading\hermes-messages")
INBOX = WIKI_BASE / "inbox"
OUTBOX = WIKI_BASE / "outbox"
ARCHIVE = WIKI_BASE / "archive"

# 确保目录存在
for d in [INBOX, OUTBOX, ARCHIVE]:
    d.mkdir(parents=True, exist_ok=True)

BRIDGE_URL = "http://172.23.137.223:8642"

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def gen_id():
    return hashlib.md5(f"{time.time()}{os.getpid()}".encode()).hexdigest()[:8]

# ============================================================
# 发送消息到 Hermes (写文件到 outbox)
# ============================================================
def send_to_hermes(content: str, msg_type: str = "query", meta: dict = None) -> dict:
    """
    发送消息到 Hermes
    - 写文件到 outbox/
    - 文件名格式: {timestamp}_{id}_{type}.md
    - 内容包含 header 元数据 + 正文
    """
    ts = get_timestamp()
    mid = gen_id()
    
    header = {
        "id": mid,
        "timestamp": ts,
        "type": msg_type,
        "sender": "wangcai",
        "status": "pending"
    }
    if meta:
        header["meta"] = meta
    
    file_content = f"""---
{json.dumps(header, ensure_ascii=False, indent=2)}
---

{content}
"""
    
    filename = f"{ts}_{mid}_{msg_type}.md"
    filepath = OUTBOX / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(file_content)
    
    # 通过 bridge API 同步到 wiki（如果需要）
    _sync_via_bridge(str(filepath), content)
    
    return {
        "success": True,
        "id": mid,
        "filename": filename,
        "timestamp": ts,
        "path": str(filepath)
    }

def _sync_via_bridge(filepath, content):
    """通过 bridge API 写入 wiki"""
    try:
        import urllib.request
        
        wiki_path = filepath.replace("D:/LLM-Wiki/", "").replace("\\", "/")
        
        data = json.dumps({
            "path": wiki_path,
            "content": content
        }).encode()
        
        req = urllib.request.Request(
            f"{BRIDGE_URL}/wiki/write",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result.get("success", False)
    except Exception as e:
        print(f"Bridge sync warning: {e}")
        return False

# ============================================================
# 读取 Hermes 回复 (从 inbox 轮询)
# ============================================================
def check_inbox(sender="hermes", msg_type=None, since_timestamp=None) -> list:
    """
    检查 inbox 中的新消息
    - 读取 {sender}_*.md 文件
    - 按 timestamp 排序
    - 可选过滤 msg_type / since_timestamp
    """
    messages = []
    
    for f in INBOX.glob("*.md"):
        if f.is_file() and f.stat().st_size > 0:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    content = fp.read()
                
                # 解析 header
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        header_text = parts[1].strip()
                        body = parts[2].strip()
                        
                        try:
                            header = json.loads(header_text)
                        except:
                            continue
                        
                        # 过滤条件
                        if header.get("sender") != sender:
                            continue
                        if msg_type and header.get("type") != msg_type:
                            continue
                        
                        messages.append({
                            "id": header.get("id"),
                            "timestamp": header.get("timestamp"),
                            "type": header.get("type"),
                            "sender": header.get("sender"),
                            "body": body,
                            "meta": header.get("meta", {}),
                            "filename": f.name,
                            "filepath": str(f)
                        })
            except Exception as e:
                print(f"Error reading {f}: {e}")
                continue
    
    # 按 timestamp 排序
    messages.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    
    # 时间过滤
    if since_timestamp:
        messages = [m for m in messages if (m["timestamp"] or "") > since_timestamp]
    
    return messages

# ============================================================
# 归档已处理消息
# ============================================================
def archive_message(filepath: str):
    """将已处理的消息移动到 archive/"""
    try:
        f = Path(filepath)
        if f.exists():
            archive_path = ARCHIVE / f.name
            i = 1
            while archive_path.exists():
                archive_path = ARCHIVE / f"{f.stem}_{i}{f.suffix}"
                i += 1
            f.rename(archive_path)
            return True
    except Exception as e:
        print(f"Archive error: {e}")
    return False

def mark_processed(filepath: str, response_content: str = None):
    """标记消息为已处理，附上回复内容"""
    try:
        f = Path(filepath)
        if not f.exists():
            return False
        
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
        
        # 更新 header
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                header_text = parts[1].strip()
                body = parts[2].strip()
                
                try:
                    header = json.loads(header_text)
                except:
                    return False
                
                header["status"] = "processed"
                header["processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if response_content:
                    header["response"] = response_content[:500]  # 截断响应
                
                new_content = f"""---
{json.dumps(header, ensure_ascii=False, indent=2)}
---

{body}
"""
                
                with open(f, "w", encoding="utf-8") as fp:
                    fp.write(new_content)
                
                return True
    except Exception as e:
        print(f"Mark error: {e}")
    return False

# ============================================================
# 轮询等待回复 (用于同步等待)
# ============================================================
def wait_for_response(sent_id: str, timeout: int = 120, poll_interval: int = 5) -> dict:
    """
    等待 Hermes 的回复
    - 超时时间: timeout 秒
    - 轮询间隔: poll_interval 秒
    - 返回: 收到回复的完整消息 或 None
    """
    start = time.time()
    
    while time.time() - start < timeout:
        messages = check_inbox(sender="hermes", msg_type="response")
        
        for msg in messages:
            # 找关联的原始消息
            if msg.get("meta", {}).get("in_reply_to") == sent_id:
                mark_processed(msg["filepath"])
                return msg
        
        # 检查是否有新的 response 消息
        for msg in messages:
            if msg["id"] == sent_id:
                mark_processed(msg["filepath"])
                return msg
        
        time.sleep(poll_interval)
    
    return None

# ============================================================
# 发送并等待 (简单封装)
# ============================================================
def send_and_wait(content: str, msg_type: str = "query", 
                   timeout: int = 120, poll_interval: int = 5) -> dict:
    """
    发送消息并同步等待回复
    - 用于需要即时响应的场景
    - 内部调用 send_to_hermes + wait_for_response
    """
    result = send_to_hermes(content, msg_type)
    sent_id = result["id"]
    
    response = wait_for_response(sent_id, timeout=timeout, poll_interval=poll_interval)
    
    return {
        "sent": result,
        "response": response
    }

# ============================================================
# 批量发送 (异步模式)
# ============================================================
def batch_send(messages: list) -> list:
    """批量发送消息，返回发送结果列表"""
    results = []
    for msg_content, msg_type in messages:
        result = send_to_hermes(msg_content, msg_type)
        results.append(result)
    return results

# ============================================================
# 健康检查
# ============================================================
def check_bridge_health() -> dict:
    """检查 bridge 服务状态"""
    try:
        import urllib.request
        req = urllib.request.Request(f"{BRIDGE_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_inbox_count() -> dict:
    """检查各目录消息数量"""
    return {
        "inbox": len(list(INBOX.glob("*.md"))),
        "outbox": len(list(OUTBOX.glob("*.md"))),
        "archive": len(list(ARCHIVE.glob("*.md")))
    }

# ============================================================
# 快速测试
# ============================================================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("=== Hermes Message Queue Test ===")
        
        # 检查 bridge
        health = check_bridge_health()
        print(f"Bridge: {health}")
        
        # 检查 inbox
        counts = check_inbox_count()
        print(f"Queue counts: {counts}")
        
        # 发送测试消息
        result = send_to_hermes(
            "系统测试消息 - 验证消息队列功能",
            msg_type="test",
            meta={"source": "hermes_queue.py", "version": "1.0"}
        )
        print(f"Send result: {result}")
        
        print("\n=== All Tests Passed ===")
    elif len(sys.argv) > 1 and sys.argv[1] == "poll":
        print("=== Polling Inbox ===")
        messages = check_inbox(sender="hermes")
        for m in messages[:5]:
            print(f"  [{m['timestamp']}] {m['type']}: {m['body'][:100]}...")
    else:
        print("Usage:")
        print("  python hermes_queue.py test   # 运行测试")
        print("  python hermes_queue.py poll  # 轮询 inbox")