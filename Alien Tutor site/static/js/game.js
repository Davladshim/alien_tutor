// ===== КОСМИЧЕСКАЯ ИГРА - БАЗОВАЯ ЛОГИКА =====

// Глобальные переменные игры
let gameState = {
    dailyScore: 0,
    starsFound: 0,
    starsTotal: 5,
    cometsCount: 0,
    cometsMax: 5,
    hasShip: false,
    gameStarted: false,
    gameCompleted: false
};

// ===== ИНИЦИАЛИЗАЦИЯ ИГРЫ =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Космическая игра загружается...');
    
    // Инициализируем интерфейс
    initGameInterface();
    
    // Имитируем загрузку лабиринта
    setTimeout(() => {
        showGameReady();
    }, 2000);
});

// ===== ФУНКЦИИ ИНТЕРФЕЙСА =====

function initGameInterface() {
    // Обновляем статистику
    updateStats();
    

    
    console.log('📊 Интерфейс игры инициализирован');
}

function updateStats() {
    // Обновляем отображение статистики
    document.getElementById('dailyScore').textContent = gameState.dailyScore;
    document.getElementById('starsFound').textContent = `${gameState.starsFound}/${gameState.starsTotal}`;
    
    // Обновляем карман
    updatePocket();
}

function updatePocket() {
    const pocketIcon = document.getElementById('pocketIcon');
    const pocketStatus = document.getElementById('pocketStatus');
    const pocketCard = pocketIcon.closest('.stat-item'); // Изменено с .stat-card на .stat-item
    
    if (gameState.hasShip) {
        pocketIcon.textContent = '🛸';
        pocketStatus.textContent = 'Тарелка';
        pocketCard.classList.add('pocket-has-ship');
    } else {
        pocketIcon.textContent = '👽';
        pocketStatus.textContent = 'Пусто';
        pocketCard.classList.remove('pocket-has-ship');
    }
}

// ===== ГЕНЕРАТОР ЛАБИРИНТА =====

const CELL_SIZE = 32; // Размер ячейки в пикселях
const PLAYER_SIZE = '1.8rem'; // Размер игрока

let maze = [];
let mazeWidth = 0;
let mazeHeight = 0;

// Генерация лабиринта как в примере (границы между ячейками)
function generateMaze() {
    const container = document.getElementById('mazeContainer');
    const containerRect = container.getBoundingClientRect();
    
    // Вычисляем количество ячеек
    mazeWidth = Math.floor((containerRect.width - 40) / CELL_SIZE);
    mazeHeight = Math.floor((containerRect.height - 40) / CELL_SIZE);
    
    console.log(`🧩 Генерируем лабиринт ${mazeWidth}x${mazeHeight} с границами`);
    
    // Создаем сетку ячеек (как в примере)
    const grid = [];
    for (let y = 0; y < mazeHeight; y++) {
        grid[y] = [];
        for (let x = 0; x < mazeWidth; x++) {
            grid[y][x] = {
                x: x,
                y: y,
                walls: [true, true, true, true], // top, right, bottom, left  
                visited: false
            };
        }
    }
    
    // Генерируем лабиринт алгоритмом из примера
    carvePassages(grid, 0, 0);
    
    // Отрисовываем
    renderMazeWithBorders(grid);
}

// Алгоритм как в твоем примере
function carvePassages(grid, startX, startY) {
    const stack = [];
    const start = grid[startY][startX];
    start.visited = true;
    stack.push(start);

    while (stack.length > 0) {
        const current = stack.pop();
        const neighbors = getUnvisitedNeighbors(grid, current);

        if (neighbors.length > 0) {
            stack.push(current);
            const next = neighbors[Math.floor(Math.random() * neighbors.length)];
            removeWalls(current, next);
            next.visited = true;
            stack.push(next);
        }
    }
}

// Функция перемешивания массива
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

// Отрисовка лабиринта тонкими линиями
function renderMaze() {
    const container = document.getElementById('mazeContainer');
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    // Создаем canvas для лабиринта
    const canvas = document.createElement('canvas');
    canvas.width = mazeWidth * CELL_SIZE;
    canvas.height = mazeHeight * CELL_SIZE;
    canvas.style.border = '2px solid #5ED9D7';
    canvas.style.borderRadius = '8px';
    canvas.style.boxShadow = '0 0 20px rgba(94, 217, 215, 0.4)';
    
    const ctx = canvas.getContext('2d');
    
    // Настройка неонового эффекта для тонких линий
    ctx.strokeStyle = "#5ED9D7";
    ctx.lineWidth = 2;
    ctx.shadowColor = "#5ED9D7";
    ctx.shadowBlur = 8;
    
    // Рисуем ТОЛЬКО линии между ячейками (не блоки!)
    for (let y = 0; y < mazeHeight; y++) {
        for (let x = 0; x < mazeWidth; x++) {
            const pixelX = x * CELL_SIZE;
            const pixelY = y * CELL_SIZE;
            
            // Если это стена, рисуем линии границ
            if (maze[y][x] === 1) {
                // Проверяем соседей и рисуем линии только там, где нужно
                
                // Верхняя линия
                if (y === 0 || maze[y-1][x] === 0) {
                    ctx.beginPath();
                    ctx.moveTo(pixelX, pixelY);
                    ctx.lineTo(pixelX + CELL_SIZE, pixelY);
                    ctx.stroke();
                }
                
                // Правая линия
                if (x === mazeWidth-1 || maze[y][x+1] === 0) {
                    ctx.beginPath();
                    ctx.moveTo(pixelX + CELL_SIZE, pixelY);
                    ctx.lineTo(pixelX + CELL_SIZE, pixelY + CELL_SIZE);
                    ctx.stroke();
                }
                
                // Нижняя линия
                if (y === mazeHeight-1 || maze[y+1][x] === 0) {
                    ctx.beginPath();
                    ctx.moveTo(pixelX + CELL_SIZE, pixelY + CELL_SIZE);
                    ctx.lineTo(pixelX, pixelY + CELL_SIZE);
                    ctx.stroke();
                }
                
                // Левая линия
                if (x === 0 || maze[y][x-1] === 0) {
                    ctx.beginPath();
                    ctx.moveTo(pixelX, pixelY + CELL_SIZE);
                    ctx.lineTo(pixelX, pixelY);
                    ctx.stroke();
                }
            }
        }
    }
    
    ctx.shadowBlur = 0;
    container.appendChild(canvas);
    console.log('🎨 Лабиринт отрисован тонкими линиями!');
}

// ===== ИГРОК В ЛАБИРИНТЕ =====

let player = {
    x: 1, // Позиция в ячейках лабиринта
    y: 1,
    element: null
};

// Создание игрока
function createPlayer() {
    const container = document.getElementById('mazeContainer');
    
    // Создаем элемент игрока
    const playerElement = document.createElement('div');
    playerElement.style.position = 'absolute';
    playerElement.style.fontSize = PLAYER_SIZE;
    playerElement.style.zIndex = '10';
    playerElement.style.transition = 'all 0.2s ease';
    playerElement.style.filter = 'drop-shadow(0 0 10px rgba(94, 217, 215, 0.8))';
    playerElement.textContent = '👽';
    playerElement.id = 'player';
    
    // Устанавливаем начальную позицию
    updatePlayerPosition(playerElement);
    
    container.appendChild(playerElement);
    player.element = playerElement;
    
    console.log('👽 Игрок создан на позиции', player.x, player.y);
}

