# SRE Skills 技能模板

## 创建新技能指南

### 1. 目录结构

```
skills/
└── <skill-name>/           # 技能目录，使用连字符命名
    ├── SKILL.md            # 技能元数据和说明
    ├── DIAGNOSIS.md        # 诊断流程
    ├── CHECKLIST.md        # 快速检查清单
    ├── SCRIPTS/            # 自动化脚本
    │   ├── script1.py
    │   └── script2.sh
    └── CASES/              # 案例库
        └── case_001.md
```

### 2. SKILL.md 模板

```yaml
name: <skill-name>
name_zh: <中文名称>
category: [sre|devops|security|network]
tags: [<相关标签>]
severity: [critical|high|medium|low]
icon: <emoji>
status: [planned|wip|ready|deprecated]

description: |
  技能详细描述
  
triggers:
  - "触发关键词1"
  - "触发关键词2"

capabilities:
  - 能力1
  - 能力2

inputs:
  - name: <参数名>
    type: <string|number|boolean>
    required: <true|false>
    default: <默认值>
    description: <参数描述>

outputs:
  - name: <输出名>
    type: <markdown|json|text>
    description: <输出描述>
```

### 3. 命名规范

- 技能名称：小写字母 + 连字符
- 中文名称：简洁明了
- 标签：使用通用标签便于搜索

### 4. 状态说明

| 状态 | 说明 |
|------|------|
| `planned` | 计划中，尚未开始 |
| `wip` | 开发中 |
| `ready` | 就绪可用 |
| `deprecated` | 已废弃 |

### 5. 贡献流程

1. Fork 仓库
2. 创建新分支 `git checkout -b skills/<skill-name>`
3. 按照模板创建技能
4. 添加测试用例
5. 提交 PR

### 6. 质量标准

- [ ] 包含完整的 SKILL.md
- [ ] 有详细的 DIAGNOSIS.md
- [ ] 提供快速 CHECKLIST.md
- [ ] 至少包含一个可执行脚本
- [ ] 至少包含一个真实案例（可选但推荐）
