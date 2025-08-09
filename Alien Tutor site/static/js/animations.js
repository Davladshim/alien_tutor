// ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
let mouseX = 0;
let mouseY = 0;
let isMouseMoving = false;
let mouseTimeout;
let isDark = true;
let starAnimations = [];
let cloudAnimations = [];

// ===== ФУНКЦИЯ ДЛЯ ПЛАВНОЙ АНИМАЦИИ ЗВЕЗД - ДОБАВЛЯЕМ БОЛЬШЕ РАНДОМНОСТИ =====
function animateStars() {
    const stars = document.querySelectorAll('.star.floating');
    
    stars.forEach((star, index) => {
        if (starAnimations[index]) {
            cancelAnimationFrame(starAnimations[index]);
        }
        
        let startTime = Date.now() + Math.random() * 20000;
        const animationType = Math.floor(Math.random() * 8);
        const randomDuration = 15 + Math.random() * 25;
        const randomAmplitude = 0.04 + Math.random() * 0.06;
        const randomPhase = Math.random() * Math.PI * 2;
        
        function animate() {
            if (!star.classList.contains('floating')) return;
            
            const elapsed = (Date.now() - startTime) / 1000;
            const progress = (elapsed % randomDuration) / randomDuration;
            
            let offsetY = 0;
            
            switch(animationType) {
                case 0:
                    offsetY = Math.sin(progress * Math.PI * 2 + randomPhase) * randomAmplitude;
                    break;
                case 1:
                    offsetY = Math.cos(progress * Math.PI * 2 + randomPhase) * randomAmplitude;
                    break;
                case 2:
                    offsetY = Math.sin(progress * Math.PI * 4 + randomPhase) * randomAmplitude * 0.7;
                    break;
                case 3:
                    offsetY = Math.cos(progress * Math.PI * 4 + randomPhase) * randomAmplitude * 0.8;
                    break;
                case 4:
                    offsetY = Math.sin(progress * Math.PI * 1.5 + randomPhase) * randomAmplitude * 1.2;
                    break;
                case 5:
                    offsetY = Math.cos(progress * Math.PI * 3 + randomPhase) * randomAmplitude * 0.9;
                    break;
                case 6:
                    offsetY = Math.sin(progress * Math.PI * 2.5 + randomPhase) * randomAmplitude * 1.1;
                    break;
                case 7:
                    offsetY = Math.cos(progress * Math.PI * 1.8 + randomPhase) * randomAmplitude * 0.6;
                    break;
            }
            
            const currentTransform = star.style.transform || 'translate(0px, 0px)';
            const matches = currentTransform.match(/translate\(([^,]+),\s*([^)]+)\)/);
            
            let currentX = 0;
            let currentY = 0;
            
            if (matches) {
                currentX = parseFloat(matches[1]);
                currentY = parseFloat(matches[2]);
            }
            
            star.style.transform = `translate(${currentX}px, ${currentY + offsetY}px)`;
            
            starAnimations[index] = requestAnimationFrame(animate);
        }
        
        setTimeout(() => {
            starAnimations[index] = requestAnimationFrame(animate);
        }, Math.random() * 15000);
    });
}

// ===== ФУНКЦИЯ ДЛЯ ПЛАВНОЙ АНИМАЦИИ ОБЛАКОВ (ИСПРАВЛЕННАЯ) =====
function animateClouds() {
    const clouds = document.querySelectorAll('.svg-cloud.floating');
    
    clouds.forEach((cloud, index) => {
        if (cloudAnimations[index]) {
            cancelAnimationFrame(cloudAnimations[index]);
        }
        
        let startTime = Date.now() + Math.random() * 10000;
        let animationType = index % 4;
        
        function animate() {
            if (!cloud.classList.contains('floating')) return;
            
            const elapsed = (Date.now() - startTime) / 1000;
            const duration = 20;
            
            let offsetY = 0;
            const progress = (elapsed % duration) / duration;
            
            // УВЕЛИЧЕННАЯ АМПЛИТУДА ПОКАЧИВАНИЙ (в 3 раза больше)
            switch(animationType) {
                case 0:
                    offsetY = Math.sin(progress * Math.PI * 2) * -0.18; // было -0.06
                    break;
                case 1:
                    offsetY = Math.sin(progress * Math.PI * 2 + Math.PI) * 0.15; // было 0.05
                    break;
                case 2:
                    offsetY = Math.sin(progress * Math.PI * 2) * -0.21; // было -0.07
                    break;
                case 3:
                    offsetY = Math.sin(progress * Math.PI * 2 + Math.PI) * 0.165; // было 0.055
                    break;
            }
            
            const currentTransform = cloud.style.transform || 'translate(0px, 0px)';
            const matches = currentTransform.match(/translate\(([^,]+),\s*([^)]+)\)/);
            
            let currentX = 0;
            let currentY = 0;
            
            if (matches) {
                currentX = parseFloat(matches[1]);
                currentY = parseFloat(matches[2]);
            }
            
            cloud.style.transform = `translate(${currentX}px, ${currentY + offsetY}px)`;
            
            cloudAnimations[index] = requestAnimationFrame(animate);
        }
        
        setTimeout(() => {
            cloudAnimations[index] = requestAnimationFrame(animate);
        }, Math.random() * 8000);
    });
}

