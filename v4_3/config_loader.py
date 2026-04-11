"""
配置加载器
版本：V4.3.0
创建：2026-04-11

功能：
1. 加载 JSON 配置文件
2. 参数验证
3. 默认值管理
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化
        
        Args:
            config_dir: 配置文件目录
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
        
        self.config_dir = config_dir
        self.configs = {}
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_name: 配置文件名称（不含.json）
            
        Returns:
            Dict: 配置内容
        """
        config_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        if not os.path.exists(config_path):
            print(f"[WARNING] 配置文件不存在：{config_path}")
            return self._get_default_config(config_name)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.configs[config_name] = config
        
        return config
    
    def save_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """
        保存配置文件
        
        Args:
            config_name: 配置文件名称
            config: 配置内容
            
        Returns:
            bool: 是否成功
        """
        config_path = os.path.join(self.config_dir, f"{config_name}.json")
        
        try:
            # 确保目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.configs[config_name] = config
            
            print(f"[OK] 配置已保存：{config_path}")
            return True
        
        except Exception as e:
            print(f"[ERROR] 保存配置失败：{e}")
            return False
    
    def get_config(self, config_name: str, key: str = None, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            config_name: 配置文件名称
            key: 配置键（可选，不传则返回整个配置）
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        if config_name not in self.configs:
            self.load_config(config_name)
        
        if config_name not in self.configs:
            return default
        
        config = self.configs[config_name]
        
        if key is None:
            return config
        
        # 支持嵌套键（如 "risk.max_daily_loss"）
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _get_default_config(self, config_name: str) -> Dict[str, Any]:
        """
        获取默认配置
        
        Args:
            config_name: 配置文件名称
            
        Returns:
            Dict: 默认配置
        """
        defaults = {
            'regime_config': {
                'trend': {
                    'ADX_threshold': 25,
                    'ema_short': 10,
                    'ema_long': 20
                },
                'volatility': {
                    'ATR_multiplier': 1.5,
                    'ATR_period': 14
                },
                'ranging': {
                    'ADX_threshold': 20,
                    'bollinger_period': 20
                },
                'dynamic_thresholds': {
                    'TRENDING_UP': 0.08,
                    'TRENDING_DOWN': 0.08,
                    'RANGING': 0.15,
                    'HIGH_VOLATILITY': 0.20
                }
            },
            'factor_weights': {
                'momentum': 0.3,
                'mean_reversion': 0.3,
                'breakout': 0.2,
                'volatility': 0.2
            },
            'risk_params': {
                'account': {
                    'min_margin_level': 200,
                    'max_leverage': 3.0,
                    'max_daily_loss_percent': 0.03,
                    'max_total_drawdown_percent': 0.10
                },
                'position': {
                    'max_positions': 3,
                    'max_same_symbol': 2,
                    'max_total_risk_percent': 0.03,
                    'risk_per_trade_percent': 0.005
                },
                'stop_loss': {
                    'atr_multiplier': 1.5,
                    'min_points': 20
                },
                'var': {
                    'confidence_level': 0.95,
                    'max_var_percent': 0.02
                }
            },
            'walk_forward_config': {
                'train_months': 6,
                'test_months': 1,
                'min_sharpe_train': 1.5,
                'min_sharpe_test': 1.0,
                'max_parameter_sensitivity': 0.20
            }
        }
        
        return defaults.get(config_name, {})
    
    def validate_config(self, config_name: str, schema: Dict[str, Any]) -> bool:
        """
        验证配置
        
        Args:
            config_name: 配置文件名称
            schema: 验证模式
            
        Returns:
            bool: 是否有效
        """
        config = self.get_config(config_name)
        
        if not config:
            return False
        
        # 简单验证：检查必需的键
        for key in schema.get('required', []):
            if key not in config:
                print(f"[ERROR] 配置缺少必需项：{key}")
                return False
        
        # 验证类型
        if 'types' in schema:
            for key, expected_type in schema['types'].items():
                if key in config:
                    if not isinstance(config[key], expected_type):
                        print(f"[ERROR] 配置类型错误：{key} 应为 {expected_type}")
                        return False
        
        return True


def main():
    """测试函数"""
    loader = ConfigLoader()
    
    print("=" * 80)
    print("配置加载器测试")
    print("=" * 80)
    
    # 加载配置
    regime_config = loader.load_config('regime_config')
    print(f"\nRegime Config: {json.dumps(regime_config, indent=2, ensure_ascii=False)}")
    
    factor_weights = loader.load_config('factor_weights')
    print(f"\nFactor Weights: {json.dumps(factor_weights, indent=2, ensure_ascii=False)}")
    
    risk_params = loader.load_config('risk_params')
    print(f"\nRisk Params: {json.dumps(risk_params, indent=2, ensure_ascii=False)}")
    
    # 获取特定值
    adx_threshold = loader.get_config('regime_config', 'trend.ADX_threshold', default=25)
    print(f"\nADX Threshold: {adx_threshold}")
    
    momentum_weight = loader.get_config('factor_weights', 'momentum', default=0.3)
    print(f"Momentum Weight: {momentum_weight}")
    
    max_daily_loss = loader.get_config('risk_params', 'account.max_daily_loss_percent', default=0.03)
    print(f"Max Daily Loss: {max_daily_loss}")


if __name__ == "__main__":
    main()
