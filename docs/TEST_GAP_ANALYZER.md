# 测试缺口分析工具 (Test Gap Analyzer)

## 概述

测试缺口分析工具是一个自动化工具，用于识别和补充代码中缺少测试覆盖的区域。工具会分析最近的 Git 提交，识别出高风险的代码变更，然后自动生成测试框架。

## 功能特性

- 📊 **自动分析**: 分析最近的 Git 提交，找出缺少测试的代码变更
- 🎯 **风险分级**: 按风险级别（高/中/低）分类识别到的缺口
- 🔍 **智能检测**: 识别高风险模式，如 JSON 解析、正则表达式、SQL 操作、加密解密等
- 📝 **测试生成**: 自动生成完整的 pytest 测试文件框架
- ⚙️ **CI 集成**: 可以与 GitHub Actions 等 CI 工具集成
- 🔐 **安全优先**: 特别关注认证授权、加密解密等安全关键代码

## 安装

工具已包含在 AI Agent Repair Tool 项目中，无需额外安装依赖。

## 使用方法

### 命令行使用

```bash
# 基础用法 - 分析当前项目的最近 10 个提交
python -m test_gap_analyzer.analyze

# 分析指定数量的提交
python -m test_gap_analyzer.analyze --commits 20

# 分析特定项目目录
python -m test_gap_analyzer.analyze --project /path/to/project

# 分析并自动写入测试文件
python -m test_gap_analyzer.analyze --write

# 包含低风险缺口（默认只包含高/中风险）
python -m test_gap_analyzer.analyze --include-low-risk

# 发现高风险缺口时返回非零退出码（CI 集成用）
python -m test_gap_analyzer.analyze --fail-on-high-risk

# 指定测试文件目录
python -m test_gap_analyzer.analyze --test-dir tests
```

### 完整示例

```bash
# 分析最近 50 个提交，写入测试，并在发现高风险时失败
python -m test_gap_analyzer.analyze \
    --commits 50 \
    --write \
    --fail-on-high-risk
```

## 输出说明

工具运行后会输出以下内容：

1. **分析统计**: 处理的提交数、发现的缺囗数、生成的测试文件数
2. **风险缺口**: 按高/中/低分类列出发现的问题
3. **生成的测试**: 列出创建/修改的测试文件
4. **建议**: 根据分析结果给出的建议

## 检测的高风险模式

工具特别关注以下高风险模式：

### 安全相关
- `json.loads` / JSON 解析
- `eval()` 函数使用
- SQL 查询操作
- `encrypt` / `decrypt` 加密解密
- `authenticate` / `authorize` 认证授权
- `validate_token` / `verify_signature` 验证操作

### 数据处理
- 正则表达式操作
- `int()` / `float()` / `complex()` 类型转换
- `parse_csv` / `parse_xml` / `parse_yaml` 解析操作

### 并发/异步
- `async` 函数
- `Promise.all` / `asyncio.gather` 并发操作
- `lock` / `semaphore` 锁操作

### 条件和异常
- `if` / `else` 分支
- `try` / `except` 异常处理
- `raise` 抛出异常
- 循环操作 (`for` / `while`)

## 集成到 CI/CD

### GitHub Actions

在项目的 `.github/workflows/test.yml` 中已经配置了测试缺口分析：

```yaml
test-gap-analysis:
  name: Test Gap Analysis
  runs-on: ubuntu-latest
  if: github.event_name == 'pull_request'
  
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 20
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Run Test Gap Analyzer
      run: |
        python -m test_gap_analyzer.analyze --commits 10 --fail-on-high-risk
      continue-on-error: false
    
    - name: Upload analysis report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-gap-analysis-report
        path: tests/
```

### 其他 CI 系统

在任何支持 Python 的 CI 系统中，都可以添加以下步骤：

```bash
# 运行分析
python -m test_gap_analyzer.analyze --commits 20 --fail-on-high-risk
```

## 生成的测试文件

工具生成的测试文件包含：

- 完整的 pytest 测试类
- 详细的文档字符串，说明风险原因
- 原代码片段引用
- TODO 注释提示需要完善的测试逻辑
- 基本的测试框架

### 示例生成的测试

```python
"""
测试: core/security.py
自动生成的测试 - Test Gap Analyzer
"""
import pytest
import json
from unittest.mock import patch, Mock
import core.security


class TestSecurity:
    """security 模块的测试类"""
    
    def test_validate_token_L42(self):
        """
        [高风险] 认证授权 - 安全关键模块
        原代码位置: core/security.py:42
        
        原代码片段:
            def validate_token(token):
                ...
        """
        # TODO: 实现具体的测试逻辑
        # 这个函数包含高风险操作，需要仔细测试
        
        # 示例: 验证函数不抛出异常
        try:
            if validate_token in ...:
                # 准备测试数据
                test_input = None  # TODO: 替换为实际输入
                result = validate_token(test_input)  # TODO: 传递正确的参数
                assert result is not None
            else:
                pytest.skip("需要手动实现测试 - 特定代码行需要测试")
        except Exception as e:
            pass
            
        # 安全性验证
        # TODO: 添加边界条件测试
        # TODO: 添加无效输入测试
        # TODO: 添加安全边界检查
```

## 最佳实践

1. **定期运行**: 在每次 PR 时自动运行，及时发现问题
2. **结合代码审查**: 发现的缺口应作为代码审查的重点
3. **持续完善**: 生成的测试是框架，需要开发人员补充具体的测试逻辑
4. **风险分级**: 优先处理高风险缺口，再逐步完善中低风险
5. **团队协作**: 生成的测试文件可以作为团队协作的起点

## 配置选项

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--project` | `-p` | 项目根目录 | `.` |
| `--commits` | `-c` | 分析的提交数 | `10` |
| `--test-dir` | `-t` | 测试目录 | `tests` |
| `--write` | `-w` | 写入测试文件 | `False` |
| `--include-low-risk` | `-l` | 包含低风险缺口 | `False` |
| `--fail-on-high-risk` | | 高风险时失败 | `False` |

### 自定义风险模式

可以通过修改 `test_gap_analyzer/types.py` 中的 `HIGH_RISK_PATTERNS` 和 `MEDIUM_RISK_PATTERNS` 来添加自定义的风险检测模式。

## 注意事项

1. **Git 仓库要求**: 需要在 Git 仓库中运行，工具依赖 Git 历史分析
2. **测试文件命名**: 工具会按照 Python 约定生成 `test_*.py` 文件
3. **手动补充**: 自动生成的测试是框架，需要开发人员补充具体的测试逻辑
4. **冲突处理**: 如果测试文件已存在，工具会安全地追加新测试而不是覆盖
5. **性能**: 大量提交时分析可能较慢，建议合理设置 `--commits` 参数

## 故障排除

### 无法找到 Git 仓库

```
⚠️  警告: 不是 Git 仓库，无法分析提交历史
```

**解决**: 在项目根目录初始化 Git 或确保当前目录有 `.git` 文件夹。

### 没有找到提交

确保有至少一次提交历史：
```bash
git init
git add .
git commit -m "Initial commit"
```

### 生成的测试无法运行

这是正常的，因为自动生成的测试需要你填充：
1. 测试输入数据
2. 正确的函数调用参数
3. 具体的断言逻辑

## 贡献

欢迎通过 Issue 和 PR 来改进工具！

## 许可证

与 AI Agent Repair Tool 使用相同的许可证。
