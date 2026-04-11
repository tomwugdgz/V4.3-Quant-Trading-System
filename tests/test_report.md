================================================================================
V4.3 系统完整性测试报告
================================================================================
测试时间：2026-04-11 14:42:40

总测试数：10
通过：7
失败：3
通过率：70.0%

错误列表:
--------------------------------------------------------------------------------
[FAIL] 因子计算: Invalid frequency: H. Failed to parse with error message: ValueError("Invalid frequency: H. Failed to parse with error message: KeyError('H'). Did you mean h?") Did you mean h?
[FAIL] 配置加载器: 
[FAIL] Review Agent: Execution failed on sql '
        SELECT * FROM orders 
        WHERE DATE(created_at) = '2026-04-11'
        ': no such table: orders

详细结果:
--------------------------------------------------------------------------------
PASS: 因子库导入
PASS: Market Regime 导入
PASS: Factor Score 导入
PASS: Risk Agent 导入
PASS: Review Agent 导入
PASS: Config Loader 导入
FAIL: 因子计算
       Invalid frequency: H. Failed to parse with error message: ValueError("Invalid frequency: H. Failed to parse with error message: KeyError('H'). Did you mean h?") Did you mean h?
PASS: 加载 Regime Config
FAIL: 配置加载器
FAIL: Review Agent
       Execution failed on sql '
        SELECT * FROM orders 
        WHERE DATE(created_at) = '2026-04-11'
        ': no such table: orders

================================================================================
*V4.3 System Tester - 质量保障，持续交付*