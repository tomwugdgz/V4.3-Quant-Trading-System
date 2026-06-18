#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIAdPlacer 统一 SDK
封装 4 个端口的 API：
  5002 MCP Server - pDOOH 投放平台（资源查询 + 投放执行）
  5003 Tom Agent  - 投放方案生成 + CPM 追踪
  5004 ROI Agent  - ROI 三场景计算 + 行业对比
  5005 竞品 Agent  - 竞品情报 + 行业分类
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests

# Force UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

HOST = "47.253.159.62"
P_MCP, P_TOM, P_ROI, P_COMP = 5002, 5003, 5004, 5005

TIMEOUT = 30


class AIAdPlacerClient:
    """AIAdPlacer 统一 SDK"""

    def __init__(self, host: str = HOST, timeout: int = TIMEOUT):
        self.host = host
        self.timeout = timeout
        self.session = requests.Session()

    # ===== 底层调用 =====

    def _mcp(self, tool: str, args: Dict[str, Any]) -> Any:
        """5002 MCP 调用 - 直接 POST name + arguments"""
        r = self.session.post(
            f"http://{self.host}:{P_MCP}/api/v2/mcp/pdooh/tools/call",
            json={"name": tool, "arguments": args},
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        # 解析嵌套 JSON 字符串
        if "content" in data and data["content"]:
            text = data["content"][0].get("text", "[]")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text
        return data

    def _tom(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """5003 Tom 调用"""
        url = f"http://{self.host}:{P_TOM}{endpoint}"
        r = self.session.request(method, url, json=data, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _roi(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """5004 ROI 调用"""
        url = f"http://{self.host}:{P_ROI}{endpoint}"
        r = self.session.request(method, url, json=data, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _comp(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """5005 竞品调用 - GET only"""
        url = f"http://{self.host}:{P_COMP}{endpoint}"
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ===== 健康检查 =====

    def health(self) -> Dict:
        """4 端口健康检查"""
        result = {}
        for name, port in [("mcp_5002", P_MCP), ("tom_5003", P_TOM),
                           ("roi_5004", P_ROI), ("comp_5005", P_COMP)]:
            try:
                r = self.session.get(f"http://{self.host}:{port}/health", timeout=3)
                result[name] = {"status": "ok", "data": r.json()}
            except Exception as e:
                result[name] = {"status": "fail", "error": str(e)}
        return result

    # ==========================================
    # 5002 MCP - 资源查询 + 投放执行
    # ==========================================

    def query_screens(self, city: str, district: Optional[str] = None,
                      lat: Optional[float] = None, lng: Optional[float] = None,
                      radius: int = 3000, tags: Optional[List[str]] = None,
                      min_house_price: Optional[float] = None,
                      limit: int = 20) -> List[Dict]:
        """查询智能屏"""
        args = {"city": city, "radius": radius, "limit": limit}
        if district: args["district"] = district
        if lat is not None: args["lat"] = lat
        if lng is not None: args["lng"] = lng
        if tags: args["tags"] = tags
        if min_house_price is not None: args["min_house_price"] = min_house_price
        return self._mcp("pdooh_query_screens", args)

    def audience_insight(self, product_desc: str, target_city: Optional[str] = None,
                         budget_hint: Optional[float] = None) -> Dict:
        """AI 人群洞察"""
        args = {"product_desc": product_desc}
        if target_city: args["target_city"] = target_city
        if budget_hint is not None: args["budget_hint"] = budget_hint
        return self._mcp("pdooh_audience_insight", args)

    def query_access_points(self, city: Optional[str] = None, district: Optional[str] = None,
                            min_price: Optional[float] = None, limit: int = 20) -> List[Dict]:
        """查询门禁点位"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        if min_price is not None: args["min_price"] = min_price
        return self._mcp("pdooh_query_access_points", args)

    def query_smart_frames(self, city: Optional[str] = None, district: Optional[str] = None,
                           min_price: Optional[float] = None, limit: int = 20) -> List[Dict]:
        """查询智能框点位"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        if min_price is not None: args["min_price"] = min_price
        return self._mcp("pdooh_query_smart_frames", args)

    def query_daocha_points(self, city: Optional[str] = None, district: Optional[str] = None,
                            min_car_traffic: Optional[int] = None, limit: int = 20) -> List[Dict]:
        """查询道闸广告点位"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        if min_car_traffic is not None: args["min_car_traffic"] = min_car_traffic
        return self._mcp("pdooh_query_daocha_points", args)

    def query_led_points(self, city: Optional[str] = None, district: Optional[str] = None,
                         limit: int = 20) -> List[Dict]:
        """查询商场 LED 点位"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        return self._mcp("pdooh_query_led_points", args)

    def query_smart_screen_2025(self, city: Optional[str] = None, district: Optional[str] = None,
                                limit: int = 20) -> List[Dict]:
        """查询智能屏 2025 数据"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        return self._mcp("pdooh_query_smart_screen_2025", args)

    def query_customers(self, brand: Optional[str] = None, contact: Optional[str] = None,
                        industry: Optional[str] = None, city: Optional[str] = None,
                        limit: int = 20) -> List[Dict]:
        """查询客户资料"""
        args = {"limit": limit}
        if brand: args["brand"] = brand
        if contact: args["contact"] = contact
        if industry: args["industry"] = industry
        if city: args["city"] = city
        return self._mcp("pdooh_query_customers", args)

    def compliance_check(self, content: str, industry: Optional[str] = None) -> Dict:
        """广告内容合规预审"""
        args = {"content": content}
        if industry: args["industry"] = industry
        return self._mcp("pdooh_compliance_check", args)

    def search_local_community(self, keyword: str, city: Optional[str] = None,
                               limit: int = 10) -> List[Dict]:
        """搜索楼盘"""
        args = {"keyword": keyword, "limit": limit}
        if city: args["city"] = city
        return self._mcp("pdooh_search_local_community", args)

    def query_city_resources(self, city: str) -> Dict:
        """查询城市媒体资源统计"""
        return self._mcp("pdooh_query_city_resources", {"city": city})

    def query_city_summary(self) -> Dict:
        """查询全国城市资源汇总"""
        return self._mcp("pdooh_query_city_summary", {})

    # ==========================================
    # 5003 Tom - 方案生成 + CPM
    # ==========================================

    def plan_generate(self, brand: str, industry: str, budget: str,
                      city: str, target: str, product: str,
                      duration: str, media_mix: str = "单元门",
                      launch_date: Optional[str] = None) -> Dict:
        """
        生成投放方案
        budget 必须是字符串，如 "30万"（不是 300000）
        """
        data = {
            "brand": brand, "industry": industry, "budget": budget,
            "city": city, "target": target, "product": product,
            "duration": duration, "media_mix": media_mix,
        }
        if launch_date:
            data["launch_date"] = launch_date
        return self._tom("/api/plan/generate", method="POST", data=data)

    def pricing(self) -> Dict:
        """获取所有媒体类型定价"""
        return self._tom("/api/pricing")

    def cpm_track(self, city: str, media_type: str = "unit_door",
                  weeks: int = 2, limit: int = 100) -> Dict:
        """CPM 追踪"""
        return self._tom("/api/cpm/track", method="POST", data={
            "city": city, "media_type": media_type, "weeks": weeks, "limit": limit
        })

    def cpm_compare(self, unit_qty: int = 100, access_qty: int = 50,
                    weeks: int = 2) -> Dict:
        """CPM 对比（单元门 vs 广告门）"""
        return self._tom("/api/cpm/compare", method="POST", data={
            "unit_qty": unit_qty, "access_qty": access_qty, "weeks": weeks
        })

    # ==========================================
    # 5004 ROI - 三场景 ROI
    # ==========================================

    def roi(self, frames: int = 1000, period_weeks: int = 2,
            plan_type: str = "A", industry: str = "日化用品",
            city: str = "广州") -> Dict:
        """ROI 三场景计算"""
        return self._roi("/api/roi", method="POST", data={
            "frames": frames, "period_weeks": period_weeks,
            "plan_type": plan_type, "industry": industry, "city": city
        })

    def roi_formula(self) -> Dict:
        """ROI 计算公式说明"""
        return self._roi("/api/formula")

    def roi_compare(self) -> Dict:
        """媒体 ROI 对比（社区门 vs 梯媒 vs 地铁）"""
        return self._roi("/api/compare")

    # ==========================================
    # 5005 竞品 - 情报 + 行业
    # ==========================================

    def competitors(self) -> Dict:
        """获取所有竞品（按品类）"""
        return self._comp("/api/competitors")

    def intelligence(self, industry: Optional[str] = None) -> Dict:
        """获取竞品情报（全部或按行业）"""
        params = {}
        if industry:
            params["industry"] = industry
        return self._comp("/api/intelligence", params=params)

    def intelligence_search(self, query: str) -> Dict:
        """按品牌/关键词搜索情报"""
        return self._comp("/api/intelligence/search", params={"q": query})

    def industries(self) -> Dict:
        """所有行业分类"""
        return self._comp("/api/industries")

    def brands(self) -> Dict:
        """所有品牌列表"""
        return self._comp("/api/brands")

    def intelligence_stats(self) -> Dict:
        """情报统计"""
        return self._comp("/api/intelligence/stats")


# ===== CLI 入口 =====

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AIAdPlacer 统一 SDK")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("health", help="4 端口健康检查")
    sub.add_parser("industries", help="列出所有行业")
    sub.add_parser("brands", help="列出所有品牌")

    p_plan = sub.add_parser("plan", help="生成投放方案")
    p_plan.add_argument("--brand", required=True)
    p_plan.add_argument("--industry", required=True)
    p_plan.add_argument("--budget", required=True, help="字符串，如 30万")
    p_plan.add_argument("--city", required=True)
    p_plan.add_argument("--target", required=True)
    p_plan.add_argument("--product", required=True)
    p_plan.add_argument("--duration", required=True)
    p_plan.add_argument("--media-mix", default="单元门")
    p_plan.add_argument("--launch-date", default=None)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    cli = AIAdPlacerClient()

    if args.cmd == "health":
        print(json.dumps(cli.health(), ensure_ascii=False, indent=2))
    elif args.cmd == "industries":
        print(json.dumps(cli.industries(), ensure_ascii=False, indent=2))
    elif args.cmd == "brands":
        print(json.dumps(cli.brands(), ensure_ascii=False, indent=2))
    elif args.cmd == "plan":
        result = cli.plan_generate(
            brand=args.brand, industry=args.industry, budget=args.budget,
            city=args.city, target=args.target, product=args.product,
            duration=args.duration, media_mix=args.media_mix,
            launch_date=args.launch_date,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
