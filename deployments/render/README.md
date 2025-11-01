# Multi-Agent Competition System - Render Deployment

FastAPI + htmx版のマルチエージェント競技システム。

## 機能

- Pythonフルスタック（FastAPI + Jinja2 + htmx）
- 長時間実行対応（最大100分）
- PostgreSQL統合可能
- プロダクション向け構成

## デプロイ方法

### 自動デプロイ（推奨）

1. [Render Dashboard](https://dashboard.render.com/) にログイン
2. "New Web Service" をクリック
3. GitHubリポジトリを接続
4. 以下を設定：
   - **Root Directory**: `deployments/render`
   - **Build Command**: render.yamlから自動検出
   - **Start Command**: render.yamlから自動検出
5. 環境変数を設定（OPENAI_API_KEY等）
6. "Create Web Service" をクリック

## ローカル実行

```bash
cd deployments/render
pip install -r ../../shared/requirements-core.txt
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

ブラウザで http://localhost:8000 を開く
