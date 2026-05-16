# 社区贡献安全与质量保障方案

## 一、贡献流程安全

```
提交 PR → 自动检查 → 人工审查 → 合并发布
    │          │           │
    ▼          ▼           ▼
 模板检查   安全扫描    代码审核
 格式检查   测试覆盖   维护者批准
```

## 二、强制要求

### 1. 必需项
- [ ] 新工具必须包含测试用例
- [ ] 配置文件必须有文档说明
- [ ] PR 必须描述修复/新增内容
- [ ] 必须签署 DCO (Developer Certificate of Origin)

### 2. 自动化检查
```yaml
# .github/CONTRIBUTING_CHECKLIST.md
## PR Checklist

### 代码质量
- [ ] 代码通过 `python -m py_compile` 编译检查
- [ ] 新函数有 docstring 文档
- [ ] 遵循 PEP 8 代码规范

### 测试要求
- [ ] 新功能有对应测试
- [ ] 测试覆盖率达到 80%+
- [ ] 所有测试通过 `python -m pytest`

### 安全检查
- [ ] 无硬编码密码/密钥
- [ ] 无可疑的系统调用
- [ ] 路径操作使用安全 API

### 文档更新
- [ ] README.md 已更新（如有必要）
- [ ] API 变更已记录
- [ ] 贡献者名单已更新
```

## 三、危险操作防控

### 1. 文件操作白名单
```python
# 只允许操作以下目录
ALLOWED_PATHS = [
    "~/.config/<tool-name>/",
    "~/.local/share/<tool-name>/",
    "<tool-install-dir>/config/",
]

# 禁止操作
BLOCKED_PATHS = [
    "~/.ssh/",
    "~/.aws/",
    "/etc/passwd",
    "C:\\Windows\\System32\\",  # Windows 系统目录
]
```

### 2. 命令执行限制
```python
# 只允许安全的配置文件操作
ALLOWED_COMMANDS = [
    "json.tool",      # JSON 格式化验证
    "shutil.copytree",  # 备份
    "shutil.rmtree",    # 清理（需确认）
]

# 禁止执行
BLOCKED_COMMANDS = [
    "subprocess.run",   # 禁止任意命令执行
    "eval",             # 禁止动态代码执行
    "exec",             # 禁止动态代码执行
]
```

### 3. 恶意模式检测
```python
MALICIOUS_PATTERNS = [
    # 编码混淆
    r"base64\.(b64decode|b64encode)",
    r"\\x[0-9a-f]{2}",
    
    # 网络请求（禁止在配置修复时）
    r"requests\.(get|post)",
    r"urllib\.request",
    
    # 系统操作
    r"os\.system",
    r"subprocess\.Popen",
    
    # 敏感文件访问
    r"open.*\.ssh",
    r"open.*\.aws",
]
```

## 四、审核清单

### 维护者审核要点

1. **代码审核**
   - [ ] 功能逻辑正确
   - [ ] 无安全漏洞
   - [ ] 代码可读性
   - [ ] 测试覆盖

2. **意图审核**
   - [ ] 贡献者意图明确
   - [ ] 非恶意代码
   - [ ] 符合项目方向

3. **法律审核**
   - [ ] 无许可证冲突
   - [ ] DCO 已签署
   - [ ] 无侵权代码

## 五、响应机制

### 发现恶意代码的处理流程

```
发现可疑代码
      │
      ▼
立即冻结该 PR
      │
      ▼
安全团队评估
      │
      ├─── 确认恶意 ───→ 永久封禁 + 公开声明
      │
      └─── 误报 ───→ 解除冻结 + 改进检测
```

## 六、社区激励

### 1. 贡献者等级
```
🥉 Level 1: 初次贡献 (1-5 PR)
🥈 Level 2: 活跃贡献者 (6-20 PR)
🥇 Level 3: 核心贡献者 (20+ PR)
🏆 Level 4: 维护者 (邀请加入团队)
```

### 2. 致谢方式
- README 贡献者名单
- Release Notes 特别鸣谢
- GitHub 贡献者徽章
- 年度贡献者证书

## 七、参考文档

- [GitHub 安全最佳实践](https://docs.github.com/en/code-security)
- [OpenSSF 安全记分卡](https://securityscorecards.dev/)
- [DCO 签署指南](https://developercertificate.org/)
- [Contributor Covenant 行为准则](https://www.contributor-covenant.org/)