// ===== СОЗДАНИЕ ЗВЕЗД - РАВНОМЕРНОЕ ХАОТИЧНОЕ РАСПРЕДЕЛЕНИЕ ПО ВСЕМУ ЭКРАНУ =====
function createStars() {
    const container = document.getElementById('backgroundContainer');
    const starCount = 60;

    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        
        const size = Math.random() * 8 + 4;
        star.style.width = size + 'px';
        star.style.height = size + 'px';
        
        const left = Math.random() * 100;
        const top = Math.random() * 100;
        
        star.style.left = left + '%';
        star.style.top = top + '%';
        
        star.dataset.parallax = (Math.random() * 0.5 + 0.1).toFixed(2);
        star.style.animationDelay = (Math.random() * 10) + 's';
        
        container.appendChild(star);
    }
}

// ===== ПРОСТОЕ СОЗДАНИЕ ОБЛАКА БЕЗ ПРОВЕРКИ КОЛЛИЗИЙ =====
function createCloudSimple(container, leftPercent, topPercent, size, cloudPositions) {
    let width, height, bubbleSize, bubblesCount, blurAmount;
    
    if (size === 'large') {
        width = (Math.random() * 400 + 300) * 1.2;
        height = (Math.random() * 300 + 200) * 1.2;
        bubbleSize = 15 + Math.random() * 25;
        bubblesCount = Math.floor(Math.random() * 5) + 8;
        blurAmount = (6 + Math.random() * 4) * 0.9;
    } else {
        width = (Math.random() * 200 + 150) * 1.2;
        height = (Math.random() * 150 + 100) * 1.2;
        bubbleSize = 8 + Math.random() * 12;
        bubblesCount = Math.floor(Math.random() * 3) + 4;
        blurAmount = (4 + Math.random() * 3) * 1.2;
    }
    
    const left = leftPercent + Math.random() * 3 - 1.5;
    const top = topPercent + Math.random() * 3 - 1.5;
    
    createCloud(container, left, top, size, width, height, bubbleSize, bubblesCount, blurAmount);
    
    // Записываем позицию для будущих проверок
    const screenWidth = window.innerWidth || 1920;
    const screenHeight = window.innerHeight || 1080;
    
    cloudPositions.push({
        left: (left / 100) * screenWidth,
        top: (top / 100) * screenHeight,
        right: (left / 100) * screenWidth + width,
        bottom: (top / 100) * screenHeight + height
    });
}

// ===== ПРОВЕРКА ПЕРЕСЕЧЕНИЯ С МЯГКОЙ ТОЛЕРАНТНОСТЬЮ =====
function isOverlappingTooMuch(rect1, rect2) {
    // Проверяем только сильное пересечение (более 60% площади)
    const overlapLeft = Math.max(rect1.left, rect2.left);
    const overlapTop = Math.max(rect1.top, rect2.top);
    const overlapRight = Math.min(rect1.right, rect2.right);
    const overlapBottom = Math.min(rect1.bottom, rect2.bottom);
    
    if (overlapLeft < overlapRight && overlapTop < overlapBottom) {
        const overlapArea = (overlapRight - overlapLeft) * (overlapBottom - overlapTop);
        const rect1Area = (rect1.right - rect1.left) * (rect1.bottom - rect1.top);
        const overlapRatio = overlapArea / rect1Area;
        
        return overlapRatio > 0.6; // Только если пересечение больше 60%
    }
    
    return false;
}

