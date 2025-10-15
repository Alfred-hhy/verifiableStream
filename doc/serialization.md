# 序列化与哈希规范

为确保客户端/服务器/测试一致性，项目统一了以下规则：

- 群元素序列化：使用 charm 的 `grp.serialize(elem)`；反序列化 `grp.deserialize(b)`。
- 指数（ZR）由 charm 内部维护模数，构造时使用 `grp.init(ZR, int_value)`。
- 消息打包：统一使用 msgpack（vds/common/ser.py 提供 pack/unpack）。
- H_zr：`vds/common/group.py::H_zr(grp, bytes)` 使用 SHA-256 → 整数 → `grp.init(ZR, n)`，用于：
  - ACC：`y = H_zr(b'ACC_SIG' || σ)`（域分离）
  - CVC：`m_data = H_zr(data)` 与 `m_ptr = H_zr(serialize_G1(C_child))`
- serialize_G1：`vds/common/group.py::serialize_G1`，用于 CVC 指针哈希的唯一序列化。

注意：
- 反序列化后，Charm 通常包含子群检查；如需额外稳妥，可在关键路径上做一次确认（例如乘以群阶是否回到单位元）。

