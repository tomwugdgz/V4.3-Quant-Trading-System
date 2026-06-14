#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pDOOH MCP 客户端封装
用法:
    python pdooh_client.py list                              # 列出所有工具
    python pdooh_client.py call <tool_name> --args '{...}'   # 调用工具
    python pdooh_client.py health                            # 健康检查
    
或者作为 Python 模块:
    from pdooh_client import PdoohClient
    client = PdoohClient()
    result = client.query_access_points("广州", limit=10)
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import requests

API_BASE = "http://47.253.159.62:5002/api/v2/mcp/pdooh"
TOOLS_CALL_URL = f"{API_BASE}/tools/call"
TOOLS_LIST_URL = f"{API_BASE}/tools/list"
HEALTH_URL = f"{API_BASE}/health"


class PdoohClient:
    """pDOOH MCP 客户端"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()

    def _call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具并自动解析嵌套 JSON"""
        payload = {"name": tool_name, "arguments": arguments}
        try:
            resp = self.session.post(
                TOOLS_CALL_URL, json=payload, timeout=self.timeout
            )
            resp.raise_for_status()
            result = resp.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"网络错误: {e}"}
        except json.JSONDecodeError as e:
            return {"error": f"返回非 JSON: {e}", "raw": resp.text[:500]}

        if "detail" in result:
            return {"error": result["detail"]}

        # 解析嵌套的 text JSON 字符串
        if "content" in result and len(result.get("content", [])) > 0:
            text = result["content"][0].get("text", "[]")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text
        return result

    def health(self) -> Dict:
        """健康检查"""
        try:
            resp = self.session.get(HEALTH_URL, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def list_tools(self) -> List[Dict]:
        """列出所有工具"""
        try:
            resp = self.session.get(TOOLS_LIST_URL, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("tools", [])
        except Exception as e:
            return [{"error": str(e)}]

    # ===== 核心投放工具 =====

    def query_screens(
        self,
        city: str,
        district: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius: int = 3000,
        tags: Optional[List[str]] = None,
        min_house_price: Optional[float] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """查询智能屏"""
        args = {
            "city": city,
            "radius": radius,
            "limit": limit,
        }
        if district:
            args["district"] = district
        if lat is not None:
            args["lat"] = lat
        if lng is not None:
            args["lng"] = lng
        if tags:
            args["tags"] = tags
        if min_house_price is not None:
            args["min_house_price"] = min_house_price
        return self._call("pdooh_query_screens", args)

    def get_screen_audience(self, screen_id: int) -> Dict:
        """获取指定屏的人群画像"""
        return self._call("pdooh_get_screen_audience", {"screen_id": screen_id})

    def create_campaign(
        self,
        name: str,
        screen_ids: List[int],
        start_date: str,
        end_date: str,
        budget: float,
        creative_text: Optional[str] = None,
        ai_generated: bool = False,
    ) -> Dict:
        """创建投放计划"""
        args = {
            "name": name,
            "screen_ids": screen_ids,
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget,
            "ai_generated": ai_generated,
        }
        if creative_text:
            args["creative_text"] = creative_text
        return self._call("pdooh_create_campaign", args)

    def query_campaigns(self, status: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """查询投放计划列表"""
        args = {"limit": limit}
        if status:
            args["status"] = status
        return self._call("pdooh_query_campaigns", args)

    def submit_creative(
        self,
        campaign_id: int,
        creative_type: str,
        creative_url: Optional[str] = None,
        ai_prompt: Optional[str] = None,
    ) -> Dict:
        """提交广告创意"""
        args = {
            "campaign_id": campaign_id,
            "creative_type": creative_type,
        }
        if creative_url:
            args["creative_url"] = creative_url
        if ai_prompt:
            args["ai_prompt"] = ai_prompt
        return self._call("pdooh_submit_creative", args)

    def query_report(
        self,
        campaign_id: Optional[int] = None,
        screen_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """查询投放报告"""
        args = {}
        if campaign_id is not None:
            args["campaign_id"] = campaign_id
        if screen_id is not None:
            args["screen_id"] = screen_id
        if start_date:
            args["start_date"] = start_date
        if end_date:
            args["end_date"] = end_date
        return self._call("pdooh_query_report", args)

    # ===== AI 能力工具 =====

    def compliance_check(self, content: str, industry: Optional[str] = None) -> Dict:
        """广告内容合规预审"""
        args = {"content": content}
        if industry:
            args["industry"] = industry
        return self._call("pdooh_compliance_check", args)

    def query_local_screens(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        media_type: Optional[str] = None,
        min_price: Optional[float] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """查询本地 SQLite 数据库的社区点位"""
        args = {"limit": limit}
        if city:
            args["city"] = city
        if district:
            args["district"] = district
        if media_type:
            args["media_type"] = media_type
        if min_price is not None:
            args["min_price"] = min_price
        return self._call("pdooh_query_local_screens", args)

    def query_local_stats(
        self,
        query_type: str = "city_stats",
        city: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Dict:
        """查询城市/区域统计"""
        args = {"query_type": query_type}
        if city:
            args["city"] = city
        if keyword:
            args["keyword"] = keyword
        return self._call("pdooh_query_local_stats", args)

    def search_local_community(
        self, keyword: str, city: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """搜索楼盘"""
        args = {"keyword": keyword, "limit": limit}
        if city:
            args["city"] = city
        return self._call("pdooh_search_local_community", args)

    def audience_insight(
        self,
        product_desc: str,
        target_city: Optional[str] = None,
        budget_hint: Optional[float] = None,
    ) -> Dict:
        """AI 人群洞察"""
        args = {"product_desc": product_desc}
        if target_city:
            args["target_city"] = target_city
        if budget_hint is not None:
            args["budget_hint"] = budget_hint
        return self._call("pdooh_audience_insight", args)

    # ===== 资源查询工具 =====

    def query_access_points(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        min_price: Optional[float] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """查询门禁点位（广告门）"""
        args = {"limit": limit}
        if city:
            args["city"] = city
        if district:
            args["district"] = district
        if min_price is not None:
            args["min_price"] = min_price
        return self._call("pdooh_query_access_points", args)

    def query_smart_frames(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        min_price: Optional[float] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """查询单元门智能框点位"""
        args = {"limit": limit}
        if city:
            args["city"] = city
        if district:
            args["district"] = district
        if min_price is not None:
            args["min_price"] = min_price
        return self._call("pdooh_query_smart_frames", args)

    def query_daocha_points(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        min_car_traffic: Optional[int] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """查询道闸广告点位"""
        args = {"limit": limit}
        if city:
            args["city"] = city
        if district:
            args["district"] = district
        if min_car_traffic is not None:
            args["min_car_traffic"] = min_car_traffic
        return self._call("pdooh_query_daocha_points", args)

    def query_led_points(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """查询商场 LED 点位"""
        args = {"limit": limit}
        if city:
            args["city"] = city
        if district:
            args["district"] = district
        return self._call("pdooh_query_led_points", args)

    def query_smart_screen_2025(
        self,
        city: Optional[str] = None,
        district: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """查询智能屏 2025 数据（按楼盘统计）"""
        args = {"limit": limit}
        if city:
            args["city"] = city
        if district:
            args["district"] = district
        return self._call("pdooh_query_smart_screen_2025", args)

    def query_city_resources(self, city: str) -> Dict:
        """查询城市媒体资源统计"""
        return self._call("pdooh_query_city_resources", {"city": city})

    def query_city_summary(self) -> Dict:
        """查询全国城市资源汇总"""
        return self._call("pdooh_query_city_summary", {})

    def query_customers(
        self,
        brand: Optional[str] = None,
        contact: Optional[str] = None,
        industry: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """查询客户资料"""
        args = {"limit": limit}
        if brand:
            args["brand"] = brand
        if contact:
            args["contact"] = contact
        if industry:
            args["industry"] = industry
        if city:
            args["city"] = city
        return self._call("pdooh_query_customers", args)


# ===== CLI 入口 =====


def main():
    parser = argparse.ArgumentParser(description="pDOOH MCP 客户端")
    subparsers = parser.add_subparsers(dest="command")

    # health
    subparsers.add_parser("health", help="健康检查")

    # list
    subparsers.add_parser("list", help="列出所有工具")

    # call
    call_parser = subparsers.add_parser("call", help="调用工具")
    call_parser.add_argument("tool", help="工具名称")
    call_parser.add_argument(
        "--args", "-a", default="{}", help="工具参数（JSON 字符串）"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = PdoohClient()

    if args.command == "health":
        result = client.health()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "list":
        tools = client.list_tools()
        print(f"共 {len(tools)} 个工具：\n")
        for t in tools:
            print(f"- {t.get('name')}: {t.get('description', '')[:60]}")
    elif args.command == "call":
        try:
            arguments = json.loads(args.args)
        except json.JSONDecodeError as e:
            print(f"参数 JSON 解析失败: {e}", file=sys.stderr)
            sys.exit(1)
        result = client._call(args.tool, arguments)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
