# ledger-publisher

**Publisher for 可验证透明日志平台**

Publishes daily proof bundles to GitHub Pages with automatic verification.

---

## 🎯 功能

- ✅ 按日构建 Proof Bundle
- ✅ 自动生成 Merkle root
- ✅ 生成 manifest + checkpoint
- ✅ GitHub Actions 自动发布
- ✅ 只追加守卫（append-only guard）
- ✅ 支持多种 Profile（可扩展）

---

## 🚀 快速开始

### 本地构建 Bundle

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成示例数据（100条记录）
python -m adapters.domain_onchain_payments.export sample \
  --output records.jsonl \
  --count 100

# 3. 构建 Bundle
python -m builder.build \
  --input records.jsonl \
  --profile-dir ../ledger-spec/profiles \
  --profile domain-onchain-payments \
  --date 2026-01-17 \
  --output dist/

# 4. 查看结果
ls dist/proofs/2026-01-17/
```

### GitHub Actions 自动发布

```bash
# 1. Fork 本仓库

# 2. 修改 .github/workflows/publish.yml 中的配置
#    - 改 your-org 为你的组织名
#    - 改 remote_url 为你的 GitHub Pages URL

# 3. 启用 GitHub Actions
#    Settings → Actions → I understand my workflows, enable them

# 4. 推送代码
git add .
git commit -m "Enable automatic publishing"
git push

# Done! 每天自动运行 ✨
```

---

## 📁 目录结构

```
ledger-publisher/
├── builder/                    # 核心构建逻辑
│   ├── __init__.py
│   ├── build.py              # 主构建脚本
│   ├── merkle.py             # Merkle 树计算
│   ├── normalizers.py        # 字段标准化
│   ├── manifest.py           # Manifest 生成
│   └── append_only_guard.py   # 只追加守卫
├── adapters/                  # 数据适配器
│   └── domain-onchain-payments/
│       └── export.py         # 导出示例
├── profiles/                  # 从 spec 复制的 profile
├── config/                    # 配置文件
├── .github/workflows/
│   └── publish.yml           # GitHub Actions
├── pages/                     # 静态页面
├── tests/                     # 测试
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 🔧 核心 API

### build.build_bundle()

```python
from builder import build_bundle

result = build_bundle(
    input_file="records.jsonl",
    profile_dir="../ledger-spec/profiles",
    profile_id="domain-onchain-payments",
    date="2026-01-17",
    output_dir="dist/"
)
```

**输出：**
- `dist/proofs/2026-01-17/records-000.jsonl`
- `dist/proofs/2026-01-17/daily_root.txt`
- `dist/proofs/2026-01-17/manifest.json`
- `dist/proofs/2026-01-17/checkpoint.json`
- `dist/proofs/2026-01-17/core_spec.json`
- `dist/proofs/2026-01-17/profile.json`

---

## 🛡️ 安全特性

### Append-Only Guard

```python
from builder import append_only_guard

# 检查是否可以发布（防篡改）
append_only_guard.check_append_only(
    bundle_dir="dist/proofs/2026-01-17",
    remote_url="https://your-org.github.io/ledger-publisher"
)
```

**规则：**
- 新日期：✅ 允许发布
- 已存在 + manifest 相同：✅ 幂等（允许）
- 已存在 + manifest 不同：❌ 失败（阻止篡改）

---

## 📊 数据流

```
内部数据源
    ↓
adapters/export.py
    ↓
records.jsonl (JSONL格式)
    ↓
builder.build()
    ↓
proofs/YYYY-MM-DD/
    ├── records-*.jsonl
    ├── daily_root.txt
    ├── manifest.json
    ├── checkpoint.json
    ├── core_spec.json
    └── profile.json
    ↓
GitHub Actions
    ↓
gh-pages 分支
    ↓
https://your-org.github.io/ledger-publisher/proofs/YYYY-MM-DD/
```

---

## 🧪 测试

```bash
# 运行测试（如果有）
python -m pytest tests/

# 手动验证
python -m builder.build --input tests/sample.jsonl --output dist/
```

---

## 🔌 自定义

### 添加新 Adapter

```python
# adapters/your-profile/export.py

def export_from_database():
    # 从数据库导出 records.jsonl
    pass
```

### 添加新 Profile

1. 在 `ledger-spec/profiles/` 创建新 profile
2. 复制 adapter 模板
3. 更新 `publish.yml` 配置

---

## 📖 文档

- [Core Spec](../ledger-spec/CORE_SPEC.md)
- [Profile 规范](../ledger-spec/profiles/domain-onchain-payments/)
- [完整项目方案](../完整项目方案_修正版.md)

---

## 🤝 贡献

欢迎提交 PR！

1. Fork 本仓库
2. 创建 feature 分支
3. 提交 PR
4. 等待 CI 通过

---

## 📄 许可

待定（项目启动时确定）
