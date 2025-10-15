# 项目总览（verifiableStream）

本项目实现并演示两类可验证数据流（VDS, Verifiable Data Streaming）方案，目标是提供可插拔的 ACC 模块与一条可复现论文结论的 CVC 基线。

- VDS-ACC（Construction 4）：Ed25519 签名 + 双线性累加器（黑名单）。验证 O(1)，服务器生成证明随更新次数 U 增长。
- VDS-CVC（Construction 3，基线）：q 叉树 + Chameleon Vector Commitment。当前采用对称群（SS512）用于快速验证思路，支持 append/query/verify/update；后续可切换到非对称群并完成常数时间 ledger 优化。

仓库亮点
- Python 包结构清晰，ACC/CVC 两条方案彼此隔离、可替换。
- CLI 可直接演示 ACC/CVC 的初始化、追加、查询、验证、更新。
- 测试覆盖端到端流程；CVC 的对称群基线已通过；ACC 全流程通过。
- 预留性能优化入口（ACC 多项式乘积树、multi-exponentiation；CVC ledger 常数时间更新）。

## 目录导航

- doc/overview.md（本文）：总体介绍与导航
- doc/prerequisites.md：配对群/密码学/工具链前置知识
- doc/serialization.md：序列化、哈希、域分离与一致性
- doc/acc.md：ACC 方案代码走读与 API
- doc/cvc.md：CVC 方案代码走读与 API（基线 + 拟实现的非对称变体）
- doc/storage.md：存储抽象与内存实现
- doc/cli.md：命令行使用说明
- doc/testing.md：测试与基准规划
- doc/faq.md：常见问题（Charm 安装、曲线选择等）

## 代码结构（简述）

- vds/common：通用组件（群、签名、PRF、序列化、类型、异常）
- vds/acc：累加器与 VDS 封装
- vds/cvc：向量承诺原语与 VDS 封装
- vds/storage：内存/文件存储（当前主要使用内存版）
- vds/cli：命令行工具
- tests：单元测试与端到端用例
- bench：性能基准（占位，待完善）

## 当前测试现状

- ACC：端到端全部通过
- CVC（SS512）：append/query/verify/update 通过；父段证明采用 open_slot 直接构造（O(q)），ledger 常数时间优化留作 TODO

