# 🛠️ Dev Problem-Solving Journal

> **仓库定位**：聚焦 Java 后端开发，记录真实生产环境中的疑难问题、排查思路、解决方案及底层原理延伸。
> **更新频率**：随项目迭代持续更新，欢迎通过 Issues 交流讨论。

## 📂 内容导航

> 💡 **提示**：本仓库采用自动化索引（`update_readme.py`），案例数量与最近更新信息由脚本自动生成。也可使用 GitHub 搜索功能（`t` 键）快速定位内容。

### 按技术领域分类

<!-- TABLE_START -->
| Java 核心与框架 | JDK 17/21, Spring Boot, Spring Cloud | 1 | 2026-08-01 |
| 数据库与存储 | TiDB, MongoDB, Redis | 0 | - |
| 搜索与中间件 | Elasticsearch, RocketMQ/Kafka | 0 | - |
| 容器化与编排 | Docker, Kubernetes | 0 | - |
| 可观测性与运维 | Prometheus, Grafana, SkyWalking | 0 | - |
| 架构与设计模式 | 分布式架构, DDD, 设计模式 | 1 | 2026-08-01 |
<!-- TABLE_END -->

### 按时间线归档

<!-- TIMELINE_START -->
- [2026 年](./2026/)（1 篇）
  <!-- TIMELINE_END -->

## 📝 案例文档规范

每个案例文档遵循以下结构，确保信息完整、可复用：

```markdown
# [问题简述] - [核心技术点]

## 🐛 问题背景
- **项目/场景**：
- **现象描述**：
- **影响范围**：

## 🔍 排查思路
1. **初步判断**：
2. **验证过程**：
3. **关键线索**：

## ✅ 解决方案
- **核心方案**：
- **代码/配置示例**：
- **验证结果**：

## 📚 知识点延伸
- **相关原理**：
- **最佳实践**：
- **参考资料**：

## 🏷️ 标签
#java #tidb #k8s #performance
```

> ⚠️ **标签规范**：`## 🏷️ 标签` 中的标签用于自动分类统计，请使用**小写英文**标签，多个标签以空格分隔。支持的标签见下方[标签映射表](#标签分类映射)。

### 标签分类映射

`update_readme.py` 根据以下映射关系将标签归类到技术领域：

| 标签 | 归类到 |
| --- | --- |
| `java`, `spring`, `spring-boot`, `spring-cloud`, `jdk`, `jvm`, `mybatis`, `hibernate` | Java 核心与框架 |
| `tidb`, `mongodb`, `redis`, `mysql`, `postgresql`, `database`, `sql` | 数据库与存储 |
| `elasticsearch`, `rocketmq`, `kafka`, `rabbitmq`, `mq`, `search` | 搜索与中间件 |
| `docker`, `kubernetes`, `k8s`, `container`, `cicd` | 容器化与编排 |
| `prometheus`, `grafana`, `skywalking`, `monitoring`, `logging`, `tracing` | 可观测性与运维 |
| `ddd`, `architecture`, `design-pattern`, `distributed`, `microservice` | 架构与设计模式 |

如需添加新标签，请同步更新 `update_readme.py` 中的 `TAG_CATEGORY_MAP` 字典。

## 🤝 参与交流

- **提问/讨论**：通过 [Issues](https://github.com/MaxHuang26/Dev-Problem-Solving-Journal/issues) 提出疑问或分享见解。
- **补充案例**：欢迎提交 PR 补充类似问题的解决思路。
- **内容纠错**：发现文档错误或过时信息，请提交 Issue 或 PR 修正。

## ⚖️ 版权与许可

本仓库内容采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 协议共享。

- **允许**：分享、改编、非商业使用
- **要求**：署名、相同方式共享、非商业
- **禁止**：商业使用、移除署名

> ⚠️ **免责声明**：本仓库内容仅为个人经验总结，不构成任何技术建议或保证。使用相关方案前请自行评估风险。

## 📊 仓库统计

<!-- STATS_START -->
![Last Updated](https://img.shields.io/github/last-commit/MaxHuang26/Dev-Problem-Solving-Journal)
![Issues](https://img.shields.io/github/issues/MaxHuang26/Dev-Problem-Solving-Journal)
![Stars](https://img.shields.io/github/stars/MaxHuang26/Dev-Problem-Solving-Journal)
![License](https://img.shields.io/github/license/MaxHuang26/Dev-Problem-Solving-Journal)
<!-- STATS_END -->

---

> **维护者**：[Max Huang](https://github.com/MaxHuang26)
