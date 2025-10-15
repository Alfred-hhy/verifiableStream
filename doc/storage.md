# 存储抽象与实现

当前实现主要使用内存存储（MemStore），用于 demo 与测试。文件存储（FileStore）为占位。

## 接口（MemStore）

- set_root/get_root：方案根（未广泛使用；根由客户端持有）
- CVC：
  - put_cvc_insert_path/get_cvc_auth_path/apply_cvc_updates（当前基线未用）
- ACC：
  - save_acc_item(idx, data, tag, sigma)
  - get_acc_item(idx)
  - set_acc_state()/get_acc_state()：累加器值与 powers 缓存
  - set_acc_poly()/get_acc_poly()：f(X) 系数（ascending）
  - acc_count()：当前已保存的条目数
  - append_powers(new)：追加 powers（供“缺幂补齐”接口使用）

## 说明

- ACC 状态导出时，从 MemStore 读取 accumulator/powers/f_coeffs，一并写入导出 blob。
- 导入时，重建 MemStore 的上述值；items 由上层自行迁移（测试中示例）。

