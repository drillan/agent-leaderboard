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
    });

    // エラーハンドリング
    document.addEventListener('htmx:responseError', function(evt) {
        console.error('htmx error:', evt.detail);
        showErrorNotification('リクエストに失敗しました');
    });

    // タイムアウトハンドリング
    document.addEventListener('htmx:timeout', function(evt) {
        console.error('htmx timeout:', evt.detail);
        showErrorNotification('リクエストがタイムアウトしました');
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
