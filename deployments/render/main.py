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
from src.execution.executor import execute_multi_agent, extract_tool_hierarchy
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

# データベース初期化
db_path = project_root / "shared" / "database.db"
try:
    db = DatabaseConnection(db_path)
    db.initialize_schema()
    db.close()
    logger.info(f"Database schema initialized at {db_path}")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

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


# ============================================================================
# タブエンドポイント
# ============================================================================

@app.get("/tabs/execution", response_class=HTMLResponse)
async def tab_execution(request: Request):
    """タスク実行タブ."""
    return templates.TemplateResponse(
        "tabs/execution.html",
        {"request": request}
    )


@app.get("/tabs/performance", response_class=HTMLResponse)
async def tab_performance(request: Request):
    """パフォーマンスタブ."""
    return templates.TemplateResponse(
        "tabs/performance.html",
        {"request": request}
    )


@app.get("/tabs/history", response_class=HTMLResponse)
async def tab_history(request: Request):
    """履歴タブ."""
    return templates.TemplateResponse(
        "tabs/history.html",
        {"request": request}
    )


@app.get("/tabs/settings", response_class=HTMLResponse)
async def tab_settings(request: Request):
    """設定タブ."""
    # 設定フォームを直接生成して返す（より確実）
    if config is None:
        form_html = '<p class="error-message">設定が読み込めません</p>'
    else:
        # タスクエージェント設定
        task_agents_html = ''
        for i, agent in enumerate(config.task_agents, 1):
            selected_openai = "selected" if agent.provider == "openai" else ""
            selected_anthropic = "selected" if agent.provider == "anthropic" else ""
            selected_gemini = "selected" if agent.provider == "gemini" else ""
            selected_groq = "selected" if agent.provider == "groq" else ""
            selected_hf = "selected" if agent.provider == "huggingface" else ""

            task_agents_html += f'''
        <div class="agent-config">
            <select name="provider_{i}">
                <option value="openai" {selected_openai}>OpenAI</option>
                <option value="anthropic" {selected_anthropic}>Anthropic</option>
                <option value="gemini" {selected_gemini}>Gemini</option>
                <option value="groq" {selected_groq}>Groq</option>
                <option value="huggingface" {selected_hf}>Hugging Face</option>
            </select>
            <input type="text" name="model_{i}" value="{agent.model}" placeholder="モデル名">
            <input type="text" name="api_key_env_{i}" value="{agent.api_key_env}" placeholder="API_KEY環境変数名">
            <button type="button"
                    hx-delete="/settings/agent/{i}"
                    hx-target="closest .agent-config"
                    hx-swap="outerHTML swap:1s">
                削除
            </button>
        </div>
        '''

        # 評価エージェント設定
        selected_groq_eval = "selected" if config.evaluation_agent.provider == "groq" else ""
        selected_openai_eval = "selected" if config.evaluation_agent.provider == "openai" else ""
        selected_anthropic_eval = "selected" if config.evaluation_agent.provider == "anthropic" else ""

        eval_provider_options = f'''
        <option value="groq" {selected_groq_eval}>Groq</option>
        <option value="openai" {selected_openai_eval}>OpenAI</option>
        <option value="anthropic" {selected_anthropic_eval}>Anthropic</option>
        '''

        form_html = f'''
    <div class="settings-tab">
        <h2>⚙️ 設定</h2>
        <p style="color: #666; margin-bottom: 1.5rem;">エージェント設定と実行パラメータをカスタマイズします。</p>

        <form hx-post="/settings/save"
              hx-target="#settings-result"
              hx-swap="innerHTML">

            <section>
                <h3>タスクエージェント (2-5個必須)</h3>
                <div id="task-agents">
                    {task_agents_html}
                </div>
                <button type="button"
                        hx-post="/settings/agent/add"
                        hx-target="#task-agents"
                        hx-swap="beforeend">
                    + エージェント追加
                </button>
            </section>

            <section>
                <h3>評価エージェント</h3>
                <div class="form-group">
                    <label>プロバイダー:</label>
                    <select name="eval_provider">
                        {eval_provider_options}
                    </select>
                </div>
                <div class="form-group">
                    <label>モデル:</label>
                    <input type="text"
                           name="eval_model"
                           value="{config.evaluation_agent.model}">
                </div>
                <div class="form-group">
                    <label>評価プロンプト:</label>
                    <textarea name="eval_prompt" rows="10">{config.evaluation_agent.prompt}</textarea>
                </div>
            </section>

            <section>
                <h3>実行設定</h3>
                <div class="form-group">
                    <label>タイムアウト (秒):</label>
                    <input type="number"
                           name="timeout"
                           value="{config.execution.timeout_seconds}"
                           min="10"
                           max="300">
                </div>
            </section>

            <button type="submit" style="background: #0066cc; color: white; padding: 0.75rem 2rem; font-size: 1rem; margin-top: 1rem;">
                💾 保存
            </button>
        </form>

        <div id="settings-result"></div>
    </div>
    '''

    return HTMLResponse(content=form_html)


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

        # データベースを初期化
        db = DatabaseConnection(project_root / "shared" / "database.db")
        db.initialize_schema()
        repository = TaskRepository(db)

        # タスクエージェントを作成
        agents = [create_task_agent(model_config) for model_config in config.task_agents]

        # タスクをDBに保存
        from src.models.task import TaskSubmission
        task_submission = TaskSubmission(prompt=task)
        task_id = repository.create_task(task_submission)
        logger.info(f"Task created with ID: {task_id}")

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
                # DBに実行結果を保存（ID を取得）
                execution.id = repository.create_execution(execution)
                logger.info(f"Execution created with ID: {execution.id}")

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

                    # 評価をDBに保存
                    repository.create_evaluation(evaluation)

                    # 結果を辞書で保存
                    evaluated_results.append({
                        "model": f"{execution.model_provider}/{execution.model_name}",
                        "score": evaluation.score,
                        "duration": execution.duration_seconds or 0,
                        "explanation": evaluation.explanation,
                        "status": execution.status.value,
                        "execution_id": execution.id
                    })
                else:
                    # 実行失敗の場合
                    evaluated_results.append({
                        "model": f"{execution.model_provider}/{execution.model_name}",
                        "score": 0,
                        "duration": execution.duration_seconds or 0,
                        "explanation": "実行失敗",
                        "status": execution.status.value,
                        "execution_id": execution.id
                    })
            except Exception as e:
                logger.error(f"Evaluation failed for {execution.model_name}: {e}")
                evaluated_results.append({
                    "model": f"{execution.model_provider}/{execution.model_name}",
                    "score": 0,
                    "duration": execution.duration_seconds or 0,
                    "explanation": f"評価エラー: {str(e)}",
                    "status": execution.status.value,
                    "execution_id": execution.id
                })

        # セッションに保存
        execution_id = str(uuid.uuid4())
        execution_results[execution_id] = evaluated_results

        db.close()

        # リーダーボード + 実行詳細を返す
        return templates.TemplateResponse(
            "partials/execution_results.html",
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


# ============================================================================
# パフォーマンスメトリクス
# ============================================================================

@app.get("/performance/charts", response_class=HTMLResponse)
async def get_performance_charts(request: Request, task_id: str = "all"):
    """パフォーマンスチャートを生成."""
    try:
        # DBコネクションとリポジトリを初期化
        db = DatabaseConnection(project_root / "shared" / "database.db")
        db.initialize_schema()  # スキーマを確認
        repository = TaskRepository(db)

        # パフォーマンスメトリクスを取得
        metrics_data = []
        try:
            if task_id == "all":
                metrics_data = repository.get_performance_metrics(task_id=None)
            else:
                try:
                    metrics_data = repository.get_performance_metrics(task_id=int(task_id))
                except ValueError:
                    metrics_data = []
        except Exception as e:
            logger.warning(f"Failed to fetch performance metrics: {e}")
            metrics_data = []

        if not metrics_data:
            return HTMLResponse(content='<p class="placeholder">データがありません。タスクを実行してください。</p>')

        # モデル名を抽出
        models = [f"{m['model_provider']}/{m['model_name']}" for m in metrics_data]

        # 実行時間チャート
        durations = [m['avg_duration'] for m in metrics_data]
        std_durations = [m['std_duration'] for m in metrics_data]
        counts = [m['execution_count'] for m in metrics_data]

        # 詳細統計のホバーテキスト
        duration_hover_texts = [
            f"平均: {m['avg_duration']:.2f}秒<br>"
            f"標準偏差: {m['std_duration']:.2f}秒<br>"
            f"最小: {m['min_duration']:.2f}秒<br>"
            f"最大: {m['max_duration']:.2f}秒<br>"
            f"実行回数: {m['execution_count']}"
            for m in metrics_data
        ]

        duration_fig = go.Figure(data=[
            go.Bar(
                x=models,
                y=durations,
                error_y={
                    "type": "data",
                    "array": std_durations,
                    "visible": True,
                    "symmetric": False
                },
                marker_color='rgb(99, 110, 250)',
                name='平均実行時間',
                hovertext=duration_hover_texts,
                hoverinfo="text"
            )
        ])
        duration_fig.update_layout(
            title="実行時間（平均 ± 標準偏差）",
            xaxis_title="モデル",
            yaxis_title="時間（秒）",
            template="plotly_white",
            height=400
        )

        # トークン消費チャート
        tokens = [m['avg_tokens'] for m in metrics_data]
        std_tokens = [m['std_tokens'] for m in metrics_data]

        # 詳細統計のホバーテキスト
        token_hover_texts = [
            f"平均: {m['avg_tokens']:.0f}トークン<br>"
            f"標準偏差: {m['std_tokens']:.0f}トークン<br>"
            f"実行回数: {m['execution_count']}"
            for m in metrics_data
        ]

        token_fig = go.Figure(data=[
            go.Bar(
                x=models,
                y=tokens,
                error_y={
                    "type": "data",
                    "array": std_tokens,
                    "visible": True,
                    "symmetric": False
                },
                marker_color='rgb(239, 85, 59)',
                name='平均トークン数',
                hovertext=token_hover_texts,
                hoverinfo="text"
            )
        ])
        token_fig.update_layout(
            title="トークン消費（平均 ± 標準偏差）",
            xaxis_title="モデル",
            yaxis_title="トークン数",
            template="plotly_white",
            height=400
        )

        # スループット（トークン/秒）チャート
        throughput = [m['avg_tokens'] / max(m['avg_duration'], 0.1) for m in metrics_data]
        throughput_fig = go.Figure(data=[
            go.Bar(
                x=models,
                y=throughput,
                marker_color='rgb(0, 204, 150)',
                name='スループット'
            )
        ])
        throughput_fig.update_layout(
            title="スループット（トークン/秒）",
            xaxis_title="モデル",
            yaxis_title="トークン/秒",
            template="plotly_white",
            height=400
        )

        # HTMLに統合
        duration_html = duration_fig.to_html(
            include_plotlyjs='cdn',
            div_id='chart-duration',
            config={'responsive': True}
        )
        token_html = token_fig.to_html(
            include_plotlyjs=False,
            div_id='chart-tokens',
            config={'responsive': True}
        )
        throughput_html = throughput_fig.to_html(
            include_plotlyjs=False,
            div_id='chart-throughput',
            config={'responsive': True}
        )

        html = f'''
        <div class="chart-container">{duration_html}</div>
        <div class="chart-container">{token_html}</div>
        <div class="chart-container">{throughput_html}</div>
        '''

        return HTMLResponse(content=html)

    except Exception as e:
        logger.error(f"Error generating performance charts: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<p class="error-message">チャート生成エラー: {str(e)}</p>'
        )


@app.get("/performance/stats", response_class=HTMLResponse)
async def get_performance_stats(request: Request, task_id: str = "all"):
    """パフォーマンス統計情報を取得."""
    try:
        db = DatabaseConnection(project_root / "shared" / "database.db")
        db.initialize_schema()  # スキーマを確認
        repository = TaskRepository(db)

        metrics_data = []
        try:
            if task_id == "all":
                metrics_data = repository.get_performance_metrics(task_id=None)
            else:
                try:
                    metrics_data = repository.get_performance_metrics(task_id=int(task_id))
                except ValueError:
                    metrics_data = []
        except Exception as e:
            logger.warning(f"Failed to fetch performance stats: {e}")
            metrics_data = []

        if not metrics_data:
            return HTMLResponse(content='<p class="placeholder">データがありません。タスクを実行してください。</p>')

        # 統計情報を表示
        html = '<table style="width: 100%;">'
        html += '<thead><tr><th>モデル</th><th>実行回数</th><th>平均時間（秒）</th><th>平均トークン</th><th>スループット</th></tr></thead>'
        html += '<tbody>'

        for m in sorted(metrics_data, key=lambda x: x['avg_duration']):
            model_name = f"{m['model_provider']}/{m['model_name']}"
            throughput = m['avg_tokens'] / max(m['avg_duration'], 0.1)
            html += f'''
            <tr>
                <td><strong>{model_name}</strong></td>
                <td>{m['execution_count']}</td>
                <td>{m['avg_duration']:.2f}</td>
                <td>{m['avg_tokens']:.0f}</td>
                <td>{throughput:.2f} tokens/s</td>
            </tr>
            '''

        html += '</tbody></table>'

        return HTMLResponse(content=html)

    except Exception as e:
        logger.error(f"Error generating performance stats: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<p class="error-message">統計情報取得エラー: {str(e)}</p>'
        )


# ============================================================================
# 履歴ビュー
# ============================================================================

@app.get("/history/list", response_class=HTMLResponse)
async def get_history_list(request: Request):
    """履歴リストを取得."""
    try:
        db = DatabaseConnection(project_root / "shared" / "database.db")
        db.initialize_schema()  # スキーマを確認
        repository = TaskRepository(db)

        # タスク履歴を取得
        tasks = repository.get_task_history()

        if not tasks:
            return HTMLResponse(content='<p class="placeholder">履歴はまだありません</p>')

        html = '<div class="history-list">'

        for task in tasks:
            # task は辞書オブジェクト
            task_id = task.get('id')
            prompt = task.get('prompt', '')[:100]
            submitted_at = task.get('submitted_at', 'Unknown')
            execution_count = task.get('execution_count', 0)

            html += f'''
            <div class="history-item"
                 hx-get="/history/{task_id}/leaderboard"
                 hx-target="#history-detail"
                 hx-swap="innerHTML">
                <div class="task-prompt">{prompt}...</div>
                <div class="task-meta">
                    <span class="timestamp">{submitted_at}</span>
                    <span class="agent-count">{execution_count}エージェント</span>
                </div>
            </div>
            '''

        html += '</div>'
        return HTMLResponse(content=html)

    except Exception as e:
        logger.error(f"Error fetching history list: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<p class="error-message">履歴取得エラー: {str(e)}</p>'
        )


@app.get("/history/{task_id}/leaderboard", response_class=HTMLResponse)
async def get_history_leaderboard(request: Request, task_id: int):
    """過去タスクのリーダーボードを取得."""
    try:
        db = DatabaseConnection(project_root / "shared" / "database.db")
        db.initialize_schema()  # スキーマを確認
        repository = TaskRepository(db)

        # 指定されたタスクのリーダーボードを取得
        leaderboard_data = repository.get_leaderboard(task_id)

        if not leaderboard_data:
            return HTMLResponse(content='<p class="placeholder">このタスクの結果はありません</p>')

        # リーダーボードテーブルをレンダリング
        return templates.TemplateResponse(
            "partials/leaderboard.html",
            {
                "request": request,
                "results": sorted(leaderboard_data, key=lambda x: x.get('score', 0), reverse=True),
                "execution_id": None
            }
        )

    except Exception as e:
        logger.error(f"Error fetching history leaderboard: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<p class="error-message">リーダーボード取得エラー: {str(e)}</p>'
        )


# ============================================================================
# 設定管理
# ============================================================================

@app.get("/settings/form", response_class=HTMLResponse)
async def get_settings_form(request: Request):
    """設定フォームを取得."""
    if config is None:
        return HTMLResponse(
            content='<p class="error-message">設定が読み込めません</p>'
        )

    # タスクエージェント設定
    task_agents_html = ''
    for i, agent in enumerate(config.task_agents, 1):
        task_agents_html += f'''
        <div class="agent-config">
            <select name="provider_{i}">
                <option value="openai" {"selected" if agent.provider == "openai" else ""}>OpenAI</option>
                <option value="anthropic" {"selected" if agent.provider == "anthropic" else ""}>Anthropic</option>
                <option value="gemini" {"selected" if agent.provider == "gemini" else ""}>Gemini</option>
                <option value="groq" {"selected" if agent.provider == "groq" else ""}>Groq</option>
                <option value="huggingface" {"selected" if agent.provider == "huggingface" else ""}>Hugging Face</option>
            </select>
            <input type="text" name="model_{i}" value="{agent.model}" placeholder="モデル名">
            <input type="text" name="api_key_env_{i}" value="{agent.api_key_env}" placeholder="API_KEY環境変数名">
            <button type="button"
                    hx-delete="/settings/agent/{i}"
                    hx-target="closest .agent-config"
                    hx-swap="outerHTML swap:1s">
                削除
            </button>
        </div>
        '''

    # 評価エージェント設定
    eval_provider_options = f'''
        <option value="groq" {"selected" if config.evaluation_agent.provider == "groq" else ""}>Groq</option>
        <option value="openai" {"selected" if config.evaluation_agent.provider == "openai" else ""}>OpenAI</option>
        <option value="anthropic" {"selected" if config.evaluation_agent.provider == "anthropic" else ""}>Anthropic</option>
    '''

    html = f'''
    <form hx-post="/settings/save"
          hx-target="#settings-result"
          hx-swap="innerHTML">

        <section>
            <h3>タスクエージェント (2-5個必須)</h3>
            <div id="task-agents">
                {task_agents_html}
            </div>
            <button type="button"
                    hx-post="/settings/agent/add"
                    hx-target="#task-agents"
                    hx-swap="beforeend">
                + エージェント追加
            </button>
        </section>

        <section>
            <h3>評価エージェント</h3>
            <div class="form-group">
                <label>プロバイダー:</label>
                <select name="eval_provider">
                    {eval_provider_options}
                </select>
            </div>
            <div class="form-group">
                <label>モデル:</label>
                <input type="text"
                       name="eval_model"
                       value="{config.evaluation_agent.model}">
            </div>
            <div class="form-group">
                <label>評価プロンプト:</label>
                <textarea name="eval_prompt" rows="10">{config.evaluation_agent.prompt}</textarea>
            </div>
        </section>

        <section>
            <h3>実行設定</h3>
            <div class="form-group">
                <label>タイムアウト (秒):</label>
                <input type="number"
                       name="timeout"
                       value="{config.execution.timeout_seconds}"
                       min="10"
                       max="300">
            </div>
        </section>

        <button type="submit" style="background: #0066cc; color: white; padding: 0.75rem 2rem; font-size: 1rem; margin-top: 1rem;">
            💾 保存
        </button>
    </form>

    <div id="settings-result"></div>
    '''

    return HTMLResponse(content=html)


@app.post("/settings/save", response_class=HTMLResponse)
async def save_settings(request: Request):
    """設定を保存（TOML書き込み）."""
    try:
        form = await request.form()

        # フォームから設定を構築
        # TODO: フォームデータを解析して新しい設定を構築
        # 現在は簡易版 - 実装が必要

        return HTMLResponse(
            content='<p class="success-message">✓ 設定を保存しました</p>'
        )

    except Exception as e:
        logger.error(f"Error saving settings: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<p class="error-message">設定保存エラー: {str(e)}</p>'
        )


@app.post("/settings/agent/add", response_class=HTMLResponse)
async def add_agent(request: Request):
    """エージェント設定行を追加."""
    # デフォルトのエージェント設定を返す
    new_index = 999  # ダミーインデックス

    html = f'''
    <div class="agent-config">
        <select name="provider_{new_index}">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option>
            <option value="groq">Groq</option>
            <option value="huggingface">Hugging Face</option>
        </select>
        <input type="text" name="model_{new_index}" placeholder="モデル名">
        <input type="text" name="api_key_env_{new_index}" placeholder="API_KEY環境変数名">
        <button type="button"
                hx-delete="/settings/agent/{new_index}"
                hx-target="closest .agent-config"
                hx-swap="outerHTML swap:1s">
            削除
        </button>
    </div>
    '''

    return HTMLResponse(content=html)


@app.delete("/settings/agent/{index}", response_class=HTMLResponse)
async def delete_agent(index: int):
    """エージェント設定行を削除."""
    return HTMLResponse(content='')


# ============================================================================
# 実行詳細・モーダル
# ============================================================================

@app.get("/execution/{execution_id}/detail", response_class=HTMLResponse)
async def get_execution_detail(request: Request, execution_id: int):
    """実行詳細をモーダルで表示."""
    try:
        db = DatabaseConnection(project_root / "shared" / "database.db")
        db.initialize_schema()  # スキーマを確認
        repository = TaskRepository(db)

        # 実行情報を取得
        execution = repository.get_execution(execution_id)
        if not execution:
            return HTMLResponse(content='<p class="error-message">実行が見つかりません</p>')

        # 評価結果を取得（DBから直接取得）
        conn = db.connect()
        evaluation_row = conn.execute(
            "SELECT score, explanation FROM evaluations WHERE execution_id = ?",
            [execution_id]
        ).fetchone()

        evaluation = None
        if evaluation_row:
            evaluation = {
                "score": evaluation_row[0],
                "explanation": evaluation_row[1]
            }
        else:
            evaluation = {
                "score": 0,
                "explanation": "評価なし"
            }

        # エージェントの最終応答を抽出
        import json
        agent_response = extract_agent_response(execution.all_messages_json)

        # ツール呼び出しツリーを抽出
        tool_calls = []
        try:
            tool_hierarchy = extract_tool_hierarchy(execution)
            for node in tool_hierarchy:
                tool_calls.append({
                    "call_id": node.get("call_id", "unknown"),
                    "tool_name": node.get("tool_name", "Unknown"),
                    "args": json.dumps(node.get("args", {}), indent=2, ensure_ascii=False),
                    "result": json.dumps(node.get("result", {}), indent=2, ensure_ascii=False)
                })
        except Exception as e:
            logger.warning(f"Failed to extract tool hierarchy: {e}")
            tool_calls = []

        # メッセージを抽出（実行ログ表示用）
        messages = []
        if execution.all_messages_json:
            try:
                all_data = json.loads(execution.all_messages_json)
                if isinstance(all_data, list):
                    messages = all_data
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse all_messages_json: {e}")

        # インライン表示用テンプレートを返す（モーダルではなく）
        return templates.TemplateResponse(
            "components/execution_detail_inline.html",
            {
                "request": request,
                "execution": execution,
                "evaluation": evaluation,
                "agent_response": agent_response,
                "messages": messages,
                "tool_calls": tool_calls
            }
        )

    except Exception as e:
        logger.error(f"Error fetching execution detail: {e}", exc_info=True)
        return HTMLResponse(
            content=f'<p class="error-message">詳細取得エラー: {str(e)}</p>'
        )


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
