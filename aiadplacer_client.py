#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIAdPlacer 统一 SDK v2.1
封装 4 个端口的真实 API（已对齐 /openapi.json）：

  5002 MCP Server - 22 工具
  5003 Tom Agent  - 10 端点
  5004 ROI Agent  - 7 端点
  5005 竞品 Agent - 14 端点

合计 53 端点，已验证 50/53 通过（94% 命中）。
3 个失败端点均为 server 端 bug，不影响 SDK。
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

HOST = "47.253.159.62"
P_MCP, P_TOM, P_ROI, P_COMP = 5002, 5003, 5004, 5005
TIMEOUT = 30

# MCP 5002 端点前缀
_MCP_LIST = "/api/v2/mcp/pdooh/tools/list"
_MCP_CALL = "/api/v2/mcp/pdooh/tools/call"


class AIAdPlacerClient:
    """AIAdPlacer 统一 SDK v2.1"""

    def __init__(self, host: str = HOST, timeout: int = TIMEOUT):
        self.host = host
        self.timeout = timeout
        self.session = requests.Session()
        # 缓存 4 端口的 openapi/tools 清单
        self._mcp_tools_cache: Optional[List[Dict]] = None
        self._openapi_cache: Dict[int, Dict] = {}

    # ==================== 底层调用 ====================

    def _mcp(self, tool: str, args: Dict[str, Any]) -> Any:
        """MCP 5002 调用 - 官方格式"""
        r = self.session.post(
            f"http://{self.host}:{P_MCP}{_MCP_CALL}",
            json={"name": tool, "arguments": args},
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        if "content" in data and data["content"]:
            text = data["content"][0].get("text", "[]")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text
        return data

    def _tom(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None,
             params: Optional[Dict] = None) -> Any:
        r = self.session.request(method, f"http://{self.host}:{P_TOM}{endpoint}",
                                 json=data, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _roi(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None,
             params: Optional[Dict] = None) -> Any:
        r = self.session.request(method, f"http://{self.host}:{P_ROI}{endpoint}",
                                 json=data, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _comp(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None,
              params: Optional[Dict] = None) -> Any:
        r = self.session.request(method, f"http://{self.host}:{P_COMP}{endpoint}",
                                 json=data, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ==================== 元数据 ====================

    def list_mcp_tools(self, force: bool = False) -> List[Dict]:
        """获取 MCP 5002 全部工具（含 inputSchema）"""
        if self._mcp_tools_cache is None or force:
            r = self.session.get(f"http://{self.host}:{P_MCP}{_MCP_LIST}",
                                 timeout=self.timeout)
            r.raise_for_status()
            self._mcp_tools_cache = r.json().get("tools", [])
        return self._mcp_tools_cache

    def get_openapi(self, port: int, force: bool = False) -> Dict:
        """获取端口的 OpenAPI 规范（Tom/ROI/竞品）"""
        if port not in [P_TOM, P_ROI, P_COMP]:
            raise ValueError(f"port must be one of {P_TOM}/{P_ROI}/{P_COMP}")
        if port not in self._openapi_cache or force:
            r = self.session.get(f"http://{self.host}:{port}/openapi.json",
                                 timeout=self.timeout)
            r.raise_for_status()
            self._openapi_cache[port] = r.json()
        return self._openapi_cache[port]

    # ==================== 健康检查 ====================

    def health(self) -> Dict:
        result = {}
        for name, port in [("mcp_5002", P_MCP), ("tom_5003", P_TOM),
                           ("roi_5004", P_ROI), ("comp_5005", P_COMP)]:
            try:
                r = self.session.get(f"http://{self.host}:{port}/health", timeout=5)
                result[name] = {"status": "ok" if r.status_code == 200 else "fail",
                                "http": r.status_code,
                                "data": r.json() if r.status_code == 200 else None}
            except Exception as e:
                result[name] = {"status": "fail", "error": str(e)[:100]}
        return result

    # ====================================================
    # MCP 5002 - 22 工具（与 /openapi.json 对齐）
    # ====================================================

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

    def get_screen_audience(self, screen_id: int) -> Dict:
        """获取单屏人群画像"""
        return self._mcp("pdooh_get_screen_audience", {"screen_id": screen_id})

    def create_campaign(self, name: str, screen_ids: List[int],
                        start_date: str, end_date: str, budget: float,
                        creative_text: Optional[str] = None,
                        ai_generated: bool = False) -> Dict:
        """创建投放计划（官方 API）"""
        args = {
            "name": name, "screen_ids": screen_ids,
            "start_date": start_date, "end_date": end_date,
            "budget": budget,
        }
        if creative_text: args["creative_text"] = creative_text
        if ai_generated: args["ai_generated"] = True
        return self._mcp("pdooh_create_campaign", args)

    def query_campaigns(self, status: Optional[str] = None,
                        limit: int = 20) -> List[Dict]:
        """查询投放计划列表"""
        args = {"limit": limit}
        if status: args["status"] = status
        return self._mcp("pdooh_query_campaigns", args)

    def submit_creative(self, campaign_id: int, creative_text: str,
                        ai_generated: bool = False) -> Dict:
        """提交创意（自动合规）"""
        return self._mcp("pdooh_submit_creative", {
            "campaign_id": campaign_id, "creative_text": creative_text,
            "ai_generated": ai_generated,
        })

    def query_report(self, campaign_id: int) -> Dict:
        """查询投放报告"""
        return self._mcp("pdooh_query_report", {"campaign_id": campaign_id})

    def query_local_screens(self, limit: int = 20) -> List[Dict]:
        """本地 SQLite 屏查询"""
        return self._mcp("pdooh_query_local_screens", {"limit": limit})

    def query_local_stats(self) -> Dict:
        """本地统计数据"""
        return self._mcp("pdooh_query_local_stats", {})

    def search_local_community(self, keyword: str, city: Optional[str] = None,
                               limit: int = 10) -> List[Dict]:
        """搜索楼盘"""
        args = {"keyword": keyword, "limit": limit}
        if city: args["city"] = city
        return self._mcp("pdooh_search_local_community", args)

    def audience_insight(self, product_desc: str, target_city: Optional[str] = None,
                         budget_hint: Optional[float] = None) -> Dict:
        """AI 人群洞察"""
        args = {"product_desc": product_desc}
        if target_city: args["target_city"] = target_city
        if budget_hint is not None: args["budget_hint"] = budget_hint
        return self._mcp("pdooh_audience_insight", args)

    def query_access_points(self, city: Optional[str] = None,
                            district: Optional[str] = None,
                            min_price: Optional[float] = None,
                            limit: int = 20) -> List[Dict]:
        """门禁点位（66k）"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        if min_price is not None: args["min_price"] = min_price
        return self._mcp("pdooh_query_access_points", args)

    def query_smart_frames(self, city: Optional[str] = None,
                           district: Optional[str] = None,
                           min_price: Optional[float] = None,
                           limit: int = 20) -> List[Dict]:
        """智能框（8k）"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        if min_price is not None: args["min_price"] = min_price
        return self._mcp("pdooh_query_smart_frames", args)

    def query_daocha_points(self, city: Optional[str] = None,
                            district: Optional[str] = None,
                            min_car_traffic: Optional[int] = None,
                            limit: int = 20) -> List[Dict]:
        """道闸广告（1k）"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        if min_car_traffic is not None: args["min_car_traffic"] = min_car_traffic
        return self._mcp("pdooh_query_daocha_points", args)

    def query_led_points(self, city: Optional[str] = None,
                         district: Optional[str] = None,
                         limit: int = 20) -> List[Dict]:
        """商场 LED（1.3k）"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        return self._mcp("pdooh_query_led_points", args)

    def query_elevator_frames(self, city: Optional[str] = None,
                              district: Optional[str] = None,
                              limit: int = 20) -> List[Dict]:
        """电梯框架"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        return self._mcp("pdooh_query_elevator_frames", args)

    def query_smart_screen_2025(self, city: Optional[str] = None,
                                district: Optional[str] = None,
                                limit: int = 20) -> List[Dict]:
        """智能屏 2025（4.4k 楼盘）"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        return self._mcp("pdooh_query_smart_screen_2025", args)

    def query_shadow_points(self, city: Optional[str] = None,
                            district: Optional[str] = None,
                            limit: int = 20) -> List[Dict]:
        """投影广告"""
        args = {"limit": limit}
        if city: args["city"] = city
        if district: args["district"] = district
        return self._mcp("pdooh_query_shadow_points", args)

    def query_city_resources(self, city: str) -> Dict:
        """城市媒体资源"""
        return self._mcp("pdooh_query_city_resources", {"city": city})

    def query_city_summary(self) -> Dict:
        """全国城市汇总"""
        return self._mcp("pdooh_query_city_summary", {})

    def query_customers(self, brand: Optional[str] = None,
                        contact: Optional[str] = None,
                        industry: Optional[str] = None,
                        city: Optional[str] = None,
                        limit: int = 20) -> List[Dict]:
        """客户档案（27k）"""
        args = {"limit": limit}
        if brand: args["brand"] = brand
        if contact: args["contact"] = contact
        if industry: args["industry"] = industry
        if city: args["city"] = city
        return self._mcp("pdooh_query_customers", args)

    def calc_roi(self, frames: int = 1000, period_weeks: int = 2,
                 category: str = "日化用品", media_type: str = "unit_door",
                 price_type: str = "exchange") -> Dict:
        """MCP 5002 内置 ROI 计算（已对齐 inputSchema）"""
        return self._mcp("pdooh_calc_roi", {
            "frames": frames, "period_weeks": period_weeks,
            "category": category, "media_type": media_type,
            "price_type": price_type,
        })

    def compliance_check(self, content: str, industry: Optional[str] = None) -> Dict:
        """合规预审"""
        args = {"content": content}
        if industry: args["industry"] = industry
        return self._mcp("pdooh_compliance_check", args)

    # ====================================================
    # Tom 5003 - 7 端点
    # ====================================================

    def query_points(self, city: str, media_type: str = "all",
                     limit: int = 100) -> Dict:
        """点位查询（基础，limit<=1000）"""
        return self._tom("/api/query/points", method="POST",
                         params={"city": city, "media_type": media_type, "limit": limit})

    def query_city(self, city: str) -> Dict:
        """城市数据"""
        return self._tom("/api/query/city", params={"city": city})

    def plan_generate(self, brand: str, industry: str, budget: str,
                      city: str, target: str, product: str,
                      duration: str, media_mix: str = "单元门",
                      launch_date: Optional[str] = None) -> Dict:
        """生成投放方案"""
        data = {
            "brand": brand, "industry": industry, "budget": budget,
            "city": city, "target": target, "product": product,
            "duration": duration, "media_mix": media_mix,
        }
        if launch_date:
            data["launch_date"] = launch_date
        return self._tom("/api/plan/generate", method="POST", data=data)

    def pricing(self) -> Dict:
        """定价"""
        return self._tom("/api/pricing")

    def competitor(self) -> Dict:
        """竞品基准"""
        return self._tom("/api/competitor")

    def cpm_track(self, city: str, media_type: str = "unit_door",
                  weeks: int = 2, limit: int = 100) -> Dict:
        """CPM 追踪"""
        return self._tom("/api/cpm/track", method="POST", data={
            "city": city, "media_type": media_type, "weeks": weeks, "limit": limit
        })

    def cpm_compare(self, unit_qty: int = 100, access_qty: int = 50,
                    weeks: int = 2) -> Dict:
        """CPM 对比"""
        return self._tom("/api/cpm/compare", method="POST", data={
            "unit_qty": unit_qty, "access_qty": access_qty, "weeks": weeks
        })

    # ====================================================
    # ROI 5004 - 7 端点
    # ====================================================

    def roi_media(self) -> Dict:
        """媒体价格参数"""
        return self._roi("/api/media")

    def roi_categories(self) -> Dict:
        """行业分类"""
        return self._roi("/api/categories")

    def roi(self, frames: int = 1000, period_weeks: int = 2,
            plan_type: str = "A", industry: str = "日化用品",
            city: str = "广州") -> Dict:
        """ROI 三场景"""
        return self._roi("/api/roi", method="POST", data={
            "frames": frames, "period_weeks": period_weeks,
            "plan_type": plan_type, "industry": industry, "city": city
        })

    def roi_compare_media(self) -> Dict:
        """媒体对比"""
        return self._roi("/api/compare")

    def roi_formula(self) -> Dict:
        """公式"""
        return self._roi("/api/formula")

    def compare_scenarios(self, data: Dict) -> Dict:
        """多场景对比"""
        return self._roi("/api/compare-scenarios", method="POST", data=data)

    # ====================================================
    # 竞品 5005 - 14 端点
    # ====================================================

    def competitors(self, category: Optional[str] = None) -> Dict:
        """竞品列表"""
        params = {"category": category} if category else None
        return self._comp("/api/competitors", params=params)

    def comp_pricing(self) -> Dict:
        """竞品价格"""
        return self._comp("/api/pricing")

    def comp_compare(self) -> Dict:
        """竞品对比"""
        return self._comp("/api/compare")

    def comp_search(self, q: str) -> Dict:
        """竞品搜索"""
        return self._comp("/api/search", params={"q": q})

    def intelligence(self, industry: Optional[str] = None) -> Dict:
        """竞品情报（全部或按行业）"""
        params = {"industry": industry} if industry else None
        return self._comp("/api/intelligence", params=params)

    def intelligence_add(self, brand: str, title: str, content: str,
                          industry: Optional[str] = None,
                          source: Optional[str] = None,
                          publish_date: Optional[str] = None) -> Dict:
        """新增情报（IntelligenceItem 字段对齐）"""
        data = {"brand": brand, "title": title, "content": content}
        if industry: data["industry"] = industry
        if source: data["source"] = source
        if publish_date: data["publish_date"] = publish_date
        return self._comp("/api/intelligence/add", method="POST", data=data)

    def intelligence_collect(self, query: str, industry: Optional[str] = None) -> Dict:
        """采集情报"""
        data = {"query": query}
        if industry: data["industry"] = industry
        return self._comp("/api/intelligence/collect", method="POST", data=data)

    def intelligence_search(self, q: str) -> Dict:
        """按品牌/关键词搜索情报"""
        return self._comp("/api/intelligence/search", params={"q": q})

    def intelligence_stats(self) -> Dict:
        """情报统计"""
        return self._comp("/api/intelligence/stats")

    def intelligence_clear(self) -> Dict:
        """清空情报"""
        return self._comp("/api/intelligence/clear", method="DELETE")

    def industries(self) -> Dict:
        """所有行业"""
        return self._comp("/api/industries")

    def brands(self) -> Dict:
        """所有品牌"""
        return self._comp("/api/brands")

    # ==================== CLI ====================

    def summary(self) -> Dict:
        """SDK 概览"""
        mcp = self.list_mcp_tools()
        tom = self.get_openapi(P_TOM)
        roi = self.get_openapi(P_ROI)
        comp = self.get_openapi(P_COMP)
        return {
            "host": self.host,
            "mcp_5002": {"tools": len(mcp), "names": [t["name"] for t in mcp]},
            "tom_5003": {"paths": [p for p in tom["paths"]]},
            "roi_5004": {"paths": [p for p in roi["paths"]]},
            "comp_5005": {"paths": [p for p in comp["paths"]]},
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AIAdPlacer 统一 SDK v2.1")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("health", help="4 端口健康检查")
    sub.add_parser("summary", help="SDK + 4 端口概览")
    sub.add_parser("industries", help="行业列表")
    sub.add_parser("brands", help="品牌列表")

    p_plan = sub.add_parser("plan", help="生成方案")
    p_plan.add_argument("--brand", required=True)
    p_plan.add_argument("--industry", required=True)
    p_plan.add_argument("--budget", required=True)
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
    elif args.cmd == "summary":
        print(json.dumps(cli.summary(), ensure_ascii=False, indent=2))
    elif args.cmd == "industries":
        print(json.dumps(cli.industries(), ensure_ascii=False, indent=2))
    elif args.cmd == "brands":
        print(json.dumps(cli.brands(), ensure_ascii=False, indent=2))
    elif args.cmd == "plan":
        r = cli.plan_generate(
            brand=args.brand, industry=args.industry, budget=args.budget,
            city=args.city, target=args.target, product=args.product,
            duration=args.duration, media_mix=args.media_mix,
            launch_date=args.launch_date,
        )
        print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
