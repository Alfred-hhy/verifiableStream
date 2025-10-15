# 前置知识与工具

本项目涉及双线性配对、群运算、哈希到域、数字签名、序列化与 Python 工具链。建议掌握以下基础。

## 数学与密码学

- 双线性配对与群：G1、G2、GT、ZR，双线性 map e : G1×G2→GT（对称群时 G1=G2）。
- 指数与群运算：a**x 表示幂运算，群乘法写作 “*”。
- 承诺与向量承诺：本项目 CVC 采用线性承诺 C = g^r ∏ h_i^{m_i}。
- 累加器（Nguyen/Damgård–Triandopoulos）与（非）成员证明公式。
- 变色龙哈希/承诺思想：通过 trapdoor 更新随机性保持承诺不变（当前基线未用）。

## 库与工具

- charm-crypto（配对群）
  - PairingGroup('MNT224'/'BN254'/'SS512')
  - 元素类型：G1/G2/GT/ZR
  - 运算：乘法 `*`、幂 `**`、配对 `pair(a,b)`、序列化 `grp.serialize(elem)`
- cryptography（Ed25519）
  - 生成、签名与验证
- pydantic（数据模型）
  - vds/common/types.py 中的模型用于结构化返回与检查
- msgpack（序列化）
  - 统一对象打包
- click（CLI）
  - 命令行解析
- pytest / hypothesis / pytest-benchmark
  - 测试与基准

## 开发环境建议

- Python 3.11+
- Ubuntu/WSL2 推荐；确保能安装 charm-crypto
- 创建虚拟环境，安装 requirements.txt

