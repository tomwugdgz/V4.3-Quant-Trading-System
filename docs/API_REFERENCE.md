# API 参考文档 (API Reference)

**版本**: V4.3.0  
**创建时间**: 2026-04-11  
**最后更新**: 2026-04-11

---

## 一、Market Regime Agent

### 1.1 类定义

```python
from v4_3.market_regime import MarketRegimeAgent

class MarketRegimeAgent:
    """市场状态判断 Agent"""
    
    def __init__(self, config_path: str = "config/regime_config.json")
    def detect_regime(self, symbol: str, timeframe: str) -> MarketRegime
    def should_trade(self, regime: MarketRegime) -> bool
    def get_dynamic_threshold(self, regime: MarketRegime) -> float
    def get_regime_report(self, symbol: str, timeframe: str) -> Dict
```

---

### 1.2 detect_regime

**功能**: 判断市场状态

**参数**:
- `symbol` (str): 交易品种，如 "EURUSD"
- `timeframe` (str): 时间周期，如 "H1", "H4", "D1"

**返回**:
```python
MarketRegime.TRENDING_UP      # 上涨趋势
MarketRegime.TRENDING_DOWN    # 下跌趋势
MarketRegime.RANGING          # 震荡市
MarketRegime.HIGH_VOLATILITY  # 高波动
```

**示例**:
```python
agent = MarketRegimeAgent()
regime = agent.detect_regime("EURUSD", "H1")
print(f"市场状态：{regime.value}")
```

---

### 1.3 should_trade

**功能**: 判断是否应该交易

**参数**:
- `regime` (MarketRegime): 市场状态

**返回**:
- `bool`: True=可以交易，False=不交易

**示例**:
```python
if agent.should_trade(regime):
    print("可以交易")
else:
    print("不交易")
```

---

### 1.4 get_dynamic_threshold

**功能**: 获取动态信号阈值

**参数**:
- `regime` (MarketRegime): 市场状态

**返回**:
- `float`: 信号阈值（百分比）

**示例**:
```python
threshold = agent.get_dynamic_threshold(regime)
print(f"信号阈值：{threshold:.2f}%")
```

---

## 二、Factor Score Engine

### 2.1 类定义

```python
from v4_3.factor_score import FactorScoreEngine

class FactorScoreEngine:
    """因子评分引擎"""
    
    def __init__(self, config_path: str = "config/factor_weights.json")
    def calculate_score(self, symbol: str, timeframe: str) -> Dict
    def get_factor_breakdown(self, symbol: str, timeframe: str) -> Dict
```

---

### 2.2 calculate_score

**功能**: 计算综合评分

**参数**:
- `symbol` (str): 交易品种
- `timeframe` (str): 时间周期

**返回**:
```python
{
    'score': float,        # 综合评分 (0-100)
    'signal': str,         # 交易信号
    'factors': {           # 各因子评分
        'momentum': float,
        'mean_reversion': float,
        'breakout': float,
        'volatility': float
    }
}
```

**示例**:
```python
engine = FactorScoreEngine()
result = engine.calculate_score("EURUSD", "H1")

print(f"综合评分：{result['score']:.1f}")
print(f"交易信号：{result['signal']}")
```

---

### 2.3 get_factor_breakdown

**功能**: 获取因子细分

**参数**:
- `symbol` (str): 交易品种
- `timeframe` (str): 时间周期

**返回**:
```python
{
    'momentum': {
        'ema_slope': float,
        'price_momentum': float,
        'macd': Dict
    },
    'mean_reversion': {
        'rsi': Dict,
        'bollinger': Dict,
        'bias': float
    },
    ...
}
```

---

## 三、Risk Agent

### 3.1 类定义

```python
from v4_3.risk_agent import RiskAgent

class RiskAgent:
    """风控 Agent"""
    
    def __init__(self, config_path: str = "config/risk_params.json", 
                 custom_params: Dict = None)
    def can_trade(self, symbol: str, signal: str, volume: float,
                  account_info: Dict, positions: List) -> Tuple[bool, str]
    def calculate_position_size(self, symbol: str, stop_loss: float,
                                 risk_percent: float = 0.005) -> float
    def generate_risk_report(self, positions: List, account_info: Dict) -> str
```

---

### 3.2 can_trade

**功能**: 风控检查

**参数**:
- `symbol` (str): 交易品种
- `signal` (str): 交易信号
- `volume` (float): 手数
- `account_info` (Dict): 账户信息
- `positions` (List): 当前持仓