// Обновление позиции игрока на экране
function updatePlayerPosition(element) {
    const container = document.getElementById('mazeContainer');
    const containerRect = container.getBoundingClientRect();
    const canvas = container.querySelector('canvas');
    
    if (canvas) {
        const canvasRect = canvas.getBoundingClientRect();
        const containerOffsetX = canvasRect.left - containerRect.left;
        const containerOffsetY = canvasRect.top - containerRect.top;
        
        // Вычисляем позицию в пикселях с центрированием в ячейке
        const pixelX = containerOffsetX + (player.x * CELL_SIZE) + (CELL_SIZE / 2);
        const pixelY = containerOffsetY + (player.y * CELL_SIZE) + (CELL_SIZE / 2);
        
        element.style.left = pixelX + 'px';
        element.style.top = pixelY + 'px';
        element.style.transform = 'translate(-50%, -50%)'; // Центрируем
    }
}

// Проверка, можно ли двигаться в направлении (для новой структуры)
function canMoveTo(x, y) {
    // Проверяем границы лабиринта
    if (x < 0 || x >= mazeWidth || y < 0 || y >= mazeHeight) {
        return false;
    }
    
    // Проверяем, нет ли блока в целевой позиции
    const blockAtTarget = gameElements.blocks.find(block => block.x === x && block.y === y);
    if (blockAtTarget) {
        return false; // Блок блокирует движение
    }
    
    // Проверяем стены между текущей и целевой позицией
    const currentCell = window.mazeGrid[player.y][player.x];
    
    // Определяем направление движения
    const dx = x - player.x;
    const dy = y - player.y;
    
    // Проверяем стены в зависимости от направления
    if (dx === 1) { // движение вправо
        return !currentCell.walls[1];
    } else if (dx === -1) { // движение влево
        return !currentCell.walls[3];
    } else if (dy === 1) { // движение вниз
        return !currentCell.walls[2];
    } else if (dy === -1) { // движение вверх
        return !currentCell.walls[0];
    }
    
    return false;
}

// Движение игрока
function movePlayer(dx, dy) {
    // Запускаем таймер портала при первом движении
    startPortalTimer();
    const newX = player.x + dx;
    const newY = player.y + dy;
    
    if (canMoveTo(newX, newY)) {
        player.x = newX;
        player.y = newY;
        updatePlayerPosition(player.element);
        
        console.log(`👽 Игрок движется к (${player.x}, ${player.y})`);
    } else {
        console.log('🚫 Движение заблокировано стеной');
    }
}

// ===== ОБНОВЛЕННЫЕ ФУНКЦИИ =====

// Заменяем старую функцию управления
function handleGameKeys(event) {
    if (!gameState.gameStarted) return;
    
    switch(event.code) {
        case 'ArrowUp':
        case 'KeyW':
            console.log('🔼 Движение вверх');
            movePlayer(0, -1);
            event.preventDefault();
            break;
            
        case 'ArrowDown':
        case 'KeyS':
            console.log('🔽 Движение вниз');
            movePlayer(0, 1);
            event.preventDefault();
            break;
            
        case 'ArrowLeft':
        case 'KeyA':
            console.log('◀️ Движение влево');
            movePlayer(-1, 0);
            event.preventDefault();
            break;
            
        case 'ArrowRight':
        case 'KeyD':
            console.log('▶️ Движение вправо');
            movePlayer(1, 0);
            event.preventDefault();
            break;
            
        case 'Space':
            console.log('💥 Действие (пробел)');
            handleSpaceAction();
            event.preventDefault();
            break;
    }
}

// Заменяем старую функцию запуска
function showGameStarted() {
    console.log('🎮 Генерируем лабиринт...');
    
    setTimeout(() => {
        generateMaze();
        createPlayer();
        initializeGameElements();
        console.log('✅ Игра готова! Используй стрелки или WASD для движения');
    }, 500);
    // Запускаем систему комет
    startCometSystem();
}

// ===== НЕДОСТАЮЩИЕ ФУНКЦИИ =====

function showGameReady() {
    const placeholder = document.querySelector('.maze-placeholder');
    if (placeholder) {
        placeholder.innerHTML = `
            <div class="placeholder-icon">🌌</div>
            <div class="placeholder-text">Лабиринт готов!</div>
            <div style="margin-top: 1rem; font-size: 1rem; opacity: 0.8;">Нажми любую клавишу для начала</div>
        `;
        
        // Добавляем обработчик клавиш
        document.addEventListener('keydown', handleGameStart);
    }
}

function handleGameStart(event) {
    if (!gameState.gameStarted) {
        gameState.gameStarted = true;
        console.log('🎮 Игра началась!');
        
        // Убираем обработчик начала игры
        document.removeEventListener('keydown', handleGameStart);
        
        // Запускаем игру
        showGameStarted();
        
        // Добавляем основные обработчики игры
        document.addEventListener('keydown', handleGameKeys);
    }
}

// Недостающие функции для нового алгоритма
function getUnvisitedNeighbors(grid, cell) {
    const neighbors = [];
    const { x, y } = cell;

    // Проверяем соседей (вверх, право, вниз, лево)
    if (y > 0 && !grid[y - 1][x].visited) neighbors.push(grid[y - 1][x]); // top
    if (x < mazeWidth - 1 && !grid[y][x + 1].visited) neighbors.push(grid[y][x + 1]); // right  
    if (y < mazeHeight - 1 && !grid[y + 1][x].visited) neighbors.push(grid[y + 1][x]); // bottom
    if (x > 0 && !grid[y][x - 1].visited) neighbors.push(grid[y][x - 1]); // left

    return neighbors;
}

function removeWalls(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;

    if (dx === 1) {
        a.walls[3] = false; // left wall of a
        b.walls[1] = false; // right wall of b
    } else if (dx === -1) {
        a.walls[1] = false; // right wall of a
        b.walls[3] = false; // left wall of b
    }

    if (dy === 1) {
        a.walls[0] = false; // top wall of a
        b.walls[2] = false; // bottom wall of b
    } else if (dy === -1) {
        a.walls[2] = false; // bottom wall of a
        b.walls[0] = false; // top wall of b
    }
}

