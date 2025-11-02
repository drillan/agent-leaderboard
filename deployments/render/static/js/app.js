/**
 * Agent Leaderboard - カスタムJavaScript
 * htmx との連携とUI制御を担当
 */

/**
 * ページロード時の初期化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * アプリケーションの初期化
 */
function initializeApp() {
    // htmxイベントリスナーを登録
    setupHtmxListeners();

    // モーダル関連の機能を初期化
    setupModalHandlers();
}

/**
 * htmxイベントリスナーを設定
 */
function setupHtmxListeners() {
    // リクエスト完了時
    document.addEventListener('htmx:afterSwap', function(evt) {
        // スクロールを最上部に
        window.scrollTo(0, 0);

        // 実行タブの結果表示処理
        const resultsDiv = document.getElementById('results');
        if (evt.detail.target && evt.detail.target.id === 'results' && resultsDiv) {
            const statusDisplay = document.getElementById('status-display');
            if (statusDisplay) {
                statusDisplay.style.display = 'none';
                statusDisplay.classList.add('hidden');
            }
            resultsDiv.style.display = 'block';
            window.scrollTo(0, resultsDiv.offsetTop - 100);
        }
    });

    // フォーム送信前処理（実行タブ用）
    document.addEventListener('htmx:beforeRequest', function(evt) {
        const taskForm = document.querySelector('.task-form');
        if (evt.detail.xhr && evt.detail.xhr.currentTarget === taskForm) {
            const statusDisplay = document.getElementById('status-display');
            const resultsDiv = document.getElementById('results');
            const errorDisplay = document.getElementById('error-display');

            if (statusDisplay) {
                statusDisplay.style.display = 'block';
                statusDisplay.classList.remove('hidden');
            }
            if (resultsDiv) resultsDiv.style.display = 'none';
            if (errorDisplay) {
                errorDisplay.style.display = 'none';
                errorDisplay.innerHTML = '';
            }
        }
    });

    // エラーハンドリング
    document.addEventListener('htmx:responseError', function(evt) {
        console.error('htmx error:', evt.detail);
        const errorDisplay = document.getElementById('error-display');
        if (errorDisplay) {
            errorDisplay.style.display = 'block';
            const status = evt.detail.xhr?.status || 'Unknown';
            const response = evt.detail.xhr?.response || 'An error occurred';
            errorDisplay.innerHTML = `
                <div class="alert alert-error">
                    <strong>エラーが発生しました (HTTP ${status})</strong>
                    <p>${response}</p>
                </div>
            `;
        }
        showErrorNotification('リクエストに失敗しました');
    });

    // タイムアウトハンドリング
    document.addEventListener('htmx:timeout', function(evt) {
        console.error('htmx timeout:', evt.detail);
        const errorDisplay = document.getElementById('error-display');
        if (errorDisplay) {
            errorDisplay.style.display = 'block';
            errorDisplay.innerHTML = `
                <div class="alert alert-error">
                    <strong>リクエストがタイムアウトしました</strong>
                    <p>実行時間が長すぎます。別のタスクを試すか、しばらく待ってからもう一度お試しください。</p>
                </div>
            `;
        }
        showErrorNotification('リクエストがタイムアウトしました');
    });

    // パフォーマンスタブのタスクフィルター処理
    document.addEventListener('htmx:afterSwap', function(evt) {
        const taskFilter = document.getElementById('task-filter');
        if (taskFilter) {
            // 前のリスナーをクリア
            if (taskFilter.__changeHandler) {
                taskFilter.removeEventListener('change', taskFilter.__changeHandler);
            }

            // 新しいリスナーを登録
            taskFilter.__changeHandler = function() {
                const taskId = this.value;
                const chartsContainer = document.getElementById('charts-container');
                const statsContainer = document.getElementById('stats-container');

                if (chartsContainer) {
                    htmx.ajax('GET', `/performance/charts?task_id=${taskId}`, chartsContainer);
                }
                if (statsContainer) {
                    htmx.ajax('GET', `/performance/stats?task_id=${taskId}`, statsContainer);
                }
            };

            taskFilter.addEventListener('change', taskFilter.__changeHandler);
        }
    });
}

/**
 * モーダルハンドラーを設定
 */
function setupModalHandlers() {
    const modal = document.getElementById('modal');

    if (!modal) return;

    // モーダル外をクリックで閉じる
    modal.addEventListener('click', function(evt) {
        if (evt.target === modal) {
            closeModal();
        }
    });

    // キーボード（Escキー）で閉じる
    document.addEventListener('keydown', function(evt) {
        if (evt.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });
}

/**
 * モーダルを閉じる
 */
function closeModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * エラー通知を表示
 */
function showErrorNotification(message) {
    // 簡易版：コンソールに出力
    console.error(message);

    // TODO: Toast通知の実装
}

/**
 * 成功通知を表示
 */
function showSuccessNotification(message) {
    // 簡易版：コンソールに出力
    console.log(message);

    // TODO: Toast通知の実装
}

/**
 * タブをアクティブに設定
 */
function setActiveTab(element) {
    // すべてのタブから active クラスを削除
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    // クリックされたタブに active クラスを追加
    element.classList.add('active');
}

/**
 * ローディングアニメーションを表示
 */
function showLoading() {
    const loader = document.createElement('div');
    loader.className = 'loading';
    loader.id = 'page-loader';
    document.body.appendChild(loader);
}

/**
 * ローディングアニメーションを非表示
 */
function hideLoading() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.remove();
    }
}

/**
 * URLパラメータを取得
 */
function getUrlParam(param) {
    const params = new URLSearchParams(window.location.search);
    return params.get(param);
}

/**
 * URLパラメータを設定
 */
function setUrlParam(param, value) {
    const params = new URLSearchParams(window.location.search);
    params.set(param, value);
    window.history.replaceState({}, '', '?' + params.toString());
}
