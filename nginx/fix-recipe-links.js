// fix-recipe-links.js
(function() {
    'use strict';
    
    function showRecipeLink(recipeId) {
        fetch(`/api/recipes/${recipeId}/get-link/`)
            .then(response => response.json())
            .then(data => {
                const link = data.direct_link || data.link || data.url;
                showModal(link);
            })
            .catch(error => {
                console.error('Ошибка получения ссылки:', error);
                alert('Не удалось получить ссылку на рецепт');
            });
    }
    
    function showModal(link) {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 400px;
            width: 90%;
            font-family: Arial, sans-serif;
        `;
        
        modal.innerHTML = `
            <h3 style="margin: 0 0 15px 0; color: #333; font-size: 18px;">🔗 Прямая ссылка на рецепт</h3>
            <input type="text" 
                   value="${link}" 
                   id="recipeLinkInput" 
                   style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 15px; font-size: 14px;"
                   readonly>
            <div style="display: flex; gap: 10px;">
                <button onclick="copyRecipeLink()" style="flex: 1; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                    📋 Копировать
                </button>
                <button onclick="closeRecipeModal()" style="flex: 1; padding: 10px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                    ❌ Закрыть
                </button>
            </div>
        `;
        
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 9999;
        `;
        overlay.onclick = closeRecipeModal;
        
        document.body.appendChild(overlay);
        document.body.appendChild(modal);
        
        document.getElementById('recipeLinkInput').select();
    }
    
    window.copyRecipeLink = function() {
        const input = document.getElementById('recipeLinkInput');
        input.select();
        document.execCommand('copy');
        
        // Показываем уведомление о копировании
        const notice = document.createElement('div');
        notice.textContent = '✅ Ссылка скопирована!';
        notice.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            z-index: 10001;
        `;
        document.body.appendChild(notice);
        setTimeout(() => notice.remove(), 2000);
    };
    
    window.closeRecipeModal = function() {
        const modal = document.querySelector('div[style*="z-index: 10000"]');
        const overlay = document.querySelector('div[style*="z-index: 9999"]');
        if (modal) modal.remove();
        if (overlay) overlay.remove();
    };
    
    // Ждем загрузки страницы
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        // Ждем немного чтобы React успел отрендерить кнопки
        setTimeout(() => {
            const buttons = document.querySelectorAll('button');
            if (buttons.length > 0) {
                const firstButton = buttons[0];
                const originalHandler = firstButton.onclick;
                
                firstButton.onclick = function(e) {
                    const pathParts = window.location.pathname.split('/').filter(Boolean);
                    const recipeId = pathParts[1] || pathParts[0];
                    
                    if (recipeId && !isNaN(recipeId)) {
                        showRecipeLink(recipeId);
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }
                    
                    if (originalHandler) {
                        return originalHandler.call(this, e);
                    }
                };
                
                console.log('✅ Recipe links fix applied!');
            }
        }, 1000);
    }
})();
