/**
 * 固定費一覧の改定履歴の開閉。
 * htmxで本体が差し替わっても動くよう、documentへの委譲で処理する。
 */
(function () {
    'use strict';

    var COLLAPSED_MARK = '▸'; // ▸
    var EXPANDED_MARK = '▾';  // ▾

    /** 1項目分の履歴行を開閉する */
    function toggleOne(button) {
        var itemId = button.getAttribute('data-fixed-item-toggle');
        var row = document.getElementById('fixed-item-history-' + itemId);
        if (!row) {
            return;
        }
        var isHidden = row.classList.toggle('hidden');
        button.textContent = isHidden ? COLLAPSED_MARK : EXPANDED_MARK;
    }

    /** すべての履歴行をまとめて開閉する */
    function toggleAll(button) {
        var shouldExpand = button.getAttribute('data-expanded') !== 'true';

        document.querySelectorAll('[data-fixed-item-history]').forEach(function (row) {
            row.classList.toggle('hidden', !shouldExpand);
        });
        document.querySelectorAll('[data-fixed-item-toggle]').forEach(function (toggle) {
            toggle.textContent = shouldExpand ? EXPANDED_MARK : COLLAPSED_MARK;
        });

        button.setAttribute('data-expanded', shouldExpand ? 'true' : 'false');
        button.textContent = shouldExpand ? 'すべての履歴を隠す' : 'すべての履歴を表示';
    }

    document.addEventListener('click', function (event) {
        var toggleAllButton = event.target.closest('[data-fixed-items-toggle-all]');
        if (toggleAllButton) {
            toggleAll(toggleAllButton);
            return;
        }

        var toggleButton = event.target.closest('[data-fixed-item-toggle]');
        if (toggleButton) {
            toggleOne(toggleButton);
        }
    });
})();
