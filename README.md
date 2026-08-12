# Cortis Weverse Monitor

监控 CORTIS 在 Weverse 上的动态，发现新帖子/直播时通过 **PushPlus** 推送到你的微信。

## 功能

- 📝 **成员帖子通知**：推送时显示发帖人（JAMES / SEONGHYEON / JUHOON / KEONHO / MARTIN）、内容摘要、时间、原帖链接
- 🔴 **直播通知**：Cortis 开播时推送直播间链接
- ⏱️ **每 5 分钟检测一次**（GitHub Actions 最小间隔）
- ☁️ **完全云端运行**：你的电脑不用开机

## 部署步骤

### 1. 获取 PushPlus Token

1. 打开 https://www.pushplus.plus/ 并用微信扫码登录
2. 登录后页面会显示你的 **token**（一长串字符），复制保存

### 2. 创建 GitHub 仓库并上传

```bash
# 在本地执行（此目录下）
git init
git add .
git commit -m "init: cortis weverse monitor"

# 在 GitHub 网页上创建一个新仓库（例如 cortis-weverse-monitor，不要勾选 README）
git remote add origin https://github.com/<你的用户名>/cortis-weverse-monitor.git
git push -u origin main
```

### 3. 配置 Secret（PushPlus Token）

在 GitHub 仓库页面：

1. 打开 **Settings → Secrets and variables → Actions**
2. 点击 **New repository secret**
3. Name 填：`PUSHPLUS_TOKEN`
4. Secret 填：第一步复制的 PushPlus token
5. 保存

### 4. 立即测试

1. 打开仓库的 **Actions** 标签页
2. 左侧点 **Cortis Weverse Monitor**
3. 点 **Run workflow** → 绿色的按钮
4. 等 1-2 分钟，你的微信应该收到测试结果（如果没新内容则静默）

### 5. 完成 🎉

之后每 5 分钟自动检测一次，有新帖/直播自动推微信。

## 文件说明

| 文件 | 作用 |
|---|---|
| `cortis_weverse_monitor.py` | 监测主脚本（检测 + PushPlus 推送） |
| `seen.json` | 已见帖子/直播 ID 记录（自动更新并提交回仓库） |
| `.github/workflows/cortis-monitor.yml` | GitHub Actions 定时任务（每 5 分钟） |

## 自定义

- **只关注某个成员**：编辑脚本 `main()`，过滤 `it["author"]`
- **改检测频率**：编辑 `.github/workflows/cortis-monitor.yml` 里的 `cron`（GitHub 限制最小 5 分钟）

## 免责声明

本项目为个人学习用途，使用 Weverse 公开的 SEO 页面数据，与官方无关。请遵守 Weverse 服务条款，合理使用。