**返回**:
```python
(can_trade: bool, reason: str)
```

**示例**:
```python
can_trade, reason = agent.can_trade(
    symbol="EURUSD",
    signal="BUY",
    volume=0.1,
    account_info=account,
    positions=positions
)

if can_trade:
    print("风控通过")
else:
    print(f"风控不通过：{reason}")
```

---

### 3.3 calculate_position_size

**功能**: 计算仓位大小

**参数**:
- `symbol` (str): 交易品种
- `stop_loss` (float): 止损价格
- `risk_percent` (float): 风险百分比（默认 0.5%）

**返回**:
- `float`: 手数

**示例**:
```python
lot_size = agent.calculate_position_size(
    symbol="EURUSD",
    stop_loss=1.0950,
    risk_percent=0.005
)

print(f"建议手数：{lot_size:.2f}")
```

---

## 四、Review Agent

### 4.1 类定义

```python
from v4_3.review_agent import ReviewAgent

class ReviewAgent:
    """复盘 Agent"""
    
    def __init__(self, db_path: str = "trading.db")
    def get_trade_history(self, days: int = 30) -> pd.DataFrame
    def attribution_analysis(self, days: int = 30) -> Dict
    def generate_daily_report(self, date: str = None) -> str
    def identify_patterns(self, days: int = 30) -> Dict
```

---

### 4.2 attribution_analysis

**功能**: 归因分析

**参数**:
- `days` (int): 回看天数

**返回**:
```python
{
    'period': str,
    'total_trades': int,
    'strategy_attribution': Dict,
    'symbol_attribution': Dict,
    'time_attribution': Dict,
    'factor_attribution': Dict
}
```

**示例**:
```python
attribution = agent.attribution_analysis(days=30)

print(f"策略归因：{attribution['strategy_attribution']}")
print(f"品种归因：{attribution['symbol_attribution']}")
```

---

### 4.3 generate_daily_report

**功能**: 生成每日复盘报告

**参数**:
- `date` (str): 日期（YYYY-MM-DD 格式）

**返回**:
- `str`: Markdown 格式报告

**示例**:
```python
report = agent.generate_daily_report(date="2026-04-11")
print(report)
```

---

## 五、Factor IC Analyzer

### 5.1 类定义

```python
from v4_3.factor_ic_analysis import FactorICAnalyzer

class FactorICAnalyzer:
    """因子 IC 分析器"""
    
    def __init__(self, symbols: List[str] = None)
    def analyze_all_factors(self) -> Dict
    def generate_report(self, results: Dict) -> str
```

---

### 5.2 analyze_all_factors

**功能**: 分析所有因子的 IC

**返回**:
```python
{
    'EURUSD': {
        'momentum': {'ic': float, 'valid': bool},
        'mean_reversion': {'ic': float, 'valid': bool},
        ...
    },
    'GBPUSD': {...},
    ...
}
```

**示例**:
```python
analyzer = FactorICAnalyzer()
results = analyzer.analyze_all_factors()

for symbol, factors in results.items():
    print(f"\n{symbol}:")
    for factor, ic_data in factors.items():
        print(f"  {factor}: IC={ic_data['ic']:.4f}")
```

---

## 六、Parameter Robustness Tester

### 6.1 类定义

```python
from v4_3.parameter_robustness import ParameterRobustnessTester

class ParameterRobustnessTester:
    """参数鲁棒性测试器"""
    
    def __init__(self, symbol: str = "EURUSD")
    def generate_parameter_combinations(self) -> List[Dict]
    def analyze_sensitivity(self, results: List[Dict]) -> Dict
    def find_optimal_range(self, results: List[Dict], 
                           top_percent: float = 0.2) -> Dict
    def test_robustness(self, results: List[Dict]) -> Dict
```

---

### 6.2 test_robustness

**功能**: 综合鲁棒性测试

**参数**:
- `results` (List[Dict]): 各参数组合的回测结果

**返回**:
```python
{
    'robustness_score': float,
    'passed': bool,
    'sensitivity_analysis': Dict,
    'optimal_ranges': Dict,
    'recommendation': str
}
```

**示例**:
```python
tester = ParameterRobustnessTester()
robustness = tester.test_robustness(results)

print(f"鲁棒性评分：{robustness['robustness_score']:.3f}")
print(f"是否通过：{'✅ PASS' if robustness['passed'] else '❌ FAIL'}")
```

---

## 七、OOS Validator

### 7.1 类定义

