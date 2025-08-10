// 导航栏交互
document.addEventListener('DOMContentLoaded', function() {
    // 流星雨弹幕效果
    function createMeteorShower() {
        // 创建输入框和发送按钮
        const meteorContainer = document.createElement('div');
        meteorContainer.className = 'meteor-container';
        meteorContainer.innerHTML = `
            <div class="meteor-input-container">
                <input type="text" id="meteorName" placeholder="enter~">
            </div>
        `;
        // 找到小猫鱼模块的主体容器
        const mainContainer = document.querySelector('.container');
        if (mainContainer) {
            mainContainer.appendChild(meteorContainer);
        } else {
            document.body.appendChild(meteorContainer);
        }

        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .meteor-container {
                display: flex;
                justify-content: center;
                padding: 20px 0;
            }
            .meteor-input-container {
                display: flex;
            }
            #meteorName {
                padding: 8px 12px;
                font-size: 16px;
                border: 2px solid #f8f5f2;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.8);
            }
            .meteor {
                position: fixed;
                color: #fff;
                font-size: 20px;
                font-weight: bold;
                pointer-events: none;
                text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #ff00de, 0 0 20px #ff00de;
                z-index: 999;
            }
        `;
        document.head.appendChild(style);

        // 处理输入
        const input = document.getElementById('meteorName');
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const name = this.value.trim();
                if (name) {
                    createMeteor(name);
                    this.value = '';
                }
            }
        
    // 黄金矿工游戏
    if (window.location.pathname.includes('about.html')) {
        console.log('黄金矿工游戏页面加载成功');
        // 获取Canvas元素和上下文
        const canvas = document.getElementById('miner-game');
        const ctx = canvas.getContext('2d');
        const scoreElement = document.getElementById('score');
        const timeElement = document.getElementById('time');
        const startButton = document.getElementById('start-btn');

        // 游戏状态
        let score = 0;
        let timeLeft = 60;
        let isPlaying = false;
        let gameInterval;
        let hook;
        let cats = [];
        let rocks = [];

        // 游戏配置
        const HOOK_SPEED = 3;
        const CAT_VALUE = 10;
        const ROCK_VALUE = -5;
        const SPAWN_INTERVAL = 1500;

        // 初始化钩子
        function initHook() {
            hook = {
                x: canvas.width / 2,
                y: 50,
                length: 0,
                angle: 0,
                isExtending: true,
                speed: HOOK_SPEED
            };
        }

        // 创建小猫
        function createCat() {
            const size = 30 + Math.random() * 20;
            return {
                x: 50 + Math.random() * (canvas.width - 100),
                y: canvas.height - 50 - size / 2,
                size: size,
                value: CAT_VALUE,
                type: 'cat'
            };
        }

        // 创建石头
        function createRock() {
            const size = 20 + Math.random() * 30;
            return {
                x: 50 + Math.random() * (canvas.width - 100),
                y: canvas.height - 50 - size / 2,
                size: size,
                value: ROCK_VALUE,
                type: 'rock'
            };
        }

        // 生成道具
        function spawnItems() {
            if (Math.random() > 0.3) {
                cats.push(createCat());
            } else {
                rocks.push(createRock());
            }
        }

        // 绘制钩子
        function drawHook() {
            ctx.beginPath();
            ctx.moveTo(canvas.width / 2, 50);
            ctx.lineTo(hook.x, hook.y);
            ctx.strokeStyle = '#8B4513';
            ctx.lineWidth = 3;
            ctx.stroke();

            // 绘制钩子头
            ctx.beginPath();
            ctx.arc(hook.x, hook.y, 10, 0, Math.PI * 2);
            ctx.fillStyle = '#CD853F';
            ctx.fill();
        }

        // 绘制小猫
        function drawCats() {
            cats.forEach(cat => {
                ctx.beginPath();
                ctx.arc(cat.x, cat.y, cat.size, 0, Math.PI * 2);
                // 从和谐色彩方案中选择小猫颜色
                const catColors = ['#DBED9B', '#B3CF81', '#CODA9D', '#E8EED6'];
                ctx.fillStyle = catColors[Math.floor(Math.random() * catColors.length)];
                ctx.fill();
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 2;
                ctx.stroke();

                // 猫眼睛
                ctx.beginPath();
                ctx.arc(cat.x - cat.size/4, cat.y - cat.size/4, cat.size/8, 0, Math.PI * 2);
                ctx.arc(cat.x + cat.size/4, cat.y - cat.size/4, cat.size/8, 0, Math.PI * 2);
                ctx.fillStyle = '#000';
                ctx.fill();

                // 猫嘴巴
                ctx.beginPath();
                ctx.arc(cat.x, cat.y + cat.size/5, cat.size/6, 0, Math.PI);
                ctx.stroke();
            });
        }

        // 绘制石头
        function drawRocks() {
            rocks.forEach(rock => {
                ctx.beginPath();
                ctx.arc(rock.x, rock.y, rock.size, 0, Math.PI * 2);
                // 从和谐色彩方案中选择石头颜色
                const rockColors = ['#6C6A7F', '#A193AE', '#DAB9C4', '#EDD6B7'];
                ctx.fillStyle = rockColors[Math.floor(Math.random() * rockColors.length)];
                ctx.fill();
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 2;
                ctx.stroke();
            });
        }

        // 检查碰撞
        function checkCollision() {
            // 检查钩子是否碰到小猫
            for (let i = 0; i < cats.length; i++) {
                const cat = cats[i];
                const dx = hook.x - cat.x;
                const dy = hook.y - cat.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 10 + cat.size) {
                    // 碰到小猫
                    score += cat.value;
                    scoreElement.textContent = score;
                    cats.splice(i, 1);
                    hook.isExtending = false;
                    return;
                }
            }

            // 检查钩子是否碰到石头
            for (let i = 0; i < rocks.length; i++) {
                const rock = rocks[i];
                const dx = hook.x - rock.x;
                const dy = hook.y - rock.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 10 + rock.size) {
                    // 碰到石头
                    score += rock.value;
                    if (score < 0) score = 0;
                    scoreElement.textContent = score;
                    rocks.splice(i, 1);
                    hook.isExtending = false;
                    // 减慢钩子速度
                    hook.speed = HOOK_SPEED / 2;
                    setTimeout(() => {
                        hook.speed = HOOK_SPEED;
                    }, 2000);
                    return;
                }
            }

            // 检查钩子是否到达底部
            if (hook.y >= canvas.height - 50) {
                hook.isExtending = false;
            }
        }

        // 更新钩子位置
        function updateHook() {
            if (hook.isExtending) {
                hook.length += hook.speed;
                hook.x = canvas.width / 2 + Math.sin(hook.angle) * hook.length;
                hook.y = 50 + Math.cos(hook.angle) * hook.length;
            } else {
                hook.length -= hook.speed;
                hook.x = canvas.width / 2 + Math.sin(hook.angle) * hook.length;
                hook.y = 50 + Math.cos(hook.angle) * hook.length;

                // 钩子收回后重置
                if (hook.length <= 0) {
                    hook.isExtending = true;
                    hook.angle = Math.random() * Math.PI / 2 - Math.PI / 4; // 随机角度
                }
            }
        }

        // 绘制游戏
        function drawGame() {
            // 清空画布
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 绘制背景
            ctx.fillStyle = '#87CEEB'; // 天空蓝
            ctx.fillRect(0, 0, canvas.width, canvas.height - 50);
            ctx.fillStyle = '#8B4513'; // 棕色地面
            ctx.fillRect(0, canvas.height - 50, canvas.width, 50);

            // 绘制钩子
            drawHook();

            // 绘制小猫
            drawCats();

            // 绘制石头
            drawRocks();
        }

        // 更新游戏状态
        function updateGame() {
            updateHook();
            checkCollision();
            drawGame();
        }

        // 开始游戏
        function startGame() {
            if (isPlaying) return;

            // 重置游戏状态
            score = 0;
            timeLeft = 60;
            scoreElement.textContent = score;
            timeElement.textContent = timeLeft;
            cats = [];
            rocks = [];
            initHook();

            isPlaying = true;
            startButton.disabled = true;
            startButton.textContent = '游戏中...';

            // 启动游戏循环
            gameInterval = setInterval(updateGame, 30);

            // 生成道具
            const spawnInterval = setInterval(spawnItems, SPAWN_INTERVAL);

            // 倒计时
            const timerInterval = setInterval(() => {
                timeLeft--;
                timeElement.textContent = timeLeft;

                if (timeLeft <= 0) {
                    clearInterval(timerInterval);
                    clearInterval(spawnInterval);
                    clearInterval(gameInterval);
                    isPlaying = false;
                    startButton.disabled = false;
                    startButton.textContent = '再玩一次';
                    alert('游戏结束！你的分数是: ' + score);
                }
            }, 1000);
        }

        // 添加开始按钮事件
        startButton.addEventListener('click', startGame);

        // 初始化游戏
        initHook();
        drawGame();
        console.log('游戏初始化完成');
    }

});
    }

    // 创建流星
    function createMeteor(text) {
        const meteor = document.createElement('div');
        meteor.className = 'meteor';
        meteor.textContent = text;

        // 随机位置和样式
        const startX = Math.random() * window.innerWidth;
        const startY = -50;
        const endX = startX + (Math.random() * 200 - 100);
        const endY = window.innerHeight + 50;
        // 减慢弹幕速度(5-10秒)
        const duration = 5000 + Math.random() * 5000;
        const delay = Math.random() * 1000;
        const rotation = Math.random() * 360;
        const opacity = 0.7 + Math.random() * 0.3;

        meteor.style.left = `${startX}px`;
        meteor.style.top = `${startY}px`;
        meteor.style.transform = `rotate(${rotation}deg)`;
        // 使用用户提供的和谐色彩方案
        const colors = [
            '#DBED9B', '#FDCFD5', '#FF97AE', '#F16588',
            '#93B06F', '#B3CF81', '#CODA9D', '#E8EED6',
            '#DAB9C4', '#EDD6B7', '#A193AE', '#6C6A7F',
            '#EFD6DE', '#E896AB', '#C65C7A', '#AA395E'
        ];
        const randomColor = colors[Math.floor(Math.random() * colors.length)];
        meteor.style.color = randomColor;
        meteor.style.textShadow = `0 0 5px ${randomColor}, 0 0 10px ${randomColor}, 0 0 15px ${randomColor}, 0 0 20px ${randomColor}`;
        meteor.style.opacity = opacity;

        document.body.appendChild(meteor);

        // 动画
        setTimeout(() => {
            let startTime;
            function animate(timestamp) {
                if (!startTime) startTime = timestamp;
                const progress = timestamp - startTime;
                const percentage = Math.min(progress / duration, 1);

                // 线性插值
                const x = startX + (endX - startX) * percentage;
                const y = startY + (endY - startY) * percentage;
                const currentOpacity = opacity * (1 - percentage);

                meteor.style.left = `${x}px`;
                meteor.style.top = `${y}px`;
                meteor.style.opacity = currentOpacity;

                if (percentage < 1) {
                    requestAnimationFrame(animate);
                } else {
                    meteor.remove();
                }
            }

            requestAnimationFrame(animate);
        }, delay);
    }

    // 只在小猫鱼板块(contact.html)显示弹幕
    if (window.location.pathname.includes('contact.html')) {
        createMeteorShower();
    }

    // 导航栏交互

    // 获取所有导航链接
    const navLinks = document.querySelectorAll('.nav-links a');

    // 为每个导航链接添加点击事件
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // 移除所有链接的active类
            navLinks.forEach(l => l.classList.remove('active'));
            // 为当前点击的链接添加active类
            this.classList.add('active');
        });
    });

    // 检查当前页面URL，为对应的导航链接添加active类
    const currentUrl = window.location.href;
    navLinks.forEach(link => {
        if (currentUrl.includes(link.getAttribute('href'))) {
            link.classList.add('active');
        }
    });

    // 平滑滚动功能
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // 面包猫猫分页功能
    if (window.location.pathname.includes('products.html')) {
        // 定义所有面包猫数据
        const breadCats = [
            { name: '可颂猫', englishName: 'Croissant Cat', description: '可爱的可颂造型猫咪，像刚出炉的可颂一样松软诱人。' },
            { name: '泡芙猫', englishName: 'Cream Puff Cat', description: '圆滚滚的泡芙造型猫咪，肚子里装满了甜甜的奶油。' },
            { name: '蛋挞猫', englishName: 'Egg Tart Cat', description: '酥脆外皮包裹着嫩滑内心的蛋挞造型猫咪。' },
            { name: '法棍猫', englishName: 'Baguette Cat', description: '修长优雅的法棍造型猫咪，有着酥脆的外皮和柔软的内心。' },
            { name: '贝果猫', englishName: 'Bagel Cat', description: '圆润有嚼劲的贝果造型猫咪，中间有个可爱的小洞。' },
            { name: '菠萝包猫', englishName: 'Pineapple Bun Cat', description: '表面有格子花纹的菠萝包造型猫咪，香甜可口。' },
            { name: '蜜瓜包猫', englishName: 'Melon Pan Cat', description: '有着蜜瓜纹路的面包造型猫咪，外酥里嫩。' },
            { name: '甜甜圈猫', englishName: 'Donut Cat', description: '多彩可爱的甜甜圈造型猫咪，上面撒满了糖霜。' },
            { name: '吐司猫', englishName: 'Toast Cat', description: '方正可爱的吐司造型猫咪，金黄诱人。' },
            { name: '麻糬猫', englishName: 'Mochi Cat', description: '软糯Q弹的麻糬造型猫咪，有着可爱的糯米光泽。' },
            { name: '羊角猫', englishName: 'Kipfel Cat', description: '弯弯的羊角造型猫咪，酥脆多层。' },
            { name: '年轮猫', englishName: 'Baumkuchen Cat', description: '有着层层年轮的蛋糕造型猫咪，口感丰富。' },
            { name: '铜锣烧猫', englishName: 'Dorayaki Cat', description: '两片松软蛋糕夹着红豆馅的铜锣烧造型猫咪。' },
            { name: '玛芬猫', englishName: 'Muffin Cat', description: '松软可口的玛芬造型猫咪，上面有可爱的花纹。' },
            { name: '司康猫', englishName: 'Scone Cat', description: '外酥里嫩的司康造型猫咪，适合搭配奶茶食用。' },
            { name: '巧克力猫', englishName: 'Chocolate Bread Cat', description: '浓郁巧克力味的面包造型猫咪，深受巧克力爱好者喜爱。' },
            { name: '肉桂卷猫', englishName: 'Cinnamon Roll Cat', description: '有着肉桂香气的卷状猫咪，香甜可口。' },
            { name: '牛角猫', englishName: 'Croissant Cat', description: '弯弯的牛角造型猫咪，酥脆多层。' },
            { name: '红豆面包猫', englishName: 'Anpan Cat', description: '松软面包夹着甜蜜红豆馅的猫咪造型。' },
            { name: '奶油猫', englishName: 'Cream Bread Cat', description: '充满奶油香气的猫咪造型面包。' },
            { name: '咖喱面包猫', englishName: 'Curry Bread Cat', description: '外皮酥脆，内馅浓郁的咖喱面包造型猫咪。' },
            { name: '披萨猫', englishName: 'Pizza Bread Cat', description: '有着披萨风味的面包造型猫咪，上面撒有芝士和香料。' },
            { name: '果酱猫', englishName: 'Jam Bread Cat', description: '夹着甜美果酱的面包造型猫咪。' },
            { name: '奶酪猫', englishName: 'Cheese Bread Cat', description: '充满芝士香气的面包造型猫咪。' },
            { name: '葡萄干猫', englishName: 'Raisin Bread Cat', description: '添加了大量葡萄干的面包造型猫咪，酸甜可口。' },
            { name: '黑糖猫', englishName: 'Brown Sugar Bread Cat', description: '有着黑糖香气的面包造型猫咪，香甜可口。' },
            { name: '抹茶猫', englishName: 'Matcha Bread Cat', description: '有着抹茶香气的面包造型猫咪，清新可口。' },
            { name: '草莓猫', englishName: 'Strawberry Bread Cat', description: '添加了新鲜草莓的面包造型猫咪，酸甜可口。' },
            { name: '香蕉猫', englishName: 'Banana Bread Cat', description: '有着香蕉香气的面包造型猫咪，香甜软糯。' },
            { name: '南瓜猫', englishName: 'Pumpkin Bread Cat', description: '添加了南瓜泥的面包造型猫咪，营养丰富。' },
            { name: '香肠卷猫', englishName: 'Sausage Roll Cat', description: '酥脆外皮包裹着香肠的卷状猫咪造型。' },
            { name: '海苔猫', englishName: 'Seaweed Bread Cat', description: '添加了海苔的面包造型猫咪，咸香可口。' },
            { name: '芝麻猫', englishName: 'Sesame Bread Cat', description: '表面撒满芝麻的面包造型猫咪，香气四溢。' },
            { name: '核桃猫', englishName: 'Walnut Bread Cat', description: '添加了核桃的面包造型猫咪，营养丰富。' },
            { name: '苹果派猫', englishName: 'Apple Pie Cat', description: '有着苹果派风味的面包造型猫咪，香甜可口。' },
            { name: '蓝莓猫', englishName: 'Blueberry Bread Cat', description: '添加了新鲜蓝莓的面包造型猫咪，酸甜可口。' },
            { name: '柠檬猫', englishName: 'Lemon Bread Cat', description: '有着柠檬香气的面包造型猫咪，清新可口。' },
            { name: '椰子猫', englishName: 'Coconut Bread Cat', description: '添加了椰子的面包造型猫咪，香气浓郁。' },
            { name: '咖啡猫', englishName: 'Coffee Bread Cat', description: '有着咖啡香气的面包造型猫咪，适合搭配咖啡食用。' },
            { name: '蜂蜜猫', englishName: 'Honey Bread Cat', description: '添加了蜂蜜的面包造型猫咪，香甜可口。' },
            { name: '杏仁猫', englishName: 'Almond Bread Cat', description: '添加了杏仁的面包造型猫咪，香气四溢。' },
            { name: '紫薯猫', englishName: 'Purple Sweet Potato Bread Cat', description: '添加了紫薯的面包造型猫咪，营养丰富。' },
            { name: '牛奶猫', englishName: 'Milk Bread Cat', description: '添加了牛奶的面包造型猫咪，奶香浓郁。' },
            { name: '黑森林猫', englishName: 'Black Forest Bread Cat', description: '有着黑森林蛋糕风味的面包造型猫咪。' },
            { name: '栗子猫', englishName: 'Chestnut Bread Cat', description: '添加了栗子的面包造型猫咪，香甜软糯。' },
            { name: '提拉米苏猫', englishName: 'Tiramisu Bread Cat', description: '有着提拉米苏风味的面包造型猫咪，口感丰富。' },
            { name: '芒果猫', englishName: 'Mango Bread Cat', description: '添加了新鲜芒果的面包造型猫咪，果香浓郁。' },
            { name: '覆盆子猫', englishName: 'Raspberry Bread Cat', description: '添加了覆盆子的面包造型猫咪，酸甜可口。' },
            { name: '香草猫', englishName: 'Vanilla Bread Cat', description: '有着香草香气的面包造型猫咪，清新可口。' },
            { name: '樱花猫', englishName: 'Sakura Bread Cat', description: '有着樱花香气的面包造型猫咪，粉嫩可爱。' }
        ];

        // 分页配置
        const itemsPerPage = 12;
        let currentPage = 1;
        const totalPages = Math.ceil(breadCats.length / itemsPerPage);

        // 获取DOM元素
        const productGrid = document.getElementById('productGrid');
        const prevPageBtn = document.getElementById('prevPage');
        const nextPageBtn = document.getElementById('nextPage');
        const pageNumbersContainer = document.getElementById('pageNumbers');

        // 渲染面包猫卡片
        function renderBreadCats(page) {
            productGrid.innerHTML = '';
            const startIndex = (page - 1) * itemsPerPage;
            const endIndex = Math.min(startIndex + itemsPerPage, breadCats.length);
            const currentCats = breadCats.slice(startIndex, endIndex);

            currentCats.forEach(cat => {
                const card = document.createElement('div');
                card.className = 'product-card';
                card.innerHTML = `
                    <div class="product-image">
                        <p>${cat.name}</p>
                    </div>
                    <div class="product-info">
                        <h3>${cat.name} (${cat.englishName})</h3>
                        <p>${cat.description}</p>
                    </div>
                `;
                productGrid.appendChild(card);
            });
        }

        // 渲染分页按钮
        function renderPagination() {
            pageNumbersContainer.innerHTML = '';

            // 显示当前页前后各2页
            let startPage = Math.max(1, currentPage - 2);
            let endPage = Math.min(totalPages, currentPage + 2);

            // 确保至少显示5个页码
            if (endPage - startPage < 4) {
                if (startPage === 1) {
                    endPage = Math.min(5, totalPages);
                } else if (endPage === totalPages) {
                    startPage = Math.max(1, totalPages - 4);
                }
            }

            // 添加第一页按钮
            if (startPage > 1) {
                addPageButton(1);
                if (startPage > 2) {
                    addEllipsis();
                }
            }

            // 添加中间页码按钮
            for (let i = startPage; i <= endPage; i++) {
                addPageButton(i);
            }

            // 添加最后一页按钮
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    addEllipsis();
                }
                addPageButton(totalPages);
            }

            // 更新上一页/下一页按钮状态
            prevPageBtn.disabled = currentPage === 1;
            nextPageBtn.disabled = currentPage === totalPages;
        }

        // 添加页码按钮
        function addPageButton(page) {
            const button = document.createElement('button');
            button.className = `page-number ${currentPage === page ? 'active' : ''}`;
            button.textContent = page;
            button.addEventListener('click', () => {
                currentPage = page;
                renderBreadCats(currentPage);
                renderPagination();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
            pageNumbersContainer.appendChild(button);
        }

        // 添加省略号
        function addEllipsis() {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'ellipsis';
            ellipsis.textContent = '...';
            pageNumbersContainer.appendChild(ellipsis);
        }

        // 上一页按钮事件
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderBreadCats(currentPage);
                renderPagination();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });

        // 下一页按钮事件
        nextPageBtn.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                renderBreadCats(currentPage);
                renderPagination();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });

        // 初始化
        renderBreadCats(currentPage);
        renderPagination();
    }
});