// 年次ダッシュボードの内訳列エクスパンド（変動費・生活費）
(function () {
    'use strict';

    const EXPAND_ALL_LABEL = 'すべての内訳を表示';
    const COLLAPSE_ALL_LABEL = 'すべての内訳を隠す';

    /**
     * 指定グループの内訳列を開閉する
     * @param {string} group 'variable' または 'living'
     * @param {boolean} expanded true で表示、false で非表示
     */
    function setGroupExpanded(group, expanded) {
        document
            .querySelectorAll('.col-detail.col-' + group)
            .forEach(function (cell) {
                cell.classList.toggle('hidden', !expanded);
            });

        document
            .querySelectorAll('.col-toggle[data-group="' + group + '"]')
            .forEach(function (button) {
                button.setAttribute('aria-expanded', String(expanded));
                const icon = button.querySelector('.expand-icon');
                if (icon) {
                    icon.textContent = expanded ? '▼' : '▶';
                }
            });
    }

    /**
     * 展開した内訳列が画面外にあると変化に気づけないため、横スクロールして見える位置に移動する
     * @param {string} group 'variable' または 'living'
     */
    function scrollGroupIntoView(group) {
        const cells = document.querySelectorAll('.col-detail.col-' + group + ':not(.hidden)');
        if (cells.length === 0) {
            return;
        }
        const last = cells[cells.length - 1];
        const container = last.closest('.overflow-x-auto');
        if (!container) {
            return;
        }
        const containerRect = container.getBoundingClientRect();
        const cellRect = last.getBoundingClientRect();
        const overflow = cellRect.right - containerRect.right;
        if (overflow > 0) {
            container.scrollBy({ left: overflow + 16, behavior: 'smooth' });
        }
    }

    /** 内訳列がすべて表示されているかどうか */
    function isAllExpanded() {
        const cells = document.querySelectorAll('.col-detail');
        if (cells.length === 0) {
            return false;
        }
        return Array.prototype.every.call(cells, function (cell) {
            return !cell.classList.contains('hidden');
        });
    }

    /** 一括表示ボタンのラベルを現在の状態に合わせる */
    function syncExpandAllLabel() {
        const button = document.getElementById('expand-all-button');
        if (button) {
            button.textContent = isAllExpanded() ? COLLAPSE_ALL_LABEL : EXPAND_ALL_LABEL;
        }
    }

    /** 画面上に存在する内訳グループ名の一覧を取得 */
    function allGroups() {
        const groups = [];
        document.querySelectorAll('.col-toggle[data-group]').forEach(function (button) {
            const group = button.getAttribute('data-group');
            if (groups.indexOf(group) === -1) {
                groups.push(group);
            }
        });
        return groups;
    }

    // htmxによる差し替え後も動くようにイベント委譲で処理する
    document.addEventListener('click', function (event) {
        const toggle = event.target.closest('.col-toggle');
        if (toggle) {
            const group = toggle.getAttribute('data-group');
            const expanded = toggle.getAttribute('aria-expanded') === 'true';
            setGroupExpanded(group, !expanded);
            if (!expanded) {
                scrollGroupIntoView(group);
            }
            syncExpandAllLabel();
            return;
        }

        const expandAll = event.target.closest('#expand-all-button');
        if (expandAll) {
            const expand = !isAllExpanded();
            const groups = allGroups();
            groups.forEach(function (group) {
                setGroupExpanded(group, expand);
            });
            if (expand && groups.length > 0) {
                scrollGroupIntoView(groups[groups.length - 1]);
            }
            syncExpandAllLabel();
        }
    });

    document.body.addEventListener('htmx:afterSwap', syncExpandAllLabel);
})();