```python
from v4_3.oos_validation import OOSValidator

class OOSValidator:
    """样本外验证器"""
    
    def __init__(self, symbol: str = "EURUSD")
    def split_data(self, df: pd.DataFrame, 
                   train_ratio: float = 0.7) -> Tuple[pd.DataFrame, pd.DataFrame]
    def calculate_oos_performance(self, train_result: Dict, 
                                   test_result: Dict) -> Dict
    def validate(self, train_result: Dict, test_result: Dict,
                 returns: pd.Series = None) -> Dict
```

---

### 7.2 validate

**功能**: 综合 OOS 验证

**参数**:
- `train_result` (Dict): 训练集结果
- `test_result` (Dict): 测试集结果
- `returns` (pd.Series): 收益率序列（可选）

**返回**:
```python
{
    'oos_performance': Dict,
    'dsr_analysis': Dict,
    'passed': bool,
    'recommendation': str
}
```

**示例**:
```python
validator = OOSValidator()
result = validator.validate(train_result, test_result)

print(f"OOS 评分：{result['oos_performance']['oos_score']:.3f}")
print(f"是否通过：{'✅ PASS' if result['passed'] else '❌ FAIL'}")
```

---

## 八、Config Loader

### 8.1 类定义

```python
from v4_3.config_loader import ConfigLoader

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = None)
    def load_config(self, config_name: str) -> Dict[str, Any]
    def save_config(self, config_name: str, config: Dict[str, Any]) -> bool
    def get_config(self, config_name: str, key: str = None, 
                   default: Any = None) -> Any
    def validate_config(self, config_name: str, 
                        schema: Dict[str, Any]) -> bool
```

---

### 8.2 get_config

**功能**: 获取配置值

**参数**:
- `config_name` (str): 配置文件名称
- `key` (str): 配置键（支持嵌套，如 "trend.ADX_threshold"）
- `default` (Any): 默认值

**返回**:
- `Any`: 配置值

**示例**:
```python
loader = ConfigLoader()

# 获取整个配置
regime_config = loader.get_config('regime_config')

# 获取特定值
adx_threshold = loader.get_config('regime_config', 'trend.ADX_threshold', default=25)
momentum_weight = loader.get_config('factor_weights', 'momentum', default=0.3)
```

---

## 九、错误处理

### 9.1 常见错误

```python
# MT5 连接失败
class MT5ConnectionError(Exception):
    """MT5 连接错误"""
    pass

# 数据不足
class InsufficientDataError(Exception):
    """数据不足错误"""
    pass

# 配置错误
class ConfigError(Exception):
    """配置错误"""
    pass

# 风控拒绝
class RiskRejectError(Exception):
    """风控拒绝错误"""
    pass
```

---

### 9.2 错误处理示例

```python
try:
    result = engine.calculate_score("EURUSD", "H1")
except MT5ConnectionError as e:
    print(f"MT5 连接失败：{e}")
except InsufficientDataError as e:
    print(f"数据不足：{e}")
except ConfigError as e:
    print(f"配置错误：{e}")
```

---

## 十、快速参考

### 10.1 完整流程

```python
from v4_3.market_regime import MarketRegimeAgent
from v4_3.factor_score import FactorScoreEngine
from v4_3.risk_agent import RiskAgent

# 初始化
regime_agent = MarketRegimeAgent()
factor_engine = FactorScoreEngine()
risk_agent = RiskAgent()

# 扫描市场
regime = regime_agent.detect_regime("EURUSD", "H1")

if regime_agent.should_trade(regime):
    # 计算评分
    result = factor_engine.calculate_score("EURUSD", "H1")
    
    # 风控检查
    can_trade, reason = risk_agent.can_trade(...)
    
    if can_trade:
        print("可以交易")
    else:
        print(f"风控拒绝：{reason}")
else:
    print("市场状态不适合交易")
```

---

### 10.2 信号映射

| 评分范围 | 信号 | 含义 |
|----------|------|------|
| ≥70 | STRONG_BUY | 强烈买入 |
| 55-69 | BUY | 买入 |
| 46-54 | NEUTRAL | 中性 |
| 31-45 | SELL | 卖出 |
| ≤30 | STRONG_SELL | 强烈卖出 |

---

### 10.3 动态阈值

| 市场状态 | 信号阈值 |
|----------|----------|
| TRENDING_UP | 0.08% |
| TRENDING_DOWN | 0.08% |
| RANGING | 0.15% |
| HIGH_VOLATILITY | 0.20% |

---

**V4.3 Development Team**  
**2026-04-11**  
**清晰接口，高效开发**
