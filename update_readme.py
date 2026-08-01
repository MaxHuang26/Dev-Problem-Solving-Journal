#!/usr/bin/env python3
"""
update_readme.py - 自动扫描仓库中的案例 md 文件并更新 README.md

功能：
  1. 扫描 20XX/ 目录下的所有 .md 文件（排除 .gitkeep 等非案例文件）
  2. 提取每个案例文件的标签（## 🏷️ 标签 / ## 标签 部分）
  3. 按技术领域分类统计案例数量与最近更新时间
  4. 按年份统计案例数量
  5. 自动更新 README.md 中标记区域的内容

用法：
  python update_readme.py

标记区域说明：
  README.md 中使用 HTML 注释标记自动更新区域：
    <!-- TABLE_START --> ... <!-- TABLE_END -->      → 技术领域分类表格
    <!-- TIMELINE_START --> ... <!-- TIMELINE_END --> → 时间线归档列表
  脚本仅替换标记之间的内容，其余部分保持不变。

扩展标签映射：
  如需添加新的技术标签，请修改本文件中的 TAG_CATEGORY_MAP 字典，
  同时建议更新 README.md 中的"标签分类映射"表格以保持文档同步。
"""

import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ============================================================
# 配置：标签 → 技术领域映射
# 新增标签时在此添加映射即可，脚本会自动归类统计
# ============================================================
TAG_CATEGORY_MAP: dict[str, str] = {
    # Java 核心与框架
    'java':           'Java 核心与框架',
    'spring':         'Java 核心与框架',
    'spring-boot':    'Java 核心与框架',
    'spring-cloud':   'Java 核心与框架',
    'jdk':            'Java 核心与框架',
    'jvm':            'Java 核心与框架',
    'jpms':           'Java 核心与框架',
    'mybatis':        'Java 核心与框架',
    'hibernate':      'Java 核心与框架',
    'jpa':            'Java 核心与框架',
    'maven':          'Java 核心与框架',
    'gradle':         'Java 核心与框架',
    # 数据库与存储
    'tidb':           '数据库与存储',
    'mongodb':        '数据库与存储',
    'redis':          '数据库与存储',
    'mysql':          '数据库与存储',
    'postgresql':     '数据库与存储',
    'database':       '数据库与存储',
    'sql':            '数据库与存储',
    'sharding':       '数据库与存储',
    'mycat':          '数据库与存储',
    # 搜索与中间件
    'elasticsearch':  '搜索与中间件',
    'rocketmq':       '搜索与中间件',
    'kafka':          '搜索与中间件',
    'rabbitmq':       '搜索与中间件',
    'mq':             '搜索与中间件',
    'search':         '搜索与中间件',
    'canal':          '搜索与中间件',
    # 容器化与编排
    'docker':         '容器化与编排',
    'kubernetes':     '容器化与编排',
    'k8s':            '容器化与编排',
    'container':      '容器化与编排',
    'cicd':           '容器化与编排',
    'helm':           '容器化与编排',
    'jenkins':        '容器化与编排',
    # 可观测性与运维
    'prometheus':     '可观测性与运维',
    'grafana':        '可观测性与运维',
    'skywalking':     '可观测性与运维',
    'monitoring':     '可观测性与运维',
    'logging':        '可观测性与运维',
    'tracing':        '可观测性与运维',
    'alertmanager':   '可观测性与运维',
    # 架构与设计模式
    'ddd':            '架构与设计模式',
    'architecture':   '架构与设计模式',
    'design-pattern': '架构与设计模式',
    'distributed':    '架构与设计模式',
    'microservice':   '架构与设计模式',
    'concurrency':    '架构与设计模式',
}

# 技术领域显示顺序（保证表格顺序一致）
CATEGORY_ORDER: list[str] = [
    'Java 核心与框架',
    '数据库与存储',
    '搜索与中间件',
    '容器化与编排',
    '可观测性与运维',
    '架构与设计模式',
]

# 技术领域对应的核心技术栈描述（表格第二列）
CATEGORY_STACK: dict[str, str] = {
    'Java 核心与框架':   'JDK 17/21, Spring Boot, Spring Cloud',
    '数据库与存储':      'TiDB, MongoDB, Redis',
    '搜索与中间件':      'Elasticsearch, RocketMQ/Kafka',
    '容器化与编排':      'Docker, Kubernetes',
    '可观测性与运维':    'Prometheus, Grafana, SkyWalking',
    '架构与设计模式':    '分布式架构, DDD, 设计模式',
}

