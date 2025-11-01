---
title: Multi-Agent Competition System
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_file: deployments/huggingface/main.py
pinned: false
license: mit
---

# Multi-Agent Competition System (Hugging Face Spaces)

NiceGUI版のマルチエージェント競技システム。

## 機能

- 複数AIモデルの並列実行
- リアルタイムリーダーボード
- パフォーマンスメトリクス可視化
- 実行履歴の閲覧

## 必要な環境変数

このSpaceを動作させるには、Settings → Repository secrets で以下を設定：

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY`（推奨）
- `HF_TOKEN`（推奨）

## ローカル実行

```bash
cd deployments/huggingface
docker build -t agent-leaderboard .
docker run -p 7860:7860 agent-leaderboard
```
