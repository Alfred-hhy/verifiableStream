# ACC 方案代码走读与 API

本节详细解释 VDS-ACC 的实现、API、数据流与代码位置，对应论文 Construction 4。

## 设计回顾

- 客户端持有陷门 s 与签名密钥 ssk；公开参数包含 g1∈G1、h∈G2、hs=h^s、签名验签公钥 vk。
- 服务器保存数据项 (data, tag, idx, σ)，并维护多项式 f(X)=∏(X+x_i)（x_i 为被加入黑名单的签名哈希）。
- 查询时服务器生成非成员证明 (w, v) 使得：
  - v = f(-y) 且 Q(X) = (f(X)-v)/(X+y)
  - w = g1^{Q(s)}
  - 验证：e(w, h^y·hs) == e(A·g1^{-v}, h)

## 关键文件与函数

- vds/acc/accumulator.py
  - acc_setup(grp) → (ACCKey, ACCState)：生成 s, g1, h, hs，初始化 A=g1，powers=[g1, g1^s]
  - acc_add(grp, key, st, x)：客户端将 x 加入黑名单：A←A^{(x+s)}，并扩展 powers（下一阶 g1^{s^k}）
  - poly_eval/poly_div_linear：多项式 Horner 与线性因子长除（简版）；后续替换为乘积树
  - acc_nonmem_verify(...)：验证非成员等式
- vds/acc/vds_acc.py（VDS 封装）
  - setup() → (ACCPublic, state_bytes)：生成密钥、参数，初始化服务器侧存储（acc_value、powers、f_coeffs）
  - append(st, data) → AppendReceipt：签名 encode(data,tag,idx) 后保存；不改累加器
  - query(idx) → QueryProof：服务器取出 σ，计算 y、v、Q、w，返回 payload（σ,w,v,tag）
  - verify(pub, idx, data, proof) → bool：先验签，再验配对等式
  - update(st, idx, new_data) → UpdateReceipt：
    - 先 query+verify 旧项，令 x=H(σ_old)
    - 客户端 acc_add(A, x) 推进累加器值与 powers
    - 服务器 f(X) ← f(X)·(X+x)
    - 生成新签名并替换数据项；返回新根（A）
  - export_state / import_state：状态导出导入（包含版本与曲线元数据）

## API 与类型

- ACCPublic（vds/common/types.py）：{ g:G1, gs:{h,hs}, vk_sig, accumulator }
- QueryProof：{ scheme='acc', index, payload=msgpack({sigma,w,u=v,tag}) }
- AppendReceipt/UpdateReceipt：包含 index 与 RootDigest（根=当前累加器 A 的序列化）

## 代码参考位置

- acc_setup：vds/acc/accumulator.py:20
- VDSACC.setup：vds/acc/vds_acc.py:39
- VDSACC.append：vds/acc/vds_acc.py:87
- VDSACC.query：vds/acc/vds_acc.py:108
- VDSACC.verify：vds/acc/vds_acc.py:132
- VDSACC.update：vds/acc/vds_acc.py:172

## 后续优化

- 用多项式乘积树替换 poly_eval/div，提高 f(-y)、Q(X) 计算速度
- 使用 multi-exponentiation 计算 w = g1^{Q(s)}（基于 powers）
- 定义 NeedMorePowers 异常，当 deg(Q) ≥ len(powers) 时触发，通过 append_powers 一次性补齐