function renderMazeWithBorders(grid) {
    const container = document.getElementById('mazeContainer');
    container.innerHTML = '';
    
    const canvas = document.createElement('canvas');
    canvas.width = mazeWidth * CELL_SIZE;
    canvas.height = mazeHeight * CELL_SIZE;
    canvas.style.border = '2px solid #5ED9D7';
    canvas.style.borderRadius = '8px';
    canvas.style.boxShadow = '0 0 20px rgba(94, 217, 215, 0.4)';
    
    const ctx = canvas.getContext('2d');
    ctx.strokeStyle = "#5ED9D7";
    ctx.lineWidth = 2;
    ctx.shadowColor = "#5ED9D7";
    ctx.shadowBlur = 8;

    // Рисуем стены между ячейками
    for (let y = 0; y < mazeHeight; y++) {
        for (let x = 0; x < mazeWidth; x++) {
            const cell = grid[y][x];
            const pixelX = x * CELL_SIZE;
            const pixelY = y * CELL_SIZE;

            // Рисуем стены ячейки
            if (cell.walls[0]) { // top
                ctx.beginPath();
                ctx.moveTo(pixelX, pixelY);
                ctx.lineTo(pixelX + CELL_SIZE, pixelY);
                ctx.stroke();
            }
            if (cell.walls[1]) { // right
                ctx.beginPath();
                ctx.moveTo(pixelX + CELL_SIZE, pixelY);
                ctx.lineTo(pixelX + CELL_SIZE, pixelY + CELL_SIZE);
                ctx.stroke();
            }
            if (cell.walls[2]) { // bottom
                ctx.beginPath();
                ctx.moveTo(pixelX + CELL_SIZE, pixelY + CELL_SIZE);
                ctx.lineTo(pixelX, pixelY + CELL_SIZE);
                ctx.stroke();
            }
            if (cell.walls[3]) { // left
                ctx.beginPath();
                ctx.moveTo(pixelX, pixelY + CELL_SIZE);
                ctx.lineTo(pixelX, pixelY);
                ctx.stroke();
            }
        }
    }

    ctx.shadowBlur = 0;
    container.appendChild(canvas);
    console.log('🎨 Лабиринт с границами отрисован!');
    
    // Сохраняем grid для движения игрока
    window.mazeGrid = grid;
}

// ===== СИСТЕМА БЛОКОВ И ЭЛЕМЕНТОВ =====

let gameElements = {
    blocks: [], // [{x, y, type: 'block'}]
    stars: [], // [{x, y, type: 'star', solved: false}]
    ship: null, // {x, y, type: 'ship'}
    newPortal: null, // {x, y, type: 'portal'}
    oldPortal: {x: 1, y: 1, type: 'oldPortal'} // стартовая точка
};

// Поиск всех тупиков в лабиринте
function findDeadEnds() {
    const deadEnds = [];
    
    for (let y = 0; y < mazeHeight; y++) {
        for (let x = 0; x < mazeWidth; x++) {
            const cell = window.mazeGrid[y][x];
            
            // Считаем количество открытых проходов
            let openWalls = 0;
            if (!cell.walls[0]) openWalls++; // top
            if (!cell.walls[1]) openWalls++; // right  
            if (!cell.walls[2]) openWalls++; // bottom
            if (!cell.walls[3]) openWalls++; // left
            
            // Если только 1 проход = тупик, исключаем стартовую точку
            // Исключаем тупики в радиусе 4 клеток от старта (1,1)
            const distanceFromStart = Math.abs(x - 1) + Math.abs(y - 1);
            if (openWalls === 1 && distanceFromStart > 4) {
                deadEnds.push({x, y});
            }
        }
    }
    
    console.log(`🏠 Найдено ${deadEnds.length} тупиков`);
    return deadEnds;
}

// Размещение блоков: первый в тупике, остальные рядом
function placeBlocks() {
    const deadEnds = findDeadEnds();
    gameElements.blocks = [];
    
    // Берем только половину тупиков случайно
    const shuffledDeadEnds = [...deadEnds].sort(() => Math.random() - 0.5);
    const selectedDeadEnds = shuffledDeadEnds.slice(0, Math.ceil(deadEnds.length / 2));

    selectedDeadEnds.forEach(deadEnd => {
        // Первый блок всегда в тупике
        gameElements.blocks.push({
            x: deadEnd.x,
            y: deadEnd.y,
            type: 'block',
            hits: 0,
            maxHits: 2,
            containsItem: null
        });
        
        // Ищем места для дополнительных блоков рядом с тупиком
        const directions = [
            {dx: 0, dy: -1}, // вверх
            {dx: 1, dy: 0},  // вправо  
            {dx: 0, dy: 1},  // вниз
            {dx: -1, dy: 0}  // влево
        ];
        
        const possiblePositions = [];
        
        directions.forEach(dir => {
            const newX = deadEnd.x + dir.dx;
            const newY = deadEnd.y + dir.dy;
            
            // Проверяем границы и что есть проход
            if (newX >= 0 && newX < mazeWidth && newY >= 0 && newY < mazeHeight) {
                const cell = window.mazeGrid[deadEnd.y][deadEnd.x];
                
                let wallIndex = -1;
                if (dir.dx === 0 && dir.dy === -1) wallIndex = 0; // вверх
                if (dir.dx === 1 && dir.dy === 0) wallIndex = 1;   // вправо
                if (dir.dx === 0 && dir.dy === 1) wallIndex = 2;   // вниз
                if (dir.dx === -1 && dir.dy === 0) wallIndex = 3;  // влево
                
                if (wallIndex >= 0 && !cell.walls[wallIndex]) {
                    possiblePositions.push({x: newX, y: newY});
                }
            }
        });
        
        // Добавляем 1-2 дополнительных блока
        const additionalBlocks = Math.min(possiblePositions.length, Math.floor(Math.random() * 2) + 1);
        
        for (let i = 0; i < additionalBlocks; i++) {
            if (possiblePositions.length > 0) {
                const randomIndex = Math.floor(Math.random() * possiblePositions.length);
                const position = possiblePositions.splice(randomIndex, 1)[0];
                
                gameElements.blocks.push({
                    x: position.x,
                    y: position.y,
                    type: 'block',
                    hits: 0,
                    maxHits: 2,
                    containsItem: null
                });
            }
        }
    });
    
    console.log(`🧱 Размещено ${gameElements.blocks.length} блоков (в тупиках и рядом)`);
}

// Прячем элементы за блоками
function hideElementsBehindBlocks() {
    const availableBlocks = [...gameElements.blocks];
    
    // Прячем 5 звезд
    for (let i = 0; i < 5; i++) {
        if (availableBlocks.length > 0) {
            const randomIndex = Math.floor(Math.random() * availableBlocks.length);
            const block = availableBlocks.splice(randomIndex, 1)[0];
            block.containsItem = 'star';
            
            gameElements.stars.push({
                x: block.x,
                y: block.y,
                type: 'star',
                solved: false,
                hidden: true
            });
        }
    }
    
    // Прячем тарелку
    if (availableBlocks.length > 0) {
        const randomIndex = Math.floor(Math.random() * availableBlocks.length);
        const block = availableBlocks.splice(randomIndex, 1)[0];
        block.containsItem = 'ship';
        
        gameElements.ship = {
            x: block.x,
            y: block.y,
            type: 'ship',
            hidden: true
        };
    }
    
    // Прячем новый портал
    if (availableBlocks.length > 0) {
        const randomIndex = Math.floor(Math.random() * availableBlocks.length);
        const block = availableBlocks.splice(randomIndex, 1)[0];
        block.containsItem = 'portal';
        
        gameElements.newPortal = {
            x: block.x,
            y: block.y,
            type: 'portal',
            hidden: true
        };
    }
    
    console.log('🎁 Элементы спрятаны за блоками');
}