// ===== ФУНКЦИЯ СОЗДАНИЯ ОБЛАКА С МЯГКОЙ ПРОВЕРКОЙ КОЛЛИЗИЙ =====
function createCloudWithSoftCollisionCheck(container, leftPercent, topPercent, size, cloudPositions) {
    let width, height;
    
    if (size === 'large') {
        width = (Math.random() * 400 + 300) * 1.2;
        height = (Math.random() * 300 + 200) * 1.2;
    } else {
        width = (Math.random() * 200 + 150) * 1.2;
        height = (Math.random() * 150 + 100) * 1.2;
    }
    
    const left = leftPercent + Math.random() * 3 - 1.5;
    const top = topPercent + Math.random() * 3 - 1.5;
    
    // Вычисляем прямоугольник нового облака
    const screenWidth = window.innerWidth || 1920;
    const screenHeight = window.innerHeight || 1080;
    
    const newCloudRect = {
        left: (left / 100) * screenWidth,
        top: (top / 100) * screenHeight,
        right: (left / 100) * screenWidth + width,
        bottom: (top / 100) * screenHeight + height
    };
    
    // Проверяем только сильное пересечение
    for (let existingRect of cloudPositions) {
        if (isOverlappingTooMuch(newCloudRect, existingRect)) {
            return false; // Сильно пересекается, не создаем
        }
    }
    
    // Если пересечение допустимое, создаем облако
    createCloudSimple(container, leftPercent, topPercent, size, cloudPositions);
    
    return true;
}

