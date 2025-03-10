# 智能录屏回放系统

这是一个基于ffmpeg和Ollama的智能录屏回放系统，可以自动录制屏幕、提取关键帧，并使用AI模型分析内容。

## 功能特点

- 自动录制屏幕（每20秒一个片段）
- 自动提取视频关键帧
- 使用Ollama多模态模型分析关键帧内容
- 基于AI分析结果的智能搜索功能

## 系统要求

- Python 3.7+
- ffmpeg
- Ollama（本地运行）

## 安装步骤

1. 安装ffmpeg（如果尚未安装）：
   ```bash
   brew install ffmpeg  # macOS
   ```

2. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 确保Ollama已安装并运行：
   ```bash
   # 安装Ollama（如果尚未安装）
   curl https://ollama.ai/install.sh | sh
   
   # 启动Ollama服务
   ollama serve
   ```

4. 下载并运行minicpm-v模型：
   ```bash
   ollama pull minicpm-v
   ```

## 使用方法

1. 运行程序：
   ```bash
   python screen_recorder.py
   ```

2. 在程序菜单中选择：
   - 1: 开始录制（录制20秒）
   - 2: 搜索录制内容
   - 3: 退出程序

## 目录结构

- `recordings/`: 存储录制的视频文件
- `keyframes/`: 存储提取的关键帧图片
- `recording_metadata.json`: 存储录制元数据和AI分析结果

## 注意事项

- 确保系统已授予屏幕录制权限
- 确保Ollama服务正在运行
- 录制过程中请勿关闭程序 