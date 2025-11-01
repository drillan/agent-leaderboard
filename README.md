---
title: Multi-Agent Competition System
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Multi-Agent Competition System

複数のAIモデルでタスクを並列実行し、パフォーマンスを比較するシステム。

## デプロイメント

このプロジェクトは2つのプラットフォームにデプロイできます：

### 🤗 Hugging Face Spaces（NiceGUI版）

- **URL**: https://huggingface.co/spaces/YOUR_USERNAME/agent-leaderboard
- **UI**: NiceGUI（リッチなPython UI）
- **構成**: `deployments/huggingface/`
- **RAM**: 16GB無料
- **適用**: AIデモ・プロトタイプ

**デプロイ方法**:
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/agent-leaderboard
git push hf main
```

詳細: [docs/deployment-hf.md](docs/deployment-hf.md)

### 🎨 Render（FastAPI + htmx版）

- **URL**: https://agent-leaderboard.onrender.com
- **UI**: FastAPI + Jinja2 + htmx
- **構成**: `deployments/render/`
- **RAM**: 512MB無料
- **適用**: プロダクション・長時間処理

**デプロイ方法**:
1. [Render Dashboard](https://dashboard.render.com/)にアクセス
2. "New Web Service" → GitHubリポジトリを接続
3. Root Directory: `deployments/render` を設定
4. 環境変数を設定
5. Deploy!

詳細: [docs/deployment-render.md](docs/deployment-render.md)

## 開発

### プロジェクト構造

```
agent-leaderboard/
├── shared/               # 共通コード
│   ├── src/             # ビジネスロジック
│   └── requirements-core.txt
├── deployments/
│   ├── huggingface/     # HF Spaces用
│   └── render/          # Render用
└── docs/                # ドキュメント
```

### ローカル実行

#### NiceGUI版

```bash
cd deployments/huggingface
docker build -t agent-leaderboard .
docker run -p 7860:7860 agent-leaderboard
```

#### FastAPI版

```bash
cd deployments/render
pip install -r ../../shared/requirements-core.txt
pip install -r requirements.txt
uvicorn main:app --reload
```

ブラウザで http://localhost:8000 を開く

### 開発フロー

```bash
# 1. 機能開発（共通コード）
cd shared/src/agents
# 新機能を実装

# 2. テスト
cd ../../..
pytest tests/

# 3. コミット
git add shared/
git commit -m "feat: Add new feature"

# 4. プッシュ（両方自動デプロイ）
git push origin main
```

## 技術スタック

- **Runtime**: Python 3.13+
- **AI Framework**: Pydantic AI
- **Hugging Face UI**: NiceGUI
- **Render UI**: FastAPI + htmx + Jinja2
- **Database**: DuckDB
- **Visualization**: Plotly

## ライセンス

MIT
