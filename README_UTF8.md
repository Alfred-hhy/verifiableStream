# verifiableStream（可验证数据流 VDS）

本仓库实现两种可插拔的 VDS 方案：
- VDS-ACC：签名 + 双线性累加器（论文 Construction 4）。已完成并通过测试。
- VDS-CVC：q 叉树 + Chameleon Vector Commitment（论文 Construction 3）的“基线版本”。支持 append/query/verify/update（在对称群 SS512 下），用于论文复现实验。后续可切换到非对称群并加入常数时间 ledger 优化。

当前状态
- 测试：`7 passed, 1 skipped, 1 xpassed`
- CLI：提供 `acc` 与 `cvc` 的最小可运行演示（ACC 支持状态持久化；CVC 通过重放实现持久化）
- 依赖：`charm-crypto`, `cryptography`, `pydantic`, `click`, `pytest`, `hypothesis`, `pytest-benchmark`, `msgpack`

目录结构
- `vds/common`：通用工具（配对群、哈希、编码、签名、序列化、异常、类型）
- `vds/acc`：ACC 原语与 VDS 封装
- `vds/cvc`：CVC 原语与 VDS 封装（SS512 基线）
- `vds/storage`：内存存储（演示用）
- `vds/cli`：命令行工具 `vds_cli.py`
- `tests`：单元测试与性质测试
- `bench`：基准脚本（待完善）

## 安装

1) 安装依赖
```
pip install -r requirements.txt
```
确保系统可安装并加载 `charm-crypto`（例如 Ubuntu 20.04+/WSL2 环境）。

2) 运行测试
```
pytest -q
```

## CLI 使用示例

CLI 使用 msgpack 文件保存状态；ACC 完整持久化，CVC 通过重放方式恢复。

查看帮助：
```
python -m vds.cli.vds_cli --help
```

### ACC 流程（推荐）

1) 初始化
```
python -m vds.cli.vds_cli init --scheme acc --curve MNT224 --store ./acc_state.msgpack
```
输出 JSON 含耗时与路径。状态文件内包含：公开参数、公钥、客户端状态、累加器值 A、powers（g^{s^k}）、多项式系数 f_coeffs、已写入 items。

2) 追加数据
```
python -m vds.cli.vds_cli append --scheme acc --store ./acc_state.msgpack --data 0x68656c6c6f
```
`--data` 支持十六进制、文件路径或直接字符串（UTF-8）。命令更新状态文件并返回新索引与 root（A）的字节长度。

3) 查询并导出证明
```
python -m vds.cli.vds_cli query --scheme acc --store ./acc_state.msgpack --index 1 --out ./acc_proof.bin
```
`out` 文件保存的是 `QueryProof.payload`（msgpack 格式，包含 σ, w, v 等）。

4) 验证
```
python -m vds.cli.vds_cli verify --scheme acc --store ./acc_state.msgpack --index 1 --data 0x68656c6c6f --proof ./acc_proof.bin
```
返回 `{"ok": true}` 则通过。

5) 更新
```
python -m vds.cli.vds_cli update --scheme acc --store ./acc_state.msgpack --index 1 --data 0x6e6577
```
执行后根（A）发生变化，旧签名被加入黑名单，再次用旧数据验证应失败。

### CVC 基线（SS512 对称群）

1) 初始化
```
python -m vds.cli.vds_cli init --scheme cvc --q 64 --store ./cvc_state.msgpack
```

2) 追加/查询/验证
```
python -m vds.cli.vds_cli append --scheme cvc --store ./cvc_state.msgpack --data 0x616161
python -m vds.cli.vds_cli query --scheme cvc --store ./cvc_state.msgpack --index 1 --out ./cvc_proof.bin
python -m vds.cli.vds_cli verify --scheme cvc --store ./cvc_state.msgpack --index 1 --data 0x616161 --proof ./cvc_proof.bin
```

3) 更新
```
python -m vds.cli.vds_cli update --scheme cvc --store ./cvc_state.msgpack --index 1 --data 0x626262
```

说明：当前 CVC 状态持久化通过“重放 items”恢复（依赖 sk.prf_key 的确定性），不直接序列化内部树节点。后续可替换为文件化持久化实现。

## Python 方式使用（简例）

```
from charm.toolbox.pairinggroup import PairingGroup
from vds.storage.memstore import MemStore
from vds.acc.vds_acc import VDSACC

grp = PairingGroup('MNT224')
store = MemStore()
vds = VDSACC(store, grp)
pub, st = vds.setup()

rec = vds.append(st, b'hello')
q = vds.query(1)
assert vds.verify(pub, 1, b'hello', q)

upd = vds.update(st, 1, b'world')
pub.accumulator = upd.root.value
q2 = vds.query(1)
assert vds.verify(pub, 1, b'world', q2)
```

## 设计要点与安全注意
- ACC：H_zr 使用固定域分离前缀（b'ACC_SIG'），验证包含签名验签与配对等式；缺少 powers 时应通过错误码提示补齐（后续优化版本引入）。
- CVC：路径中的 h_i 必须验签；当前 query 使用 open_slot 即时构造证明（O(q)），常数时间 ledger 优化留作 TODO。
- 序列化：统一使用 msgpack；群元素用 charm 的 serialize/deserialize；整数使用大端字节。
- 子群检查：Charm 通常在反序列化中包含检查，如需可在 `common/group.py` 补充二次校验。

## 基准（规划）
- ACC：实现乘积树与 multi-exponentiation 后，测 U∈{0,100,1000,5000} 的生成/验证耗时、证明大小、补齐开销，输出 CSV。
- CVC：log_q(N) 的路径长度与验证耗时趋势（q∈{32,64,128}）。

## 版本
- 包版本：`vds.__version__` （当前 0.1.0）

