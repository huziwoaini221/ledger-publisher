# Merkle Proof API

## 概述

Merkle Proof API 允许验证单条记录是否属于某个 proof bundle，而无需下载整个 bundle。

## 核心概念

### Merkle Proof

Merkle proof 是一条从特定记录（叶子节点）到 Merkle 根的路径证明。包含：
- **leaf_hash**: 记录的哈希值
- **proof**: 路径上所有兄弟节点的哈希
- **expected_root**: 期望的 Merkle 根

### 验证过程

1. 从 leaf_hash 开始
2. 遍历 proof 中的每个步骤
3. 根据方向（left/right）与兄弟节点哈希配对
4. 计算父哈希，重复直到根
5. 比较计算结果与 expected_root

## API 使用

### 1. 生成 Proofs

Proofs 会在构建 bundle 时自动生成：

```bash
python -m builder.build \
  --input records.jsonl \
  --profile-dir ../ledger-spec/profiles \
  --profile domain-onchain-payments \
  --date 2026-01-18 \
  --output dist/
```

生成的文件结构：

```
dist/proofs/2026-01-18/
├── records-000.jsonl
├── manifest.json
├── daily_root.txt
├── proof_index.json       # Proof 索引
└── proofs/                # Proofs 目录
    ├── 0.json            # 第 0 条记录的 proof
    ├── 1.json            # 第 1 条记录的 proof
    ├── 2.json
    └── ...
```

### 2. 查询单条 Proof

通过 GitHub Pages 访问：

```bash
# 获取第 0 条记录的 proof
curl https://huziwoaini221.github.io/ledger-publisher/2026-01-18/proofs/0.json
```

响应示例：

```json
{
  "leaf_index": 0,
  "leaf_hash": "abc123...",
  "proof": [
    {
      "direction": "left",
      "sibling_hash": "def456..."
    },
    {
      "direction": "right",
      "sibling_hash": "789abc..."
    }
  ],
  "expected_root": "ec650ccad..."
}
```

### 3. 本地验证 Proof

使用 Python SDK：

```python
from builder.merkle import verify_proof

# Proof 数据
proof_data = {
    "leaf_hash": "abc123...",
    "proof": [
        {"direction": "left", "sibling_hash": "def456..."},
        {"direction": "right", "sibling_hash": "789abc..."}
    ],
    "expected_root": "ec650ccad..."
}

# 验证
is_valid = verify_proof(
    proof_data["leaf_hash"],
    proof_data["proof"],
    proof_data["expected_root"]
)

if is_valid:
    print("✅ Proof valid!")
else:
    print("❌ Proof invalid!")
```

### 4. 批量查询

使用 proof_index.json：

```bash
# 获取 proof 索引
curl https://huziwoaini221.github.io/ledger-publisher/2026-01-18/proof_index.json
```

响应：

```json
{
  "version": "1",
  "total_records": 100,
  "merkle_root": "ec650ccad...",
  "proofs": [
    {
      "record_index": 0,
      "proof_file": "proofs/0.json",
      "leaf_hash": "abc123..."
    },
    {
      "record_index": 1,
      "proof_file": "proofs/1.json",
      "leaf_hash": "def456..."
    }
  ]
}
```

## 使用场景

### 场景 1: SPV (简化支付验证)

验证某笔交易是否在账本中，无需下载全部交易：

```python
# 1. 获取记录索引（通过其他方式）
record_index = find_record_index(txid="0x123...")

# 2. 下载 proof
proof = download_proof(f"{date}/proofs/{record_index}.json")

# 3. 验证
if verify_proof(proof["leaf_hash"], proof["proof"], trusted_root):
    print("✅ Transaction verified!")
```

### 场景 2: 审计证据

提供特定记录的不可篡改证据：

```python
# 为审计员生成 proof
proof = generate_merkle_proof(record_index)

# 审计员可以独立验证
if verify_proof(...):
    print("✅ Audit evidence valid")
```

### 场景 3: 轻量级客户端

移动端或资源受限设备验证记录：

```python
# 只需要下载：
# - 单条记录
# - 对应的 proof（很小，几百字节）
# - 信任的 Merkle root

# 不需要下载整个 bundle（可能几 MB 或更大）
```

## Proof 大小分析

Proof 大小取决于记录数量：

| 记录数 | Proof 深度 | Proof 大小 |
|--------|----------|-----------|
| 100    | 7 levels | ~500 bytes |
| 1,000  | 10 levels | ~700 bytes |
| 10,000 | 14 levels | ~1 KB |
| 100,000| 17 levels | ~1.2 KB |

即使有数百万条记录，proof 也只有几千字节。

## 安全性

### 1. 哈希碰撞

SHA256 是加密安全的哈希函数，碰撞概率可忽略：
- 2^256 次方分之一
- 实际上不可能发生

### 2. 伪造 Proof

无法伪造有效的 proof，因为：
- 每个步骤都需要正确的哈希配对
- 最终必须匹配已知的 Merkle root
- 修改任何步骤都会导致最终根不匹配

### 3. 篡改检测

如果记录被篡改：
- leaf_hash 会改变
- 验证会失败
- 篡改可以被立即检测

## 性能

### 生成时间

- 100 条记录: ~0.1 秒
- 1,000 条记录: ~0.5 秒
- 10,000 条记录: ~3 秒
- 100,000 条记录: ~30 秒

### 验证时间

无论记录数量多少，验证都是 O(log n)：
- 通常 < 1 毫秒
- 适合实时验证

## 测试

运行测试：

```bash
python3 tests/test_merkle_proofs.py
```

测试覆盖：
- ✅ 小树（4个叶子）
- ✅ 大树（100个叶子）
- ✅ Proof 结构验证
- ✅ 篡改检测

## 示例代码

完整示例见：
- `tests/test_merkle_proofs.py`
- `builder/generate_proofs.py`

## 故障排查

### Q: Proof 验证失败

**可能原因**:
1. Merkle root 不匹配
2. Proof 数据损坏
3. 记录内容被篡改

**解决方法**:
1. 重新下载 proof
2. 验证 Merkle root 来源
3. 检查网络连接

### Q: 找不到 proof 文件

**可能原因**:
1. Bundle 构建时未生成 proofs
2. Record index 超出范围

**解决方法**:
1. 检查 bundle 是否包含 `proofs/` 目录
2. 验证 index 在有效范围内 [0, total_records-1]

## 下一步

- [ ] 添加 Proof 压缩
- [ ] 实现 Proof 批量验证
- [ ] 添加 Proof 缓存
- [ ] 支持增量 Proof 更新