// Проверка блока рядом с игроком (с учетом стен)
function getBlockNearPlayer() {
    const directions = [
        {dx: 0, dy: -1, wallIndex: 0}, // вверх, проверяем верхнюю стену
        {dx: 1, dy: 0, wallIndex: 1},  // вправо, проверяем правую стену
        {dx: 0, dy: 1, wallIndex: 2},  // вниз, проверяем нижнюю стену
        {dx: -1, dy: 0, wallIndex: 3}  // влево, проверяем левую стену
    ];
    
    for (let dir of directions) {
        const checkX = player.x + dir.dx;
        const checkY = player.y + dir.dy;
        
        // Проверяем границы
        if (checkX < 0 || checkX >= mazeWidth || checkY < 0 || checkY >= mazeHeight) {
            continue;
        }
        
        // Проверяем, есть ли стена между игроком и целевой позицией
        const currentCell = window.mazeGrid[player.y][player.x];
        
        // Если стена есть - не можем достать блок
        if (currentCell.walls[dir.wallIndex]) {
            continue; // Стена блокирует доступ
        }
        
        // Ищем блок в этой позиции
        const block = gameElements.blocks.find(b => b.x === checkX && b.y === checkY);
        if (block) {
            console.log(`🔨 Блок найден! Между игроком и блоком нет стены.`);
            return block;
        }
    }
    
    console.log(`❌ Нет доступных блоков рядом (или заблокированы стенами).`);
    return null;
}

// Разрушение блока с двойным взрывом!
function hitBlock(block) {
    block.hits++;
    
    if (block.hits === 1) {
        console.log('🔨 ПЕРВЫЙ УДАР! Блок трещит и камешки разлетаются...');
        
        // Первый взрыв - блок трещит
        animateBlockDestroy(block.x, block.y);
        
        // Меняем вид блока на поврежденный
        setTimeout(() => {
            const blockElements = document.querySelectorAll('.block');
            blockElements.forEach(element => {
                const elementX = parseInt(element.getAttribute('data-x'));
                const elementY = parseInt(element.getAttribute('data-y'));
                
                if (elementX === block.x && elementY === block.y) {
                    element.textContent = '🟫'; // Коричневый поврежденный блок
                    element.style.filter = 'drop-shadow(0 0 5px rgba(139, 69, 19, 0.6))';
                }
            });
        }, 200); // Небольшая задержка чтобы взрыв был виден
        
    } else if (block.hits >= block.maxHits) {
        console.log('💥 ВТОРОЙ УДАР! Блок окончательно разрушен! МЕГАВЗРЫВ!');
        
        // Второй взрыв - окончательное разрушение
        animateBlockDestroy(block.x, block.y);
        
        // Проверяем, что было спрятано за блоком
        setTimeout(() => {
            if (block.containsItem) {
                revealHiddenItem(block);
            }
        }, 300); // Задержка чтобы сначала был взрыв
        
        // Удаляем блок из массива
        const blockIndex = gameElements.blocks.indexOf(block);
        if (blockIndex > -1) {
            gameElements.blocks.splice(blockIndex, 1);
        }
        
        // Удаляем визуальный элемент после взрыва
        setTimeout(() => {
            const blockElements = document.querySelectorAll('.block');
            blockElements.forEach(element => {
                const elementX = parseInt(element.getAttribute('data-x'));
                const elementY = parseInt(element.getAttribute('data-y'));
                
                if (elementX === block.x && elementY === block.y) {
                    element.remove();
                }
            });
            
        }, 100);
    }
}

// Показать спрятанный элемент (мгновенно)
function revealHiddenItem(block) {
    const {x, y} = block;
    
    switch(block.containsItem) {
        case 'star':
            console.log('⭐ Найдена звезда!');
            const star = gameElements.stars.find(s => s.x === x && s.y === y);
            if (star) {
                star.hidden = false;
                // Мгновенно создаем элемент звезды
                createGameElement(star.x, star.y, '⭐', 'game-element star');
            }
            break;
            
        case 'ship':
            console.log('🛸 Найдена тарелка!');
            if (gameElements.ship) {
                gameElements.ship.hidden = false;
                // Мгновенно создаем элемент тарелки
                createGameElement(gameElements.ship.x, gameElements.ship.y, '🛸', 'game-element ship');
            }
            break;
            
        case 'portal':
            console.log('🌀 Найден новый портал!');
            if (gameElements.newPortal) {
                gameElements.newPortal.hidden = false;
                // Мгновенно создаем элемент портала
                createGameElement(gameElements.newPortal.x, gameElements.newPortal.y, '🌀', 'game-element portal');
            }
            break;
            
        default:
            console.log('📦 За блоком ничего не было');
    }
}

// Отрисовка всех игровых элементов
function renderGameElements() {
    const container = document.getElementById('mazeContainer');
    
    // Удаляем старые элементы (кроме canvas и игрока)
    const elementsToRemove = container.querySelectorAll('.game-element');
    elementsToRemove.forEach(el => el.remove());
    
    // Рисуем блоки с правильным видом
    gameElements.blocks.forEach(block => {
        const emoji = block.hits === 0 ? '🧱' : '🟫'; // Целый или поврежденный
        createGameElement(block.x, block.y, emoji, 'game-element block');
    });
    
    // Рисуем видимые звезды
    gameElements.stars.forEach(star => {
        if (!star.hidden) {
            createGameElement(star.x, star.y, '⭐', 'game-element star');
        }
    });
    
    // Рисуем тарелку (если видима)
    if (gameElements.ship && !gameElements.ship.hidden) {
        createGameElement(gameElements.ship.x, gameElements.ship.y, '🛸', 'game-element ship');
    }
    
    // Рисуем новый портал (если виден)
    if (gameElements.newPortal && !gameElements.newPortal.hidden) {
        createGameElement(gameElements.newPortal.x, gameElements.newPortal.y, '🌀', 'game-element portal');
    }
    
    // Рисуем старый портал (стартовая точка)
    if (gameElements.oldPortal) {
        createGameElement(gameElements.oldPortal.x, gameElements.oldPortal.y, '🌀', 'game-element old-portal');
    }
}

// Создание визуального элемента на поле
function createGameElement(x, y, emoji, className) {
    const container = document.getElementById('mazeContainer');
    const element = document.createElement('div');
    
    element.className = className;
    // Добавляем атрибуты для отслеживания позиции
    element.setAttribute('data-x', x);
    element.setAttribute('data-y', y);
    element.textContent = emoji;
    element.style.position = 'absolute';
    element.style.fontSize = '1.2rem';
    element.style.zIndex = '5';
    element.style.filter = 'drop-shadow(0 0 8px rgba(94, 217, 215, 0.6))';
    element.style.transition = 'all 0.2s ease';
    
    // Позиционируем элемент
    const canvas = container.querySelector('canvas');
    if (canvas) {
        const containerRect = container.getBoundingClientRect();
        const canvasRect = canvas.getBoundingClientRect();
        const containerOffsetX = canvasRect.left - containerRect.left;
        const containerOffsetY = canvasRect.top - containerRect.top;
        
        const pixelX = containerOffsetX + (x * CELL_SIZE) + (CELL_SIZE / 2);
        const pixelY = containerOffsetY + (y * CELL_SIZE) + (CELL_SIZE / 2);
        
        element.style.left = pixelX + 'px';
        element.style.top = pixelY + 'px';
        element.style.transform = 'translate(-50%, -50%)';
    }
    
    container.appendChild(element);
}