// ===== СОЗДАНИЕ КРАСИВЫХ ОБЛАКОВ (ИСПРАВЛЕННОЕ РАСПРЕДЕЛЕНИЕ) =====
// ===== СОЗДАНИЕ КРАСИВЫХ ОБЛАКОВ (ПРАВИЛЬНОЕ РАВНОМЕРНОЕ РАСПРЕДЕЛЕНИЕ) =====
// ===== СОЗДАНИЕ КРАСИВЫХ ОБЛАКОВ (ЕЩЕ БОЛЬШЕ ВЛЕВО) =====
function createSVGClouds() {
    const container = document.getElementById('backgroundContainer');
    const cloudPositions = []; // Массив для отслеживания занятых позиций
    
    // СДВИГАЕМ ВСЕ ГРАНИЦЫ ЛЕВЕЕ
    const zones = [
        // ЗА ЭКРАНОМ СВЕРХУ - сдвигаем левее
        { left: [-10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], top: [-15, -12, -18, -8, -20, -10, -16, -6, -14, -11, -17, -13] },
        // ВЕРХ-ЛЕВО - еще больше за левую границу
        { left: [-15, -10, -5, 3, 11, 19, 27, 35], top: [5, 15, 25, 35, 45, 10, 20, 30] },
        // ВЕРХ-ПРАВО - начинаем раньше, но тоже за правую границу  
        { left: [55, 63, 71, 79, 87, 95, 103, 110], top: [5, 15, 25, 35, 45, 10, 20, 30] },
        // НИЗ-ЛЕВО - еще больше за левую границу
        { left: [-15, -10, -5, 3, 11, 19, 27, 35], top: [60, 70, 80, 90, 95, 65, 75, 85] },
        // НИЗ-ПРАВО - начинаем раньше
        { left: [55, 63, 71, 79, 87, 95, 103, 110], top: [60, 70, 80, 90, 95, 65, 75, 85] },
        // ЦЕНТР - сдвигаем левее
        { left: [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70], top: [25, 30, 35, 40, 45, 50, 55, 35, 45, 25, 55] }
    ];

    // Создаем КРУПНЫЕ облака
    zones.forEach((zone, zoneIndex) => {
        let cloudCount;
        switch(zoneIndex) {
            case 0: cloudCount = 12; break; // За экраном больше
            case 5: cloudCount = 11; break; // В центре много
            default: cloudCount = 8; break; // В углах по 8
        }
        
        for (let i = 0; i < cloudCount && i < zone.left.length && i < zone.top.length; i++) {
            createCloudSimple(container, zone.left[i], zone.top[i], 'large', cloudPositions);
        }
    });

    // МАЛЕНЬКИЕ облачки - тоже сдвигаем левее
    const smallCloudsCount = 40;
    
    for (let i = 0; i < smallCloudsCount; i++) {
        let attempts = 0;
        let placed = false;
        
        while (attempts < 15 && !placed) {
            // Сдвигаем диапазон левее: от -20% до 110%
            const randomLeft = Math.random() * 130 - 20; // от -20 до 110
            const randomTop = Math.random() * 140 - 25; // от -25% до 115%
            
            if (createCloudWithSoftCollisionCheck(container, randomLeft, randomTop, 'small', cloudPositions)) {
                placed = true;
            }
            attempts++;
        }
        
        // Если не смогли разместить с проверкой, размещаем принудительно
        if (!placed) {
            const randomLeft = Math.random() * 130 - 20; // от -20 до 110
            const randomTop = Math.random() * 140 - 25; // от -25% до 115%
            createCloudSimple(container, randomLeft, randomTop, 'small', cloudPositions);
        }
    }
}
// ===== ФУНКЦИЯ СОЗДАНИЯ ОДНОГО ОБЛАКА =====
function createCloud(container, leftPercent, topPercent, size, width, height, bubbleSize, bubblesCount, blurAmount) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add('svg-cloud');
    
    svg.setAttribute('viewBox', '0 0 200 200');
    svg.style.width = width + 'px';
    svg.style.height = height + 'px';
    
    svg.style.left = leftPercent + '%';
    svg.style.top = topPercent + '%';
    
    // Создаем фильтр размытия для каждого облака
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    const filter = document.createElementNS("http://www.w3.org/2000/svg", "filter");
    const filterId = `blur-${Math.random().toString(36).substr(2, 9)}`;
    filter.setAttribute('id', filterId);
    
    const gaussianBlur = document.createElementNS("http://www.w3.org/2000/svg", "feGaussianBlur");
    gaussianBlur.setAttribute('stdDeviation', blurAmount);
    
    filter.appendChild(gaussianBlur);
    defs.appendChild(filter);
    svg.appendChild(defs);
    
    // Создаем КУЧЕВОЕ облако из пушистых "пузырей"
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute('filter', `url(#${filterId})`);
    
    // Основа облака - большой эллипс
    const mainEllipse = document.createElementNS("http://www.w3.org/2000/svg", "ellipse");
    mainEllipse.setAttribute('cx', '100');
    mainEllipse.setAttribute('cy', '120');
    
    if (size === 'large') {
        mainEllipse.setAttribute('rx', '45');
        mainEllipse.setAttribute('ry', '25');
    } else {
        mainEllipse.setAttribute('rx', '30');
        mainEllipse.setAttribute('ry', '18');
    }
    
    mainEllipse.setAttribute('fill', 'white');
    mainEllipse.setAttribute('opacity', '0.85');
    g.appendChild(mainEllipse);
    
    // Создаем пушистые "пузыри" для объема
    for (let j = 0; j < bubblesCount; j++) {
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        
        // Позиция пузыря относительно центра
        const bubbleX = 70 + Math.random() * 60;
        const bubbleY = 90 + Math.random() * 40;
        
        // Создаем круглый "пузырь" с выпуклостями
        const bumpsCount = 6 + Math.floor(Math.random() * 3);
        let pathData = '';
        
        for (let k = 0; k < bumpsCount; k++) {
            const angle = (k / bumpsCount) * Math.PI * 2;
            const nextAngle = ((k + 1) / bumpsCount) * Math.PI * 2;
            
            // Радиус с вариациями для пушистости
            const radius1 = bubbleSize + Math.random() * 8 - 4;
            const radius2 = bubbleSize + Math.random() * 8 - 4;
            
            const x1 = bubbleX + Math.cos(angle) * radius1;
            const y1 = bubbleY + Math.sin(angle) * radius1;
            const x2 = bubbleX + Math.cos(nextAngle) * radius2;
            const y2 = bubbleY + Math.sin(nextAngle) * radius2;
            
            // Контрольные точки для плавных выпуклостей
            const controlRadius = bubbleSize + Math.random() * 6 + 2;
            const cp1X = bubbleX + Math.cos(angle + 0.3) * controlRadius;
            const cp1Y = bubbleY + Math.sin(angle + 0.3) * controlRadius;
            const cp2X = bubbleX + Math.cos(nextAngle - 0.3) * controlRadius;
            const cp2Y = bubbleY + Math.sin(nextAngle - 0.3) * controlRadius;
            
            if (k === 0) {
                pathData = `M ${x1} ${y1}`;
            }
            
            pathData += ` C ${cp1X} ${cp1Y}, ${cp2X} ${cp2Y}, ${x2} ${y2}`;
        }
        
        pathData += ' Z';
        
        path.setAttribute('d', pathData);
        path.setAttribute('fill', 'white');
        path.setAttribute('opacity', Math.random() * 0.25 + 0.65);
        
        g.appendChild(path);
    }
    
    svg.appendChild(g);
    svg.dataset.parallax = (Math.random() * 0.5 + 0.1).toFixed(2);
    
    container.appendChild(svg);
}