# README 文件名
README_FILENAME = 'README.md'


# ============================================================
# 扫描逻辑
# ============================================================

def find_year_dirs(root: Path) -> list[Path]:
    """查找仓库根目录下所有年份目录（匹配 20XX 格式），按年份升序排列。"""
    year_dirs: list[Path] = []
    for item in sorted(root.iterdir()):
        if item.is_dir() and re.match(r'^20\d{2}$', item.name):
            year_dirs.append(item)
    return year_dirs


def extract_tags(filepath: Path) -> list[str]:
    """
    从案例 md 文件中提取标签列表。

    匹配模式：
      ## 🏷️ 标签
      #java #k8s #performance

      ## 标签
      #java #k8s

    支持有无 emoji、有无空格、有无换行的写法。
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        print(f'⚠️  无法读取文件: {filepath}')
        return []

    # 匹配 "## 🏷️ 标签" 或 "## 标签" 段落（直到下一个 ## 标题或文件末尾）
    match = re.search(
        r'##\s*(?:🏷️\s*)?标签\s*\n+(.*?)(?=\n##|\n---|\Z)',
        content,
        re.DOTALL,
    )
    if not match:
        # 兼容英文标题 "## Tags"
        match = re.search(
            r'##\s*Tags?\s*\n+(.*?)(?=\n##|\n---|\Z)',
            content,
            re.DOTALL,
        )
    if not match:
        return []

    tags_text = match.group(1)
    # 提取 #tag-name 格式的标签（支持字母开头，中间可含 . _ -）
    return re.findall(r'#([a-zA-Z][a-zA-Z0-9._-]*)', tags_text)


def classify_categories(tags: list[str]) -> set[str]:
    """根据标签将案例归类到一个或多个技术领域。返回匹配到的领域名称集合。"""
    categories: set[str] = set()
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in TAG_CATEGORY_MAP:
            categories.add(TAG_CATEGORY_MAP[tag_lower])
    return categories


def scan_cases(root: Path) -> dict:
    """
    扫描所有年份目录中的案例文件。

    返回结构:
      {
          'category_stats': { category_name: {'count': int, 'latest': datetime|None} },
          'year_stats':      { year_str: int },
          'total':           int,
          'unknown_tags':    set[str],
      }
    """
    category_stats: dict = defaultdict(lambda: {'count': 0, 'latest': None})
    year_stats: dict[str, int] = defaultdict(int)
    total = 0
    all_unknown_tags: set[str] = set()

    for year_dir in find_year_dirs(root):
        year = year_dir.name
        md_files = [
            f for f in year_dir.glob('*.md')
            if f.name != README_FILENAME
        ]

        for md_file in sorted(md_files):
            tags = extract_tags(md_file)
            categories = classify_categories(tags)
            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)

            # 收集未映射的标签
            for tag in tags:
                if tag.lower() not in TAG_CATEGORY_MAP:
                    all_unknown_tags.add(tag)

            # 无任何已映射标签时，归入"其他"以确保总数一致
            if not categories:
                categories = {'其他'}

            for cat in categories:
                cat_data = category_stats[cat]
                cat_data['count'] += 1
                if cat_data['latest'] is None or mtime > cat_data['latest']:
                    cat_data['latest'] = mtime

            year_stats[year] += 1
            total += 1

    return {
        'category_stats': dict(category_stats),
        'year_stats':      dict(year_stats),
        'total':           total,
        'unknown_tags':    all_unknown_tags,
    }


# ============================================================
# 格式化与生成
# ============================================================

def format_date(dt: datetime | None) -> str:
    """格式化日期为 'YYYY-MM-DD'，无日期时返回 '-'。"""
    if dt is None:
        return '-'
    return dt.strftime('%Y-%m-%d')


def build_table_rows(stats: dict) -> str:
    """根据统计数据生成技术领域表格的 Markdown 行。"""
    cat_stats: dict = stats['category_stats']
    rows: list[str] = []
    for cat in CATEGORY_ORDER:
        data = cat_stats.get(cat, {'count': 0, 'latest': None})
        count = data['count']
        latest = format_date(data['latest'])
        stack = CATEGORY_STACK.get(cat, '-')
        rows.append(f'| {cat} | {stack} | {count} | {latest} |')
    return '\n'.join(rows)


def build_timeline_items(stats: dict) -> str:
    """根据统计数据生成时间线归档列表。"""
    year_stats: dict = stats['year_stats']
    items: list[str] = []

    # 从当前年份往前列出已有目录的年份和仓库中已有的年份
    existing_years = {d.name for d in find_year_dirs(Path(__file__).resolve().parent)}
    all_years = sorted(existing_years, reverse=True)

    for year_str in all_years:
        count = year_stats.get(year_str, 0)
        items.append(f'- [{year_str} 年](./{year_str}/)（{count} 篇）')
    return '\n'.join(items)


# ============================================================
# README 更新
# ============================================================

def update_readme(root: Path, stats: dict) -> None:
    """更新 README.md 中由注释标记包围的自动生成区域。"""
    readme_path = root / README_FILENAME

    if not readme_path.exists():
        print(f'❌ 未找到 {README_FILENAME}')
        return

    content = readme_path.read_text(encoding='utf-8')

    # 1. 替换技术领域表格
    new_table = build_table_rows(stats)
    pattern_table = r'(<!-- TABLE_START -->\n).*?(\n[ \t]*<!-- TABLE_END -->)'
    if re.search(pattern_table, content, flags=re.DOTALL):
        content = re.sub(
            pattern_table,
            rf'\1{new_table}\2',
            content,
            flags=re.DOTALL,
        )
    else:
        print('⚠️  未找到 TABLE_START/TABLE_END 标记，跳过表格更新。')

    # 2. 替换时间线归档
    new_timeline = build_timeline_items(stats)
    pattern_timeline = r'(<!-- TIMELINE_START -->\n).*?(\n[ \t]*<!-- TIMELINE_END -->)'
    if re.search(pattern_timeline, content, flags=re.DOTALL):
        content = re.sub(
            pattern_timeline,
            rf'\1{new_timeline}\2',
            content,
            flags=re.DOTALL,
        )
    else:
        print('⚠️  未找到 TIMELINE_START/TIMELINE_END 标记，跳过时间线更新。')

    readme_path.write_text(content, encoding='utf-8')
    print(f'✅ {README_FILENAME} 已更新（共 {stats["total"]} 篇案例）')


# ============================================================
# 主入口
# ============================================================

def main() -> None:
    """主函数：扫描案例 → 打印统计 → 更新 README。"""
    root = Path(__file__).resolve().parent
    print(f'🔍 扫描目录: {root}\n')

    stats = scan_cases(root)

    # ---- 打印扫描结果 ----
    print('📊 统计结果：')
    print(f'   总案例数: {stats["total"]}\n')

    print('   按技术领域：')
    for cat in CATEGORY_ORDER:
        data = stats['category_stats'].get(cat, {'count': 0, 'latest': None})
        marker = '✨' if data['count'] > 0 else '  '
        print(f'   {marker} {cat}: {data["count"]} 篇（最近更新: {format_date(data["latest"])}）')

    # 统计"其他"分类
    other = stats['category_stats'].get('其他')
    if other and other['count'] > 0:
        print(f'     ⚠️  其他（未分类）: {other["count"]} 篇')

    print(f'\n   按年份：')
    if stats['year_stats']:
        for year in sorted(stats['year_stats']):
            count = stats['year_stats'][year]
            bar = '█' * min(count, 20)
            print(f'     {year}: {count:>3} 篇  {bar}')
    else:
        print('     （暂无案例文件）')

    # ---- 提示未映射标签 ----
    unknown = stats.get('unknown_tags', set())
    if unknown:
        print(f'\n⚠️  未映射的标签: {", ".join(sorted(unknown))}')
        print('   请在 update_readme.py 的 TAG_CATEGORY_MAP 中添加映射。')
        print('   同时建议更新 README.md 中的"标签分类映射"表格。')

    # ---- 更新 README ----
    print()
    update_readme(root, stats)


if __name__ == '__main__':
    main()