// Обработка нажатия пробела
function handleSpaceAction() {
    // Проверяем, есть ли блок рядом с игроком
    const nearbyBlock = getBlockNearPlayer();
    if (nearbyBlock) {
        hitBlock(nearbyBlock);
        return;
    }
    
    // Проверяем, стоит ли игрок на звезде
    const currentStar = gameElements.stars.find(s => 
        s.x === player.x && s.y === player.y && !s.hidden && !s.solved
    );
    if (currentStar) {
        console.log('⭐ Активирована звезда! Открываем задачу...');
        openTaskModal(currentStar);
        return;
    }
    
    // Проверяем, стоит ли игрок на тарелке
    if (gameElements.ship && 
        gameElements.ship.x === player.x && 
        gameElements.ship.y === player.y && 
        !gameElements.ship.hidden && 
        !gameState.hasShip) {
        
        console.log('🛸 Тарелка взята в карман!');
        
        // Запускаем анимацию перелета в карман
        const shipElement = document.querySelector('.ship');
        if (shipElement) {
            animateShipToInventory(shipElement);
        }
        return;
    }
    
    // Проверяем, стоит ли игрок на новом портале
    if (gameElements.newPortal && 
        gameElements.newPortal.x === player.x && 
        gameElements.newPortal.y === player.y && 
        !gameElements.newPortal.hidden) {
        
        console.log('🌀 Попытка активации портала...');
        checkPortalActivation();
        return;
    }
    
    console.log('❓ Рядом ничего интересного нет');
}

// Проверка условий для активации портала
function checkPortalActivation() {
    const allStarsSolved = gameElements.stars.every(star => star.solved);
    
    console.log('🐛 DEBUG: Проверяем портал...');
    console.log('🐛 DEBUG: Все звезды решены?', allStarsSolved);
    console.log('🐛 DEBUG: Есть тарелка?', gameState.hasShip);
    console.log('🐛 DEBUG: Звезды найдено:', gameState.starsFound);
    
    if (allStarsSolved && gameState.hasShip) {
        console.log('🎉 Все условия выполнены! Улетаем через портал!');
        
        // Показываем экран завершения игры
        showGameComplete();
        
    } else {
        let missing = [];
        if (!allStarsSolved) missing.push(`решить все звезды (${gameState.starsFound}/5)`);
        if (!gameState.hasShip) missing.push('взять тарелку');
        
        console.log(`❌ Для активации портала нужно: ${missing.join(', ')}`);
        alert(`❌ Для активации портала нужно:\n${missing.join('\n')}`);
    }
}

// Показать экран завершения игры
function showGameComplete() {
    gameState.gameCompleted = true;
    
    const container = document.getElementById('mazeContainer');
    
    // Очищаем контейнер полностью
    container.innerHTML = '';
    
    // Создаем экран завершения
    const completionScreen = document.createElement('div');
    completionScreen.className = 'game-completion';
    completionScreen.innerHTML = `
        <div class="completion-content">
            <div class="completion-icon">🎉</div>
            <div class="completion-title">Миссия выполнена!</div>
            <div class="completion-subtitle">Ты успешно завершил космическое приключение!</div>
            
            <div class="completion-stats">
                <div class="completion-stat">
                    <span class="stat-icon">💎</span>
                    <span class="stat-text">Баллов заработано: ${gameState.dailyScore}</span>
                </div>
                <div class="completion-stat">
                    <span class="stat-icon">⭐</span>
                    <span class="stat-text">Звезд решено: ${gameState.starsFound}/5</span>
                </div>
            </div>
            
            <div class="completion-message">Завтра будет новый лабиринт с новыми задачами!</div>
            
            <div class="completion-actions">
                <button onclick="goToMenu()" class="completion-btn menu">📚 Вернуться к урокам</button>
            </div>
        </div>
    `;
    
    container.appendChild(completionScreen);
    
    console.log('🚀 Игра завершена успешно!');
}

// Возврат в меню
function goToMenu() {
    window.location.href = '/student';
}

// Инициализация всех элементов после создания лабиринта
function initializeGameElements() {
    placeBlocks();
    hideElementsBehindBlocks();
    renderGameElements();
    
    console.log('🎮 Все игровые элементы размещены!');
}

// ===== МОДАЛЬНОЕ ОКНО ДЛЯ ЗАДАЧ =====

let currentTask = {
    star: null,
    question: '',
    answer: '',
    attempts: 7
};

// Простые задачи для тестирования
const testTasks = [
    { question: 'Сколько будет 5 + 3?', answer: '8' },
    { question: 'Чему равно 7 × 4?', answer: '28' },
    { question: 'Сколько будет 15 - 6?', answer: '9' },
    { question: 'Чему равно 36 ÷ 6?', answer: '6' },
    { question: 'Сколько будет 2³ (два в кубе)?', answer: '8' },
    { question: 'Чему равен корень из 25?', answer: '5' },
    { question: 'Сколько будет 12 + 8?', answer: '20' },
    { question: 'Чему равно 9 × 3?', answer: '27' }
];

// Открытие модального окна с задачей
function openTaskModal(star) {
    currentTask.star = star;
    currentTask.attempts = 7;
    
    // Выбираем случайную задачу
    const randomTask = testTasks[Math.floor(Math.random() * testTasks.length)];
    currentTask.question = randomTask.question;
    currentTask.answer = randomTask.answer;
    
    // Заполняем модальное окно
    document.getElementById('taskText').textContent = currentTask.question;
    document.getElementById('taskAnswer').value = '';
    document.getElementById('attemptsLeft').textContent = currentTask.attempts;
    
    // Показываем модальное окно
    const modal = document.getElementById('taskModal');
    modal.classList.add('active');
    
    // Фокус на поле ввода
    setTimeout(() => {
        document.getElementById('taskAnswer').focus();
    }, 300);
    
    console.log('⭐ Открыто окно задачи:', currentTask.question);
}

// Закрытие модального окна
function closeTaskModal() {
    const modal = document.getElementById('taskModal');
    modal.classList.remove('active');
    currentTask.star = null;
    
    console.log('❌ Окно задачи закрыто');
}

