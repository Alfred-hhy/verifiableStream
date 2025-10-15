# CVC 方案代码走读与 API（基线）

本节解释 VDS-CVC 的当前“基线版本”（SS512 对称群），并给出将来扩展到非对称群的建议。

## 设计回顾（基线）

- 节点承诺为长度 q+1 的向量：槽 1 存数据哈希 m_data，槽 2..q+1 存子指针哈希 m_ptr。
- 承诺：C = g^r ∏ h_i^{m_i}，其中 h_i=g^{z_i}（keygen 生成），h_{i,j}=g^{z_i z_j} 用于证明。
- 槽 i 的开放证明：π_i = h_i^r ∏_{j≠i} h_{i,j}^{m_j}；验证：e(C·h_i^{-m_i}, h_i) == e(π_i, g)。
- 当前实现：query 阶段直接用 open_slot 基于节点当前向量 m 与 r 计算 π（O(q)）。

## 关键文件与函数

- vds/cvc/cvc_core.py
  - keygen(grp, q)：生成 g、z_i、h_i、h_{i,j} 并对 (h_i||i) 签名；返回 pk/sk 与服务器缓存
  - commit_vec/open_slot/verify_slot/update_commit：对应数学接口
- vds/cvc/vds_cvc.py（VDS 封装）
  - setup：初始化根节点 r_1 与空向量承诺
  - append：叶子写数据槽，沿父链更新子指针槽（2..q+1），更新父节点承诺
  - query：返回叶段与父链段的 (C, π, h_i, signed_hi)
  - verify：逐段自底向上验证，最终比较根
  - update：显式更新策略（不使用变色龙 δr），按 “Δ 子指针哈希” 自底向上更新承诺与 ledger

## 一致性细节

- 指针哈希：m_ptr = H_zr(serialize_G1(C_child))，append/update/query/verify 全流程一致
- 槽位索引：1=数据，2..q+1=子指针（父链中，根据子编号确定 slot_idx=slot+1）
- 验签：signed_hi 携带 (h_i||i) 的 Ed25519 签名；客户端验证后才进入配对

## 非对称群最小实现建议

- 生成：g1∈G1、g2∈G2，槽基 h_j=g1^{b_j}，证明基 h_i*=g2^{a_i}，交互基 h_{i,j}=g1^{a_i b_j}
- 验证：e(C·h_j^{-m_j}, h_i*) == e(π_i, g2)
- 微调：keygen 签名 (h_i*||i)；序列化、哈希不变

## 代码参考位置

- keygen：vds/cvc/cvc_core.py:18
- VDSCVC.setup：vds/cvc/vds_cvc.py:31
- VDSCVC.append：vds/cvc/vds_cvc.py:60
- VDSCVC.query：vds/cvc/vds_cvc.py:112
- VDSCVC.verify：vds/cvc/vds_cvc.py:149
- VDSCVC.update：vds/cvc/vds_cvc.py:179

