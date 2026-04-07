# SRE Skills

> 沉淀 SRE 最佳实践，让故障排查更高效

[![GitHub stars](https://img.shields.io/github/stars/suziewong/sre-skills?style=social)](https://github.com/suziewong/sre-skills)
[![License](https://img.shields.io/github/license/suziewong/sre-skills)](https://github.com/suziewong/sre-skills/blob/main/LICENSE)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-blue)](https://github.com/openclaw/)

## 特性

- 🎯 **开箱即用** - 覆盖 SRE 最常见的故障场景
- 🔧 **可执行** - 每个技能都包含自动化脚本
- 📖 **案例驱动** - 真实案例沉淀，快速参考
- 🤖 **AI Ready** - 支持 LLM 增强的智能诊断
- 🌐 **开源免费** - Apache 2.0 协议

## 支持的场景

### 🔴 紧急类（故障时用）
- 🐬 `mysql-slow-query` - MySQL 慢查询定位
- ☸️ `k8s-pod-crash` - K8s Pod 异常排查
- 🌐 `network-timeout` - 网络超时定位
- 💾 `memory-leak` - 内存泄漏分析
- 💀 `oom-analysis` - OOM 问题诊断

### 🟡 巡检类（日常用）
- 📊 `health-check` - 系统健康度检查
- 📈 `capacity-planning` - 容量规划建议
- 💰 `cost-optimization` - 成本优化建议
- 🎯 `slo-analysis` - SLO 达成率分析

### 🟢 优化类（持续改进）
- ⚡ `performance-tuning` - 性能调优建议
- 🏗️ `architecture-review` - 架构评审
- 📝 `rca-generator` - 根因分析报告生成

## 快速开始

### 方式一：适用于 OpenClaw

```bash
# 安装所有 SRE Skills
claw skill install sre-skills

# 使用特定技能
claw skill use mysql-slow-query
```

### 方式二：直接使用

```bash
# 克隆仓库
git clone https://github.com/suziewong/sre-skills.git
cd sre-skills

# 查看技能列表
ls skills/
```

## 项目结构

```
sre-skills/
├── README.md
├── LICENSE
├── skill.json
├── skills/
│   ├── _template/         # 技能模板
│   ├── mysql-slow-query/  # MySQL 慢查询诊断
│   ├── k8s-pod-crash/     # K8s Pod 异常排查
│   └── ...
└── docs/
    ├── CONTRIBUTING.md    # 贡献指南
    └── TEMPLATE.md        # 如何创建新技能
```

## 如何贡献

欢迎贡献 SRE 技能！详见 [CONTRIBUTING.md](docs/CONTRIBUTING.md)

## License

Apache License 2.0 - 详见 [LICENSE](LICENSE)