// Проверка ответа
// Проверка ответа
function checkAnswer() {
    const userAnswer = document.getElementById('taskAnswer').value.trim();
    
    console.log('🐛 DEBUG: Проверяем ответ:', userAnswer);
    console.log('🐛 DEBUG: Правильный ответ:', currentTask.answer);
    console.log('🐛 DEBUG: Текущая звезда:', currentTask.star);
    
    if (userAnswer === '') {
        alert('Введи ответ!');
        return;
    }
    
    if (userAnswer === currentTask.answer) {
        console.log('✅ DEBUG: Ответ правильный!');
        
        // Засчитываем звезду
        if (currentTask.star) {
            console.log('🐛 DEBUG: Засчитываем звезду...');
            currentTask.star.solved = true;
            currentTask.star.hidden = true;
            gameState.starsFound++;
            
            console.log('🐛 DEBUG: Добавляем баллы...');
            addScore(10);
            
            console.log('🐛 DEBUG: Удаляем элемент...');
            // Анимация распада звезды
            animateStarDestroy(currentTask.star.x, currentTask.star.y);

            // Убираем звезду с поля
            currentTask.star.hidden = true;
            const starElements = document.querySelectorAll('.star');
            starElements.forEach(element => {
                const elementX = parseInt(element.getAttribute('data-x'));
                const elementY = parseInt(element.getAttribute('data-y'));
                
                if (elementX === currentTask.star.x && elementY === currentTask.star.y) {
                    element.remove();
                }
            });
            
            console.log('🐛 DEBUG: Закрываем модальное окно...');
        }
        
        closeTaskModal();
        
    } else {
        console.log('❌ DEBUG: Ответ неправильный');
        currentTask.attempts--;
        document.getElementById('attemptsLeft').textContent = currentTask.attempts;
        document.getElementById('taskAnswer').value = '';
        
        if (currentTask.attempts <= 0) {
            console.log('❌ Попытки исчерпаны!');
            alert('Попытки исчерпаны! Можешь вернуться к этой звезде позже.');
            closeTaskModal();
        } else {
            console.log('❌ Неправильный ответ. Попыток осталось:', currentTask.attempts);
            alert(`Неправильно! Попыток осталось: ${currentTask.attempts}`);
        }
    }
}

// Пропуск задачи
function skipTask() {
    console.log('⏭️ Задача пропущена');
    closeTaskModal();
}

// Обработка Enter в поле ввода
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        const answerInput = document.getElementById('taskAnswer');
        if (answerInput) {
            answerInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    checkAnswer();
                }
            });
        }
    }, 1000);
});

// ===== ЧИТЫ ДЛЯ ТЕСТИРОВАНИЯ =====

// Показать все скрытые элементы
function cheatRevealAll() {
    // Показываем все звезды
    gameElements.stars.forEach(star => {
        if (star.hidden) {
            star.hidden = false;
        }
    });
    
    // Показываем тарелку
    if (gameElements.ship && gameElements.ship.hidden) {
        gameElements.ship.hidden = false;
    }
    
    // Показываем портал
    if (gameElements.newPortal && gameElements.newPortal.hidden) {
        gameElements.newPortal.hidden = false;
    }
    
    // Перерисовываем
    renderGameElements();
    
    console.log('🎮 ЧИТ: Все элементы показаны!');
}

// Телепорт к элементу
function cheatTeleportTo(type, index = 0) {
    let target;
    
    switch(type) {
        case 'star':
            target = gameElements.stars[index];
            break;
        case 'ship':
            target = gameElements.ship;
            break;
        case 'portal':
        case 'newportal':
            target = gameElements.newPortal;
            break;
        case 'oldportal':
            target = gameElements.oldPortal;
            break;
        case 'block':
            target = gameElements.blocks[index];
            break;
    }
    
    if (target) {
        player.x = target.x;
        player.y = target.y;
        updatePlayerPosition(player.element);
        console.log(`🎮 ЧИТ: Телепорт к ${type}!`);
    }
}

// Сразу получить тарелку
function cheatGetShip() {
    gameState.hasShip = true;
    if (gameElements.ship) {
        gameElements.ship.hidden = true;
    }
    updateStats();
    renderGameElements();
    console.log('🎮 ЧИТ: Тарелка получена!');
}

// Решить все звезды
function cheatSolveAllStars() {
    gameElements.stars.forEach(star => {
        if (!star.solved) {
            star.solved = true;
            star.hidden = true;
            gameState.starsFound++;
            addScore(10);
        }
    });
    updateStats();
    renderGameElements();
    console.log('🎮 ЧИТ: Все звезды решены!');
}

// Экспортируем читы в консоль
window.cheatRevealAll = cheatRevealAll;
window.cheatTeleportTo = cheatTeleportTo;
window.cheatGetShip = cheatGetShip;
window.cheatSolveAllStars = cheatSolveAllStars;


console.log(`
🎮 ЧИТЫ ДЛЯ ТЕСТИРОВАНИЯ:
- cheatRevealAll() - показать все элементы
- cheatTeleportTo('star', 0) - телепорт к первой звезде
- cheatTeleportTo('ship') - телепорт к тарелке
- cheatTeleportTo('portal') - телепорт к новому порталу
- cheatTeleportTo('oldportal') - телепорт к старому порталу
- cheatGetShip() - получить тарелку
- cheatSolveAllStars() - решить все звезды
- cheatSpawnComet() - запустить комету принудительно
`);

// Функция для добавления баллов (отсутствовала!)
function addScore(points) {
    gameState.dailyScore += points;
    updateStats();
    
    // Эффект анимации при добавлении баллов
    const scoreElement = document.getElementById('dailyScore');
    if (scoreElement) {
        scoreElement.style.background = 'rgba(251, 191, 36, 0.3)';
        scoreElement.style.transform = 'scale(1.1)';
        
        setTimeout(() => {
            scoreElement.style.background = '';
            scoreElement.style.transform = 'scale(1)';
        }, 500);
    }
    
    console.log(`💎 Добавлено ${points} баллов! Всего: ${gameState.dailyScore}`);
}

// ===== СИСТЕМА КОМЕТ =====

let cometSystem = {
    direction: Math.random() > 0.5 ? 'leftToRight' : 'rightToLeft', // Направление на сегодня
    nextCometTime: Date.now() + (Math.random() * 10 * 60 * 1000), // Следующая комета через 0-10 мин
    activeCometId: 0,
    isRunning: false
};

// Запуск системы комет (с остановкой после завершения)
function startCometSystem() {
    if (cometSystem.isRunning) return;
    
    cometSystem.isRunning = true;
    console.log(`🌠 Система комет запущена!`);
    
    // Проверяем каждые 5 секунд, не пора ли запустить комету
    const cometInterval = setInterval(() => {
        // Останавливаем кометы если игра завершена или достигнут лимит
        if (gameState.gameCompleted || gameState.cometsCount >= gameState.cometsMax) {
            console.log('🌠 Система комет остановлена (игра завершена или лимит достигнут)');
            clearInterval(cometInterval);
            cometSystem.isRunning = false;
            return;
        }
        
        if (Date.now() >= cometSystem.nextCometTime) {
            launchComet();
            // Планируем следующую комету через случайное время (0-10 мин)
            cometSystem.nextCometTime = Date.now() + (Math.random() * 10 * 60 * 1000);
        }
    }, 5000);
}

