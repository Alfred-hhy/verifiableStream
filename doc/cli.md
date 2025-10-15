# CLI 使用说明

命令行入口：`python -m vds.cli.vds_cli`。

所有命令输出 JSON，便于脚本处理；ACC/CVC 的状态会保存到指定的 msgpack 文件。

## 常用命令

- 初始化
  - ACC：`init --scheme acc --curve MNT224 --store ./acc_state.msgpack`
  - CVC：`init --scheme cvc --q 64 --store ./cvc_state.msgpack`
- 追加数据
  - `append --scheme <acc|cvc> --store <state.msgpack> --data <hex|file|text>`
- 查询证明
  - `query --scheme <acc|cvc> --store <state.msgpack> --index N --out proof.bin`
- 验证
  - `verify --scheme <acc|cvc> --store <state.msgpack> --index N --data <...> --proof proof.bin`
- 更新
  - `update --scheme <acc|cvc> --store <state.msgpack> --index N --data <...>`

## 备注

- ACC：状态包含 accumulator 值 A、powers（g^{s^k} 列表）、f_coeffs（f(X) 系数），以及 items（服务器已存的数据项）。
- CVC：状态通过重放 items 恢复树；后续可替换为直接持久化树节点。
- `--data` 支持十六进制字符串（可用 0x 前缀）、文件路径、或直接文本（UTF-8）。