// ===== ОБНОВЛЕНИЕ ПОЗИЦИЙ ЭЛЕМЕНТОВ ПРИ ДВИЖЕНИИ МЫШИ =====
function updateParallax() {
    const stars = document.querySelectorAll('.star');
    const clouds = document.querySelectorAll('.svg-cloud');
    
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;
    
    const deltaX = (mouseX - centerX) / centerX;
    const deltaY = (mouseY - centerY) / centerY;

    if (isMouseMoving) {
        stars.forEach((star, index) => {
            star.classList.remove('floating');
            if (starAnimations[index]) {
                cancelAnimationFrame(starAnimations[index]);
            }
            
            const parallax = parseFloat(star.dataset.parallax);
            const moveX = deltaX * parallax * 50;
            const moveY = deltaY * parallax * 50;
            star.style.transform = `translate(${moveX}px, ${moveY}px)`;
        });

        clouds.forEach((cloud, index) => {
            cloud.classList.remove('floating');
            if (cloudAnimations[index]) {
                cancelAnimationFrame(cloudAnimations[index]);
            }
            
            const parallax = parseFloat(cloud.dataset.parallax);
            const moveX = deltaX * parallax * 50;
            const moveY = deltaY * parallax * 50;
            cloud.style.transform = `translate(${moveX}px, ${moveY}px)`;
        });
    }
}

// ===== СБРОС ПОЗИЦИЙ ПРИ ОСТАНОВКЕ МЫШИ =====
function resetParallax() {
    const stars = document.querySelectorAll('.star');
    const clouds = document.querySelectorAll('.svg-cloud');
    
    stars.forEach(star => {
        setTimeout(() => {
            star.classList.add('floating');
        }, 300);
    });

    setTimeout(animateStars, 500);

    clouds.forEach(cloud => {
        setTimeout(() => {
            cloud.classList.add('floating');
        }, 300);
    });

    setTimeout(animateClouds, 500);
}

// ===== ПЕРЕКЛЮЧЕНИЕ ТЕМЫ С ОБНОВЛЕНИЕМ ИКОНОК =====
function toggleTheme() {
    const body = document.body;
    const moonIcon = document.querySelector('.theme-icon.moon');
    const sunIcon = document.querySelector('.theme-icon.sun');
    
    isDark = !isDark;
    
    if (isDark) {
        body.className = 'theme-dark';
        moonIcon.classList.add('active');
        sunIcon.classList.remove('active');
    } else {
        body.className = 'theme-light';
        moonIcon.classList.remove('active');
        sunIcon.classList.add('active');
    }
}

// ===== ОБРАБОТКА ДВИЖЕНИЯ МЫШИ =====
document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    isMouseMoving = true;
    
    updateParallax();
    
    clearTimeout(mouseTimeout);
    mouseTimeout = setTimeout(() => {
        isMouseMoving = false;
        resetParallax();
    }, 1500);
});

// ===== ИНИЦИАЛИЗАЦИЯ =====
createStars();
createSVGClouds();

// Начальная анимация
setTimeout(() => {
    if (!isMouseMoving) {
        resetParallax();
    }
}, 100);