// Запуск одной кометы (чистая рабочая версия)
function launchComet() {
    if (gameState.gameCompleted) {
        return;
    }
    
    const container = document.getElementById('mazeContainer');
    const containerRect = container.getBoundingClientRect();
    
    const comet = document.createElement('div');
    comet.className = 'comet';
    comet.id = `comet-${cometSystem.activeCometId++}`;
    
    // Случайно выбираем направление для каждой кометы
    const randomDirection = Math.random() > 0.5 ? 'leftToRight' : 'rightToLeft';
    
    // Устанавливаем базовые стили
    comet.style.position = 'absolute';
    comet.style.fontSize = '2rem';
    comet.style.zIndex = '100';
    comet.style.cursor = 'pointer';
    comet.style.filter = 'drop-shadow(0 0 10px rgba(255, 215, 0, 0.8))';
    
    if (randomDirection === 'leftToRight') {
        comet.textContent = '🌠';
        comet.style.left = (containerRect.width + 20) + 'px'; // Стартует справа
        comet.style.top = '-50px';
        comet.dataset.direction = 'leftToRight';
    } else {
        comet.textContent = '🌠';
        comet.style.transform = 'scaleX(-1)';
        comet.style.left = '-50px'; // Стартует слева
        comet.style.top = '-50px';
        comet.dataset.direction = 'rightToLeft';
    }
    
    comet.onclick = () => catchComet(comet);
    
    container.appendChild(comet);
    animateComet(comet);
    
    console.log(`🌠 Комета запущена: ${randomDirection}`);
}

// Анимация полета кометы (использует направление из dataset)
function animateComet(comet) {
    const container = document.getElementById('mazeContainer');
    const containerRect = container.getBoundingClientRect();
    
    comet.style.position = 'absolute';
    comet.style.fontSize = '2rem';
    comet.style.zIndex = '100';
    comet.style.cursor = 'pointer';
    comet.style.filter = 'drop-shadow(0 0 10px rgba(255, 215, 0, 0.8))';
    comet.style.transition = 'all 8s linear';
    
    // Запускаем анимацию через небольшую задержку
    setTimeout(() => {
        const direction = comet.dataset.direction;
        
        if (direction === 'leftToRight') {
            // Неотзеркаленная: правый верх → левый низ (вдоль хвоста)
            comet.style.right = 'auto';
            comet.style.left = '-50px';
            comet.style.top = (containerRect.height + 50) + 'px';
        } else {
            // Отзеркаленная: левый верх → правый низ
            comet.style.left = (containerRect.width + 50) + 'px';
            comet.style.right = 'auto';
            comet.style.top = (containerRect.height + 50) + 'px';
        }
    }, 100);
    
    // Удаляем комету после анимации
    setTimeout(() => {
        if (comet.parentNode) {
            comet.remove();
        }
    }, 8500);
}

// Ловля кометы
// Ловля кометы
function catchComet(comet) {
    if (gameState.cometsCount >= gameState.cometsMax) {
        return; // Уже поймали максимум (но это секрет!)
    }
    
    console.log(`🌠 Комета поймана! Запуск анимации...`);
    
    // Запускаем анимацию распада
    animateCometDestroy(comet);
    
    // Обновляем счетчики
    gameState.cometsCount++;
    gameState.dailyScore += 5;
    updateStats();
    
    console.log(`🌠 Всего комет поймано: ${gameState.cometsCount}/${gameState.cometsMax}`);
    console.log(`💎 +5 баллов! Всего баллов: ${gameState.dailyScore}`);
    
    // Убираем комету после небольшой задержки (чтобы анимация началась)
    setTimeout(() => {
        if (comet.parentNode) {
            comet.remove();
        }
    }, 100);
    
    // Проверяем, достигли ли лимита (секретно)
    if (gameState.cometsCount >= gameState.cometsMax) {
        console.log('🌠 Лимит комет достигнут (секретно). Новые кометы не будут появляться.');
    }
}

// ЧИТ: Принудительный запуск кометы
function cheatSpawnComet() {
    launchComet();
    console.log('🎮 ЧИТ: Комета запущена принудительно!');
}

// Экспортируем чит
window.cheatSpawnComet = cheatSpawnComet;

// ===== АНИМАЦИЯ СТАРОГО ПОРТАЛА =====

let portalTimer = null;
let playerHasMoved = false;

// Запуск таймера исчезновения портала (защищенная версия)
function startPortalTimer() {
    if (playerHasMoved || portalTimer) return;
    
    playerHasMoved = true;
    console.log('👽 Игрок начал движение! Портал исчезнет через 10 секунд...');
    
    portalTimer = setTimeout(() => {
        // Принудительно запускаем исчезновение портала независимо от других анимаций
        animatePortalDisappear();
        
        // Дополнительная защита - если через 3 секунды портал все еще есть, удаляем принудительно
        setTimeout(() => {
            const portalElement = document.querySelector('.old-portal');
            if (portalElement) {
                console.log('🌀 Принудительное удаление портала (резервная защита)');
                portalElement.remove();
                gameElements.oldPortal = null;
            }
        }, 3000);
        
    }, 10000); // 10 секунд
}

// Анимация исчезновения портала (защищенная от конфликтов)
function animatePortalDisappear() {
    const portalElement = document.querySelector('.old-portal');
    
    if (portalElement) {
        console.log('🌀 Старый портал исчезает (защищенная анимация)...');
        
        // Используем CSS анимацию вместо requestAnimationFrame
        portalElement.classList.add('disappearing');
        
        // Гарантированно удаляем элемент через фиксированное время
        const portalTimeout = setTimeout(() => {
            if (portalElement && portalElement.parentNode) {
                portalElement.remove();
                gameElements.oldPortal = null;
                console.log('🌀 Старый портал исчез (принудительно)!');
            }
        }, 2100); // Чуть больше времени анимации CSS (2000ms + буфер)
        
        // Сохраняем ID таймера чтобы можно было отменить при необходимости
        portalElement.dataset.timeoutId = portalTimeout;
    }
}

// ===== АНИМАЦИЯ РАСПАДА ЗВЕЗДЫ =====

// Анимация распада звезды на частички
// Анимация распада звезды на частички
function animateStarDestroy(x, y) {
    const container = document.getElementById('mazeContainer');
    const particleCount = 8; // Количество частичек
    
    console.log('⭐ Запуск анимации распада звезды...');
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'star-particle';
        particle.textContent = '⭐';
        
        // Вычисляем позицию как у других элементов
        const canvas = container.querySelector('canvas');
        if (canvas) {
            const containerRect = container.getBoundingClientRect();
            const canvasRect = canvas.getBoundingClientRect();
            const containerOffsetX = canvasRect.left - containerRect.left;
            const containerOffsetY = canvasRect.top - containerRect.top;
            
            const pixelX = containerOffsetX + (x * CELL_SIZE) + (CELL_SIZE / 2);
            const pixelY = containerOffsetY + (y * CELL_SIZE) + (CELL_SIZE / 2);
            
            particle.style.left = pixelX + 'px';
            particle.style.top = pixelY + 'px';
        }
        
        // Вычисляем направление разлета (равномерно по кругу)
        const angle = (i / particleCount) * Math.PI * 2;
        const distance = 40 + Math.random() * 30; // Случайное расстояние 40-70px
        
        const moveX = Math.cos(angle) * distance;
        const moveY = Math.sin(angle) * distance;
        
        // Устанавливаем CSS переменные для движения
        particle.style.setProperty('--move-x', moveX + 'px');
        particle.style.setProperty('--move-y', moveY + 'px');
        
        container.appendChild(particle);
        
        // Удаляем частичку после анимации
        setTimeout(() => {
            if (particle.parentNode) {
                particle.remove();
            }
        }, 1500);
    }
}

