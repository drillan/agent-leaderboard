#!/usr/bin/env python3
"""Multi-Agent Competition System - FastAPI + htmx Interface (Render)."""

import sys
from pathlib import Path
from typing import Optional
import uuid
import logging

# 共通コードへのパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "shared"))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import plotly.graph_objects as go

# 共通コードをインポート
from src.config.loader import ConfigLoader
from src.agents.task_agent import create_task_agent
from src.agents.eval_agent import create_evaluation_agent
from src.execution.executor import execute_multi_agent
from src.execution.evaluator import evaluate_execution, extract_agent_response
from src.database.connection import DatabaseConnection
from src.database.repositories import TaskRepository

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Leaderboard",
    description="Multi-Agent Competition System",
    version="1.0.0"
)

# 静的ファイルとテンプレート
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# グローバル状態管理（セッション）
execution_results: dict[str, list] = {}

# 設定をロード
config_path = project_root / "shared" / "config.toml"
try:
    config = ConfigLoader.load(config_path)
    logger.info(f"Configuration loaded from {config_path}")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    config = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """メインページ."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Multi-Agent Competition System"}
    )


@app.post("/execute", response_class=HTMLResponse)
async def execute_task(request: Request, task: str = Form(...)):
    """
    タスク実行エンドポイント.

    htmxから呼ばれ、HTMLフラグメントを返す.
    """
    try:
        # Pydantic AIでエージェント実行
        if config is None:
            return HTMLResponse(
                content="<p style='color: red;'>設定ファイルが読み込めません</p>"
            )

        # タスクエージェントを作成
        agents = [create_task_agent(model_config) for model_config in config.task_agents]

        # タスクをDBに保存（簡易版：task_id=0）
        task_id = 0

        # エージェントを並列実行
        executions = await execute_multi_agent(
            agents=agents,
            model_configs=config.task_agents,
            prompt=task,
            task_id=task_id,
            timeout_seconds=config.execution.timeout_seconds
        )

        # 評価エージェントを作成
        eval_agent = create_evaluation_agent(config.evaluation_agent)

        # 各実行結果を評価
        evaluated_results = []
        for execution in executions:
            try:
                # メッセージから応答を抽出
                if execution.all_messages_json:
                    agent_response = extract_agent_response(execution.all_messages_json)

                    # 評価を実行
                    evaluation = await evaluate_execution(
                        execution=execution,
                        task_prompt=task,
                        agent_response=agent_response,
                        eval_agent=eval_agent,
                        timeout_seconds=30.0
                    )

                    # 結果を辞書で保存
                    evaluated_results.append({
                        "model": f"{execution.model_provider}/{execution.model_name}",
                        "score": evaluation.score,
                        "duration": execution.duration_seconds or 0,
                        "explanation": evaluation.explanation,
                        "status": execution.status.value
                    })
                else:
                    # 実行失敗の場合
                    evaluated_results.append({
                        "model": f"{execution.model_provider}/{execution.model_name}",
                        "score": 0,
                        "duration": execution.duration_seconds or 0,
                        "explanation": "実行失敗",
                        "status": execution.status.value
                    })
            except Exception as e:
                logger.error(f"Evaluation failed for {execution.model_name}: {e}")
                evaluated_results.append({
                    "model": f"{execution.model_provider}/{execution.model_name}",
                    "score": 0,
                    "duration": execution.duration_seconds or 0,
                    "explanation": f"評価エラー: {str(e)}",
                    "status": execution.status.value
                })

        # セッションに保存
        execution_id = str(uuid.uuid4())
        execution_results[execution_id] = evaluated_results

        # リーダーボードHTMLを返す
        return templates.TemplateResponse(
            "partials/leaderboard.html",
            {
                "request": request,
                "results": sorted(evaluated_results, key=lambda x: x["score"], reverse=True),
                "execution_id": execution_id
            }
        )
    except Exception as e:
        logger.error(f"Error executing task: {e}", exc_info=True)
        return HTMLResponse(
            content=f"<p style='color: red;'>エラーが発生しました: {str(e)}</p>"
        )


@app.get("/chart/{execution_id}", response_class=HTMLResponse)
async def get_chart(request: Request, execution_id: str):
    """Plotlyチャートを生成して返す."""
    results = execution_results.get(execution_id, [])

    if not results:
        return HTMLResponse(content="<p>結果が見つかりません</p>")

    # Plotlyチャート作成
    models = [r["model"] for r in results]
    scores = [r["score"] for r in results]

    fig = go.Figure(data=[
        go.Bar(
            x=models,
            y=scores,
            marker_color='rgb(55, 83, 109)'
        )
    ])

    fig.update_layout(
        title="Agent Performance",
        xaxis_title="Model",
        yaxis_title="Score",
        template="plotly_white",
        height=400
    )

    # HTMLとして返す
    chart_html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='chart',
        config={'responsive': True}
    )

    return HTMLResponse(content=chart_html)


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
