// 変動費タブの行追加機能
(function() {
    'use strict';

    function initAddRowButton() {
        const addRowBtn = document.getElementById('add-row-btn');
        const rowsContainer = document.getElementById('variable-expenses-rows');
        const cardsDataElement = document.getElementById('cards-data');
        
        if (!addRowBtn || !rowsContainer) {
            return;
        }

        // カードデータを取得
        let cardsData = [];
        if (cardsDataElement) {
            try {
                cardsData = JSON.parse(cardsDataElement.textContent);
            } catch (e) {
                console.error('Failed to parse cards data:', e);
            }
        }

        // 既存のイベントリスナーを削除（重複防止）
        const newAddRowBtn = addRowBtn.cloneNode(true);
        addRowBtn.parentNode.replaceChild(newAddRowBtn, addRowBtn);
        
        newAddRowBtn.addEventListener('click', function() {
            const rowCount = rowsContainer.querySelectorAll('.variable-expense-row').length;
            const newRow = document.createElement('div');
            newRow.className = 'variable-expense-row flex items-center space-x-3 p-3 bg-gray-50 rounded-lg';
            
            // カード選択のオプションを動的に生成
            let cardOptions = '<option value="">選択してください</option>';
            cardsData.forEach(card => {
                cardOptions += `<option value="${card.id}">${card.name}</option>`;
            });
            
            newRow.innerHTML = `
                <div class="flex-1">
                    <label class="block text-sm font-medium text-gray-700 mb-1">カード</label>
                    <select 
                        name="card_id_${rowCount}" 
                        required
                        class="w-full border border-gray-300 rounded-md px-3 py-2"
                    >
                        ${cardOptions}
                    </select>
                </div>
                <div class="flex-1">
                    <label class="block text-sm font-medium text-gray-700 mb-1">請求総額</label>
                    <input 
                        type="number" 
                        name="amount_${rowCount}" 
                        min="0"
                        required
                        class="w-full border border-gray-300 rounded-md px-3 py-2"
                    >
                </div>
                <div class="pt-6">
                    <button 
                        type="button" 
                        class="remove-row-btn text-red-600 hover:text-red-800 px-3 py-2"
                        onclick="this.closest('.variable-expense-row').remove()"
                    >
                        削除
                    </button>
                </div>
            `;
            rowsContainer.appendChild(newRow);
        });
    }

    // 初期化関数（即座に実行 + 遅延実行の両方に対応）
    function tryInit() {
        // 少し遅延させて、DOMが完全に更新されるのを待つ
        setTimeout(initAddRowButton, 10);
    }

    // DOMContentLoadedで初期化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', tryInit);
    } else {
        tryInit();
    }

    // HTMXのafterSwapイベントで再初期化
    // tab-contentが更新された場合もチェック
    document.body.addEventListener('htmx:afterSwap', function(event) {
        const target = event.detail.target;
        // variable-expenses-contentが直接更新された場合、またはtab-contentが更新されてvariable-expenses-contentが含まれる場合
        if (target.id === 'variable-expenses-content' || 
            (target.id === 'tab-content' && target.querySelector('#variable-expenses-content'))) {
            tryInit();
        }
    });
})();
