# 测试与基准

## 测试

运行全部测试：
```
pytest -q
```

- ACC
  - tests/test_accumulator.py：端到端 append/query/verify/update
  - tests/test_vds_acc.py：更新后旧证明应失败
  - tests/test_vds_acc_export_import.py：导出导入状态后继续查询
- CVC（SS512）
  - tests/test_vds_cvc.py：append/query/verify（已从 xfail 修复为通过）
  - tests/test_vds_cvc_update.py：随机更新后验证

## 基准（规划）

- bench/bench_acc.py：U∈{0,100,1000,5000}；记录生成/验证耗时、证明大小、powers 补齐开销；输出 CSV
- bench/bench_cvc.py：q∈{32,64,128} 与 N 规模；记录路径长度与验证耗时的趋势