// ===== АНИМАЦИЯ ТАРЕЛКИ В КАРМАН =====

// Анимация перелета тарелки в карман
function animateShipToInventory(shipElement) {
    console.log('🛸 Тарелка летит в карман...');
    
    // Находим иконку кармана на панели статистики
    const pocketIcon = document.getElementById('pocketIcon');
    if (!pocketIcon || !shipElement) return;
    
    // Получаем позиции
    const shipRect = shipElement.getBoundingClientRect();
    const pocketRect = pocketIcon.getBoundingClientRect();
    
    // Вычисляем расстояние для перелета
    const deltaX = pocketRect.left - shipRect.left + (pocketRect.width / 2);
    const deltaY = pocketRect.top - shipRect.top + (pocketRect.height / 2);
    
    // Устанавливаем CSS переменные для целевой позиции
    shipElement.style.setProperty('--target-x', deltaX + 'px');
    shipElement.style.setProperty('--target-y', deltaY + 'px');
    
    // Запускаем анимацию
    shipElement.classList.add('ship-flying');
    
    // После анимации удаляем элемент и обновляем карман
    setTimeout(() => {
        if (shipElement.parentNode) {
            shipElement.remove();
        }
        
        // Обновляем отображение кармана
        gameState.hasShip = true;
        if (gameElements.ship) {
            gameElements.ship.hidden = true;
        }
        updateStats();
        
        console.log('🛸 Тарелка в кармане!');
    }, 1000);
}

// ===== АНИМАЦИЯ РАСПАДА КОМЕТЫ =====

// Анимация распада кометы на частички (как у звезды)
function animateCometDestroy(cometElement) {
    console.log('🌠 Запуск анимации распада кометы...');
    
    const container = document.getElementById('mazeContainer');
    const particleCount = 6; // Чуть меньше частичек чем у звезды
    
    // Получаем позицию кометы
    const cometRect = cometElement.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    
    const centerX = cometRect.left - containerRect.left + (cometRect.width / 2);
    const centerY = cometRect.top - containerRect.top + (cometRect.height / 2);
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'star-particle'; // Используем тот же класс что у звезды
        particle.textContent = '⭐'; // Распадается на звездочки
        
        particle.style.left = centerX + 'px';
        particle.style.top = centerY + 'px';
        
        // Вычисляем направление разлета (равномерно по кругу)
        const angle = (i / particleCount) * Math.PI * 2;
        const distance = 30 + Math.random() * 25; // Немного меньший разлет чем у звезды
        
        const moveX = Math.cos(angle) * distance;
        const moveY = Math.sin(angle) * distance;
        
        // Устанавливаем CSS переменные для движения
        particle.style.setProperty('--move-x', moveX + 'px');
        particle.style.setProperty('--move-y', moveY + 'px');
        
        container.appendChild(particle);
        
        // Удаляем частичку после анимации
        setTimeout(() => {
            if (particle.parentNode) {
                particle.remove();
            }
        }, 1500);
    }
}

// Анимация взрыва блока - точно как в примере с деревянным блоком
function animateBlockDestroy(x, y) {
    const container = document.getElementById('mazeContainer');
    
    console.log('🧱 ВЗРЫВ! Реалистичная физика как в примере...');
    
    // Создаем фрагменты блока (как в примере)
    const fragmentData = [
        {w: 8, h: 10, offsetX: 0, offsetY: 0},
        {w: 10, h: 8, offsetX: 8, offsetY: 0},
        {w: 8, h: 8, offsetX: 18, offsetY: 0},
        {w: 6, h: 12, offsetX: 0, offsetY: 10},
        {w: 12, h: 6, offsetX: 6, offsetY: 10},
        {w: 8, h: 10, offsetX: 18, offsetY: 8},
        {w: 10, h: 5, offsetX: 0, offsetY: 22},
        {w: 8, h: 5, offsetX: 10, offsetY: 16},
        {w: 8, h: 10, offsetX: 18, offsetY: 18}
    ];
    
    // Базовая позиция блока на экране
    const canvas = container.querySelector('canvas');
    let baseX, baseY;
    
    if (canvas) {
        const containerRect = container.getBoundingClientRect();
        const canvasRect = canvas.getBoundingClientRect();
        const containerOffsetX = canvasRect.left - containerRect.left;
        const containerOffsetY = canvasRect.top - containerRect.top;
        
        baseX = containerOffsetX + (x * CELL_SIZE);
        baseY = containerOffsetY + (y * CELL_SIZE);
    }
    
    fragmentData.forEach((fragData, index) => {
        const fragment = document.createElement('div');
        fragment.className = 'block-fragment';
        fragment.textContent = '🟫';
        fragment.style.fontSize = '0.4rem'; // Маленькие кусочки
        
        // Начальная позиция фрагмента
        const startX = baseX + fragData.offsetX;
        const startY = baseY + fragData.offsetY;
        
        fragment.style.position = 'absolute';
        fragment.style.left = startX + 'px';
        fragment.style.top = startY + 'px';
        fragment.style.zIndex = '150';
        fragment.style.pointerEvents = 'none';
        fragment.style.transform = 'translate(0, 0) rotate(0deg)';
        fragment.style.transition = 'none';
        
        container.appendChild(fragment);
        
        // Физика движения (как в примере)
        const physics = {
            x: startX,
            y: startY,
            vx: (Math.random() - 0.5) * 8 + (index % 2 === 0 ? 3 : -3), // Скорость по X
            vy: Math.random() * -8 - 2, // Скорость по Y (вверх сначала)
            rotation: 0,
            rotationSpeed: (Math.random() - 0.5) * 15, // Вращение
            gravity: 0.4 // Гравитация
        };
        
        // Анимация физики
        function animateFragment() {
            physics.x += physics.vx;
            physics.y += physics.vy;
            physics.vy += physics.gravity; // Применяем гравитацию
            physics.rotation += physics.rotationSpeed;
            
            // Замедление при падении
            if (physics.y > window.innerHeight) {
                physics.vx *= 0.8;
            }
            
            // Обновляем позицию на экране
            fragment.style.left = physics.x + 'px';
            fragment.style.top = physics.y + 'px';
            fragment.style.transform = `rotate(${physics.rotation}deg)`;
            
            // Продолжаем анимацию пока фрагмент на экране
            if (physics.y < window.innerHeight + 100 && 
                physics.x > -100 && physics.x < window.innerWidth + 100) {
                requestAnimationFrame(animateFragment);
            } else {
                // Удаляем фрагмент когда он улетел за экран
                if (fragment.parentNode) {
                    fragment.remove();
                }
            }
        }
        
        // Запускаем анимацию фрагмента
        requestAnimationFrame(animateFragment);
    });
}