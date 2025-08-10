// 新功能实现代码

document.addEventListener('DOMContentLoaded', function() {
    // 对话框功能
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const dialogueBox = document.querySelector('.dialogue-box');

    sendBtn.addEventListener('click', function() {
        if (messageInput.value.trim()) {
            const message = document.createElement('div');
            message.className = 'message sent';
            message.textContent = messageInput.value.trim();
            dialogueBox.insertBefore(message, messageInput);
            messageInput.value = '';

            // 模拟回复
            setTimeout(() => {
                const reply = document.createElement('div');
                reply.className = 'message received';
                const replies = ['૮⸝⸝ᴗ͈ ‸ ᴗ͈⸝⸝ა 好呀！', '(*ﾟ▽ﾟ*) 我知道了！', 'ᜊ๑•×•๑ᜊ 真有趣～', '꒰๑´•௰•`๑꒱ 太棒了！'];
                reply.textContent = replies[Math.floor(Math.random() * replies.length)];
                dialogueBox.insertBefore(reply, messageInput);
                dialogueBox.scrollTop = dialogueBox.scrollHeight;
            }, 500);

            dialogueBox.scrollTop = dialogueBox.scrollHeight;
        }
    });

    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendBtn.click();
        }
    });

    // 留言板功能
    const boardInput = document.getElementById('board-input');
    const boardBtn = document.getElementById('board-btn');
    const messageBoard = document.getElementById('message-board');

    // 加载本地存储的留言
    loadBoardMessages();

    boardBtn.addEventListener('click', function() {
        if (boardInput.value.trim()) {
            const message = document.createElement('div');
            message.className = 'board-message';
            message.textContent = boardInput.value.trim() + ' (ˊo̴̶̷̤  ̫ o̴̶̷̤ˋ)';
            messageBoard.prepend(message);
            boardInput.value = '';

            // 保存到本地存储
            saveBoardMessages();
        }
    });

    boardInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            boardBtn.click();
        }
    });

    function saveBoardMessages() {
        const messages = Array.from(document.querySelectorAll('.board-message'))
            .map(el => el.textContent);
        localStorage.setItem('boardMessages', JSON.stringify(messages));
    }

    function loadBoardMessages() {
        const messages = JSON.parse(localStorage.getItem('boardMessages') || '[]');
        messages.forEach(text => {
            const message = document.createElement('div');
            message.className = 'board-message';
            message.textContent = text;
            messageBoard.prepend(message);
        });
    }

    // 每日待办功能
    const todoInput = document.getElementById('todo-input');
    const todoBtn = document.getElementById('todo-btn');
    const todoList = document.getElementById('todo-list');

    // 加载本地存储的待办
    loadTodos();

    todoBtn.addEventListener('click', function() {
        if (todoInput.value.trim()) {
            addTodo(todoInput.value.trim());
            todoInput.value = '';
            saveTodos();
        }
    });

    todoInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            todoBtn.click();
        }
    });

    function addTodo(text) {
        const li = document.createElement('li');
        li.className = 'todo-item';
        li.innerHTML = `
            <input type="checkbox" class="todo-checkbox">
            <span>${text}</span>
            <button class="todo-delete">×</button>
        `;
        todoList.appendChild(li);

        // 添加事件监听
        li.querySelector('.todo-checkbox').addEventListener('change', function() {
            li.classList.toggle('completed');
            saveTodos();
        });

        li.querySelector('.todo-delete').addEventListener('click', function() {
            li.remove();
            saveTodos();
        });
    }

    function saveTodos() {
        const todos = [];
        document.querySelectorAll('.todo-item').forEach(item => {
            todos.push({
                text: item.querySelector('span').textContent,
                completed: item.classList.contains('completed')
            });
        });
        localStorage.setItem('todos', JSON.stringify(todos));
    }

    function loadTodos() {
        const todos = JSON.parse(localStorage.getItem('todos') || '[]');
        todos.forEach(todo => {
            addTodo(todo.text);
            if (todo.completed) {
                const items = document.querySelectorAll('.todo-item');
                items[items.length - 1].classList.add('completed');
                items[items.length - 1].querySelector('.todo-checkbox').checked = true;
            }
        });
    }

    // 心情打卡功能
    const moodBtns = document.querySelectorAll('.mood-btn');
    const moodHistory = document.getElementById('mood-history');

    // 加载心情历史
    loadMoodHistory();

    moodBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const mood = this.getAttribute('data-mood');
            const emoji = this.textContent;
            const date = new Date().toLocaleString();

            const entry = document.createElement('div');
            entry.className = 'mood-entry';
            entry.textContent = `${date}: ${mood} ${emoji}`;
            moodHistory.prepend(entry);

            // 保存到本地存储
            saveMoodHistory();
        });
    });

    function saveMoodHistory() {
        const entries = Array.from(document.querySelectorAll('.mood-entry'))
            .map(el => el.textContent);
        localStorage.setItem('moodHistory', JSON.stringify(entries));
    }

    function loadMoodHistory() {
        const entries = JSON.parse(localStorage.getItem('moodHistory') || '[]');
        entries.forEach(text => {
            const entry = document.createElement('div');
            entry.className = 'mood-entry';
            entry.textContent = text;
            moodHistory.prepend(entry);
        });
    }

    // 简易跑团骰子功能
    const diceBtn = document.getElementById('dice-btn');
    const diceResult = document.getElementById('dice-result');

    diceBtn.addEventListener('click', function() {
        // 模拟骰子滚动动画
        let rolls = 0;
        const maxRolls = 20;
        const interval = setInterval(() => {
            const random = Math.floor(Math.random() * 6) + 1;
            diceResult.textContent = `🎲 投掷中... ${random}`;
            rolls++;
            if (rolls >= maxRolls) {
                clearInterval(interval);
                const result = Math.floor(Math.random() * 6) + 1;
                diceResult.textContent = `🎲 掷出了 ${result} 点！(ᐡ⸝⸝-  ̫ -⸝⸝ᐡ)`;
            }
        }, 50);
    });

    // 32*32像素画板功能
    const canvas = document.getElementById('pixel-canvas');
    const ctx = canvas.getContext('2d');
    const colorInput = document.getElementById('color-input');
    const clearBtn = document.getElementById('clear-btn');

    const PIXEL_SIZE = 8; // 8x8像素点，32*32=1024像素点，总尺寸256x256
    let isDrawing = false;

    // 初始化画布
    function initCanvas() {
        // 清空画布
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 绘制网格
        ctx.strokeStyle = '#f0f0f0';
        ctx.lineWidth = 1;

        for (let x = 0; x <= canvas.width; x += PIXEL_SIZE) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }

        for (let y = 0; y <= canvas.height; y += PIXEL_SIZE) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }

    // 绘制像素
    function drawPixel(x, y, color) {
        const pixelX = Math.floor(x / PIXEL_SIZE) * PIXEL_SIZE;
        const pixelY = Math.floor(y / PIXEL_SIZE) * PIXEL_SIZE;

        ctx.fillStyle = color;
        ctx.fillRect(pixelX, pixelY, PIXEL_SIZE, PIXEL_SIZE);

        // 绘制边框
        ctx.strokeStyle = '#f0f0f0';
        ctx.lineWidth = 1;
        ctx.strokeRect(pixelX, pixelY, PIXEL_SIZE, PIXEL_SIZE);
    }

    // 画布事件监听
    canvas.addEventListener('mousedown', function(e) {
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        drawPixel(x, y, colorInput.value);
    });

    canvas.addEventListener('mousemove', function(e) {
        if (isDrawing) {
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            drawPixel(x, y, colorInput.value);
        }
    });

    canvas.addEventListener('mouseup', function() {
        isDrawing = false;
    });

    canvas.addEventListener('mouseout', function() {
        isDrawing = false;
    });

    // 移动设备支持
    canvas.addEventListener('touchstart', function(e) {
        e.preventDefault();
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        const x = e.touches[0].clientX - rect.left;
        const y = e.touches[0].clientY - rect.top;
        drawPixel(x, y, colorInput.value);
    });

    canvas.addEventListener('touchmove', function(e) {
        e.preventDefault();
        if (isDrawing) {
            const rect = canvas.getBoundingClientRect();
            const x = e.touches[0].clientX - rect.left;
            const y = e.touches[0].clientY - rect.top;
            drawPixel(x, y, colorInput.value);
        }
    });

    canvas.addEventListener('touchend', function() {
        isDrawing = false;
    });

    clearBtn.addEventListener('click', function() {
        initCanvas();
    });

    // 初始化画布
    initCanvas();

    // 添加一些可爱的CSS样式
    const style = document.createElement('style');
    style.textContent = `
        .cute-section {
            text-align: center;
            margin: 2rem 0;
            color: #ff9eaa;
        }

        .emoji {
            font-size: 1.5rem;
            margin: 1rem 0;
        }

        .feature-card {
            background-color: #fff;
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 5px 15px rgba(201, 92, 122, 0.1);
        }

        .feature-card h3 {
            color: #C65C7A;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
        }

        .feature-card h3::before {
            margin-right: 0.5rem;
        }

        .dialogue-box {
            height: 200px;
            overflow-y: auto;
            border: 2px solid #EFD6DE;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: #f9f2f4;
        }

        .message {
            max-width: 70%;
            padding: 0.5rem 1rem;
            border-radius: 18px;
            margin-bottom: 0.5rem;
            word-break: break-word;
        }

        .message.received {
            background-color: #EFD6DE;
            color: #333;
            border-top-left-radius: 5px;
            margin-right: auto;
        }

        .message.sent {
            background-color: #C65C7A;
            color: white;
            border-top-right-radius: 5px;
            margin-left: auto;
        }

        #message-input, #board-input, #todo-input {
            width: calc(100% - 80px);
            padding: 0.8rem;
            border: 2px solid #E896AB;
            border-radius: 20px;
            margin-right: 0.5rem;
            background-color: #fff;
        }

        #send-btn, #board-btn, #todo-btn {
            padding: 0.8rem 1.5rem;
            background-color: #C65C7A;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        #send-btn:hover, #board-btn:hover, #todo-btn:hover {
            background-color: #AA395E;
        }

        #message-board {
            min-height: 100px;
            border: 2px dashed #EFD6DE;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .board-message {
            padding: 0.5rem;
            border-bottom: 1px solid #EFD6DE;
        }

        #todo-list {
            list-style-type: none;
            margin-bottom: 1rem;
        }

        .todo-item {
            display: flex;
            align-items: center;
            padding: 0.8rem;
            border-bottom: 1px solid #EFD6DE;
        }

        .todo-item.completed span {
            text-decoration: line-through;
            color: #888;
        }

        .todo-checkbox {
            margin-right: 1rem;
            width: 18px;
            height: 18px;
        }

        .todo-delete {
            margin-left: auto;
            background-color: #ffccd5;
            color: #C65C7A;
            border: none;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .mood-options {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }

        .mood-btn {
            padding: 0.5rem 1rem;
            background-color: #fff;
            border: 2px solid #E896AB;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1.5rem;
            transition: all 0.3s;
        }

        .mood-btn:hover {
            background-color: #EFD6DE;
            transform: scale(1.05);
        }

        #mood-history {
            min-height: 100px;
            border: 2px dashed #EFD6DE;
            border-radius: 10px;
            padding: 1rem;
        }

        .mood-entry {
            padding: 0.5rem;
            border-bottom: 1px solid #EFD6DE;
        }

        #dice-result {
            text-align: center;
            font-size: 1.2rem;
            margin: 1rem 0;
            padding: 1rem;
            border: 2px solid #E896AB;
            border-radius: 10px;
            background-color: #f9f2f4;
        }

        #dice-btn {
            display: block;
            width: 100%;
            padding: 1rem;
            background-color: #C65C7A;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.2rem;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        #dice-btn:hover {
            background-color: #AA395E;
        }

        #pixel-canvas {
            border: 2px solid #E896AB;
            border-radius: 10px;
            display: block;
            margin: 0 auto 1rem;
            cursor: crosshair;
        }

        .color-picker {
            display: flex;
            gap: 1rem;
            justify-content: center;
        }

        #color-input {
            width: 50px;
            height: 50px;
            border: none;
            cursor: pointer;
        }

        #clear-btn {
            padding: 0.5rem 1rem;
            background-color: #E896AB;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        #clear-btn:hover {
            background-color: #C65C7A;
        }
    `;
    document.head.appendChild(style);
});