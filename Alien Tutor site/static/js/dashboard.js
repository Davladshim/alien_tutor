// ===== ЛОГИКА ПЕРЕКЛЮЧЕНИЯ ВКЛАДОК =====

document.addEventListener('DOMContentLoaded', function() {
    // Получаем все кнопки вкладок и контент
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    // Функция переключения вкладок
    function switchTab(targetTabId) {
        // Убираем активный класс со всех кнопок
        tabButtons.forEach(button => {
            button.classList.remove('active');
        });

        // Скрываем весь контент вкладок
        tabContents.forEach(content => {
            content.classList.remove('active');
        });

        // Активируем нужную кнопку
        const activeButton = document.querySelector(`[data-tab="${targetTabId}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }

        // Показываем нужный контент
        const activeContent = document.getElementById(`${targetTabId}-tab`);
        if (activeContent) {
            activeContent.classList.add('active');
        }
    }

    // Добавляем обработчики событий на кнопки
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            switchTab(targetTab); // ← ДОБАВЬ ЭТУ СТРОКУ!
        });
    });

    // Функция для плавного появления контента (опционально)
    function initTabAnimations() {
        tabContents.forEach(content => {
            content.style.opacity = '0';
            content.style.transform = 'translateY(20px)';
            content.style.transition = 'all 0.3s ease';
        });

        // Показываем активную вкладку
        const activeContent = document.querySelector('.tab-content.active');
        if (activeContent) {
            setTimeout(() => {
                activeContent.style.opacity = '1';
                activeContent.style.transform = 'translateY(0)';
            }, 100);
        }
    }

    // Обновляем анимацию при переключении
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            setTimeout(() => {
                const activeContent = document.querySelector('.tab-content.active');
                if (activeContent) {
                    activeContent.style.opacity = '1';
                    activeContent.style.transform = 'translateY(0)';
                }
            }, 50);
        });
    });

    // Инициализируем анимации
    initTabAnimations();

    // Дополнительно: сохранение активной вкладки (опционально)
    // Можно раскомментировать, если нужно запоминать последнюю открытую вкладку
    /*
    function saveActiveTab(tabId) {
        sessionStorage.setItem('activeTab', tabId);
    }

    function loadActiveTab() {
        const savedTab = sessionStorage.getItem('activeTab');
        if (savedTab) {
            switchTab(savedTab);
        }
    }

    // Сохраняем при переключении
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            saveActiveTab(targetTab);
        });
    });

    // Загружаем при открытии страницы
    loadActiveTab();
    */
});

// ===== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ (для будущего использования) =====

// Функция для программного переключения вкладки (можно вызвать из консоли)
function goToTab(tabName) {
    const button = document.querySelector(`[data-tab="${tabName}"]`);
    if (button) {
        button.click();
    }
}

// Функция для получения текущей активной вкладки
function getCurrentTab() {
    const activeButton = document.querySelector('.tab-button.active');
    return activeButton ? activeButton.getAttribute('data-tab') : null;
}

// ===== ИНТЕГРАЦИЯ С ВИДЖЕТОМ РАСПИСАНИЯ =====

// Загрузка данных расписания
function loadScheduleData() {
    const loadingDiv = document.getElementById('schedule-loading');
    const contentDiv = document.getElementById('schedule-content');
    const errorDiv = document.getElementById('schedule-error');
    
    // Показываем загрузку
    loadingDiv.style.display = 'block';
    contentDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    
    // Получаем текущую неделю
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentWeek = getWeekNumber(now);
    
    // URL для получения данных (как в виджете)
    const apiUrl = `/proxy-schedule/${currentYear}/${currentWeek}`;
    
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
            renderSchedule(data);
        })
        .catch(error => {
            console.error('Ошибка загрузки расписания:', error);
            loadingDiv.style.display = 'none';
            errorDiv.style.display = 'block';
            errorDiv.innerHTML = `
                <p>Не удалось загрузить расписание</p>
                <button onclick="loadScheduleData()" class="retry-btn">Попробовать снова</button>
            `;
        });
}

// Функция получения номера недели (как в виджете)
function getWeekNumber(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(),0,1));
    return Math.ceil((((d - yearStart) / 86400000) + 1)/7);
}

// Отрисовка расписания
function renderSchedule(data) {
    // Ищем сетку расписания в HTML
    const scheduleGrid = document.querySelector('.schedule-grid');
    
    if (!scheduleGrid) {
        console.error('Элемент .schedule-grid не найден');
        return;
    }
    
    if (!data || !data.week_data) {
        scheduleGrid.innerHTML = '<p>Нет данных для отображения</p>';
        return;
    }
    
    // Обновляем название только в недельном режиме
    if (currentViewMode === 'week') {
        const currentPeriod = document.getElementById('currentPeriod');
        if (currentPeriod && data.week_info) {
            currentPeriod.textContent = data.week_info.title;
        }
    }
    
    // Очищаем и заполняем сетку
    let html = '';
    
    data.week_data.forEach(day => {
        const todayClass = day.is_today ? 'today' : '';
        
        html += `
            <div class="day-column ${todayClass}">
                <div class="day-header">
                    <div class="day-name">${day.day_name}</div>
                    <div class="day-date">${day.day_number}</div>
                    ${day.is_today ? '<div class="today-badge">Сегодня</div>' : ''}
                </div>
                <div class="lessons-list">
        `;
        
        if (day.lessons && day.lessons.length > 0) {
            day.lessons.forEach(lesson => {
                html += `
                    <div class="lesson-item-placeholder">
                        <div class="lesson-time">${lesson.time}</div>
                        <div class="lesson-subject">${lesson.subject}</div>
                        ${lesson.status === 'cancelled' ? '<div class="lesson-status">Отменен</div>' : ''}
                    </div>
                `;
            });
        } else {
            html += '<div class="lesson-placeholder">Нет занятий</div>';
        }
        
        html += `
                </div>
            </div>
        `;
    });
    
    scheduleGrid.innerHTML = html;
}

// Загрузка расписания при переключении на вкладку
function initScheduleHandlers() {
    const scheduleButton = document.querySelector('[data-tab="schedule"]');
    if (scheduleButton) {
        scheduleButton.addEventListener('click', function() {
            // Загружаем данные только при первом открытии вкладки
            const contentDiv = document.getElementById('schedule-content');
            if (contentDiv && contentDiv.innerHTML.trim() === '') {
                setTimeout(() => {
                    loadScheduleData();
                }, 100); // Небольшая задержка для плавности
            }
        });
    }
}

// Вызываем инициализацию сразу
initScheduleHandlers();

// Функция для принудительного обновления расписания
function refreshSchedule() {
    const scheduleTab = document.getElementById('schedule-tab');
    if (scheduleTab && scheduleTab.classList.contains('active')) {
        loadScheduleData();
    }
}

// ИСПРАВЛЕННАЯ ИНИЦИАЛИЗАЦИЯ - добавляем в существующий DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Ждем немного чтобы все загрузилось
    setTimeout(function() {
        const scheduleButton = document.querySelector('[data-tab="schedule"]');
        if (scheduleButton) {
            scheduleButton.addEventListener('click', function() {
                console.log('Кнопка расписания нажата!'); // Для отладки
                setTimeout(() => {
                    loadScheduleData();
                }, 200);
            });
            console.log('Обработчик расписания добавлен!'); // Для отладки
        } else {
            console.log('Кнопка расписания не найдена!'); // Для отладки
        }
    }, 500);
});

// ===== ДИАГРАММЫ УСПЕВАЕМОСТИ =====

// Данные для разных классов
const progressData = {
    '9': {
        hasExamScores: true,
        chartType: 'single', // одинарная диаграмма
        examScores: [
            { date: '29.01', score: 92 },
            { date: '01.02', score: 58 },
            { date: '03.02', score: 72 },
            { date: '05.02', score: 85 }
        ],
        topicProgress: { fully: 65, questions: 25, needWork: 10 },
        homeworkData: [
            { date: '06.02.2025', primary: 45, secondary: 89, solved: '18/20', grade: 5 },
            { date: '04.02.2025', primary: 38, secondary: 76, solved: '15/20', grade: 4 },
            { date: '02.02.2025', primary: 29, secondary: 58, solved: '12/20', grade: 3 }
        ]
    },
    '11': {
        hasExamScores: true,
        chartType: 'single',
        examScores: [
            { date: '28.01', score: 76 },
            { date: '30.01', score: 82 },
            { date: '02.02', score: 68 },
            { date: '04.02', score: 89 },
            { date: '06.02', score: 91 }
        ],
        topicProgress: { fully: 70, questions: 20, needWork: 10 },
        homeworkData: [
            { date: '05.02.2025', primary: 52, secondary: 95, solved: '19/20', grade: 5 },
            { date: '03.02.2025', primary: 41, secondary: 82, solved: '16/20', grade: 4 }
        ]
    },
    '8': {
        hasExamScores: false,
        chartType: 'double', // двойная диаграмма
        topicProgress: { fully: 55, questions: 30, needWork: 15 },
        doubleScores: [
            { date: '05.02', design: 85, solution: 90 },
            { date: '03.02', design: 70, solution: 80 },
            { date: '01.02', design: 60, solution: 75 },
            { date: '30.01', design: 80, solution: 85 }
        ],
        homeworkData: [
            { date: '06.02.2025', design: 4, solution: 5, topic: 'Квадратные уравнения', assigned: 8, solved: '7/8' },
            { date: '04.02.2025', design: 3, solution: 4, topic: 'Функции', assigned: 6, solved: '5/6' }
        ]
    },
    '7': {
        hasExamScores: false,
        chartType: 'double',
        topicProgress: { fully: 60, questions: 25, needWork: 15 },
        doubleScores: [
            { date: '04.02', design: 75, solution: 85 },
            { date: '02.02', design: 80, solution: 70 },
            { date: '31.01', design: 65, solution: 80 }
        ],
        homeworkData: [
            { date: '05.02.2025', design: 5, solution: 4, topic: 'Пропорции', assigned: 10, solved: '9/10' }
        ]
    },
    '10': {
        hasExamScores: false,
        chartType: 'double',
        topicProgress: { fully: 65, questions: 20, needWork: 15 },
        doubleScores: [
            { date: '06.02', design: 90, solution: 85 },
            { date: '04.02', design: 75, solution: 80 },
            { date: '02.02', design: 85, solution: 90 }
        ],
        homeworkData: [
            { date: '07.02.2025', design: 5, solution: 5, topic: 'Тригонометрия', assigned: 5, solved: '5/5' }
        ]
    }
};

// Инициализация диаграмм при загрузке
document.addEventListener('DOMContentLoaded', function() {
    initProgressCharts();
    updateChartsForClass(currentClass);
    
    // Обработчики кнопок классов
    const classButtons = document.querySelectorAll('.class-btn');
    classButtons.forEach(button => {
        button.addEventListener('click', function() {
            const newClass = this.getAttribute('data-class');
            if (newClass !== currentClass) {
                // Обновляем активную кнопку
                classButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // Обновляем класс и диаграммы
                currentClass = newClass;
                updateChartsForClass(currentClass);
            }
        });
    });
});

// Инициализация структуры диаграмм
function initProgressCharts() {
    console.log('Инициализация диаграмм успеваемости');
}

// Обновление диаграмм для выбранного класса
function updateChartsForClass(classNum) {
    const data = progressData[classNum];
    const chartsContainer = document.querySelector('.charts-container');
    const barChartSection = document.querySelector('.bar-chart-section');
    const scoreColumns = document.querySelectorAll('.score-column, .score-cell');
    const barChartTitle = document.querySelector('.bar-chart-section h3');
    
    if (data.hasExamScores) {
        // Показываем столбчатую диаграмму для 9-11 классов
        barChartSection.classList.remove('hidden');
        chartsContainer.classList.remove('single-chart');
        scoreColumns.forEach(col => col.classList.remove('hidden'));
        
        // Обновляем заголовок
        if (barChartTitle) {
            barChartTitle.textContent = 'Баллы за пробники ОГЭ/ЕГЭ';
        }
        
        renderBarChart(data.examScores);
    } else {
        // Показываем двойную столбчатую диаграмму для 7, 8, 10 классов
        barChartSection.classList.remove('hidden');
        chartsContainer.classList.remove('single-chart');
        scoreColumns.forEach(col => col.classList.add('hidden'));
        
        // Обновляем заголовок
        if (barChartTitle) {
            barChartTitle.textContent = 'Оценки: Оформление и Решение';
        }
        
        renderDoubleBarChart(data.doubleScores);
    }
    
    // Обновляем круговую диаграмму на основе реальных данных из таблицы
    const realProgress = calculateProgressFromTable();
    renderPieChart(realProgress);

    // Также обновляем таблицу домашних заданий
    updateHomeworkTable(classNum);
}

// Обновление таблицы домашних заданий
function updateHomeworkTable(classNum) {
    // Если classNum не передан, берем из window.studentData
    if (!classNum && window.studentData) {
        classNum = window.studentData.currentClass;
    }
    
    const headerElement = document.getElementById('homeworkTableHeader');
    const bodyElement = document.getElementById('homeworkTableBody');
    
    if (!headerElement || !bodyElement) return;
    
    // Очищаем таблицу
    headerElement.innerHTML = '';
    bodyElement.innerHTML = '';
    
    // Определяем, есть ли экзамены для этого класса
    const hasExamScores = (classNum === '9' || classNum === '11');
    
    // Получаем реальные данные из window.studentData
    const homeworkData = window.studentData ? window.studentData.homework : [];
    
    if (hasExamScores) {
        // Заголовки для 9 и 11 классов (пробники)
        headerElement.innerHTML = `
            <tr>
                <th>Дата домашнего задания</th>
                <th>Тема</th>
                <th>Первичные баллы за пробник</th>
                <th>Вторичные баллы за пробник</th>
                <th>Количество решенных заданий</th>
            </tr>
        `;
    } else {
        // Заголовки для 7, 8, 10 классов (обычные задания) - БЕЗ "Сколько задач было задано"
        headerElement.innerHTML = `
            <tr>
                <th>Дата домашнего задания</th>
                <th>Оформление</th>
                <th>Решение</th>
                <th>Тема</th>
                <th>Сколько решено из них</th>
            </tr>
        `;
    }
    
    // Заполняем данными из БД
    if (homeworkData && homeworkData.length > 0) {
        homeworkData.forEach(homework => {
            const row = document.createElement('tr');
            
            if (hasExamScores) {
                row.innerHTML = `
                    <td>${homework.date}</td>
                    <td>${homework.topic || ''}</td>
                    <td class="score-cell">${homework.primary_score || ''}</td>
                    <td class="score-cell">${homework.secondary_score || ''}</td>
                    <td>${homework.tasks_solved || ''}/${homework.tasks_assigned || ''}</td>
                `;
            } else {
                row.innerHTML = `
                    <td>${homework.date}</td>
                    <td class="score-cell">${homework.design_score || ''}</td>
                    <td class="score-cell">${homework.solution_score || ''}</td>
                    <td>${homework.topic || ''}</td>
                    <td>${homework.tasks_solved || ''}/${homework.tasks_assigned || ''}</td>
                `;
            }
            
            bodyElement.appendChild(row);
        });
    } else {
        // Если данных нет - показываем сообщение
        bodyElement.innerHTML = '<tr><td colspan="5" style="text-align: center; font-style: italic; color: var(--text-muted);">Нет данных о домашних заданиях</td></tr>';
    }
}

// Функция для подсчета данных из таблицы
function calculateProgressFromTable() {
    const tableRows = document.querySelectorAll('#lessonsTableBody tr');
    let fullyCount = 0;
    let questionsCount = 0;
    let needWorkCount = 0;
    
    tableRows.forEach(row => {
        const conclusionCell = row.cells[2]; // Столбец "Краткий вывод" (индекс 2)
        if (conclusionCell) {
            const conclusion = conclusionCell.textContent.trim();
            
            if (conclusion === 'Тема разобрана полностью') {
                fullyCount++;
            } else if (conclusion === 'Есть вопросы по теме') {
                questionsCount++;
            } else if (conclusion === 'Тему нужно закрепить') {
                needWorkCount++;
            }
        }
    });
    
    const total = fullyCount + questionsCount + needWorkCount;
    
    if (total === 0) {
        return { fully: 0, questions: 0, needWork: 0 };
    }
    
    return {
        fully: Math.round((fullyCount / total) * 100),
        questions: Math.round((questionsCount / total) * 100),
        needWork: Math.round((needWorkCount / total) * 100)
    };
}

// Отрисовка двойной столбчатой диаграммы для 7, 8, 10 классов
function renderDoubleBarChart(scores) {
    // Если scores не переданы, берем из window.studentData
    if (!scores && window.studentData) {
        scores = window.studentData.homework;
    }
    
    const barChart = document.getElementById('barChart');
    
    if (!barChart) return;
    
    // Очищаем предыдущие столбцы
    barChart.innerHTML = '';
    barChart.className = 'double-bar-chart chart-with-scale'; // Добавляем класс для шкалы
    
    // Если нет данных - показываем сообщение
    if (!scores || scores.length === 0) {
        barChart.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 50px;">Нет данных о домашних заданиях</div>';
        return;
    }
    
    console.log('🔍 ОТЛАДКА: Данные для двойной диаграммы:', scores);
    
    // Находим максимальное значение среди РЕАЛЬНЫХ данных
    let maxDesignScore = 0;
    let maxSolutionScore = 0;
    
    scores.forEach(scoreData => {
        const designScore = parseInt(scoreData.design_score) || 0;
        const solutionScore = parseInt(scoreData.solution_score) || 0;
        
        if (designScore > maxDesignScore) maxDesignScore = designScore;
        if (solutionScore > maxSolutionScore) maxSolutionScore = solutionScore;
    });
    
    // Используем фиксированную шкалу от 0 до 10 для удобства
    const maxScore = 10;
    const chartHeight = 220;
    
    console.log(`📊 Используем шкалу от 0 до ${maxScore}`);
    
    // Создаем вертикальную шкалу
    const verticalScale = document.createElement('div');
    verticalScale.className = 'vertical-scale';
    
    // Создаем деления от 0 до 10
    for (let i = 0; i <= maxScore; i++) {
        const scaleMark = document.createElement('div');
        scaleMark.className = 'scale-mark';
        
        // Позиционируем деление (снизу вверх)
        const positionFromBottom = (i / maxScore) * chartHeight;
        scaleMark.style.bottom = positionFromBottom + 'px';
        
        // Добавляем подпись
        const scaleLabel = document.createElement('div');
        scaleLabel.className = 'scale-label';
        scaleLabel.textContent = i;
        scaleMark.appendChild(scaleLabel);
        
        verticalScale.appendChild(scaleMark);
    }
    
    barChart.appendChild(verticalScale);
    
    // Создаем столбцы
    scores.forEach(scoreData => {
        const barGroup = document.createElement('div');
        barGroup.className = 'double-bar-group';
        
        const designScore = parseInt(scoreData.design_score) || 0;
        const solutionScore = parseInt(scoreData.solution_score) || 0;
        
        // Столбец для оформления (розовый)
        const designBar = document.createElement('div');
        designBar.className = 'double-bar-item design-bar';
        const designHeight = Math.max(10, (designScore / maxScore) * chartHeight);
        designBar.style.height = designHeight + 'px';
        
        // Создаем горизонтальную линию для столбца оформления
        const designGuideLine = document.createElement('div');
        designGuideLine.className = 'horizontal-guide-line';
        designGuideLine.style.top = '0px';
        designBar.appendChild(designGuideLine);
        
        // СТАРЫЙ тултип (как был)
        const designTooltip = document.createElement('div');
        designTooltip.className = 'double-bar-tooltip';
        designTooltip.textContent = `${scoreData.date}: Оформление ${designScore}`;
        designBar.appendChild(designTooltip);
        
        // Столбец для решения (синий)
        const solutionBar = document.createElement('div');
        solutionBar.className = 'double-bar-item solution-bar';
        const solutionHeight = Math.max(10, (solutionScore / maxScore) * chartHeight);
        solutionBar.style.height = solutionHeight + 'px';
        
        // Создаем горизонтальную линию для столбца решения
        const solutionGuideLine = document.createElement('div');
        solutionGuideLine.className = 'horizontal-guide-line';
        solutionGuideLine.style.top = '0px';
        solutionBar.appendChild(solutionGuideLine);
        
        // СТАРЫЙ тултип (как был)
        const solutionTooltip = document.createElement('div');
        solutionTooltip.className = 'double-bar-tooltip';
        solutionTooltip.textContent = `${scoreData.date}: Решение ${solutionScore}`;
        solutionBar.appendChild(solutionTooltip);
        
        barGroup.appendChild(designBar);
        barGroup.appendChild(solutionBar);
        barChart.appendChild(barGroup);
        
        console.log(`📊 Создан столбец: оформление=${designHeight}px (${designScore}/10), решение=${solutionHeight}px (${solutionScore}/10)`);
    });
}

// Отрисовка столбчатой диаграммы
function renderBarChart(scores) {
    // Если scores не переданы, берем из window.studentData
    if (!scores && window.studentData) {
        scores = window.studentData.examResults;
    }
    
    const barChart = document.getElementById('barChart');
    
    if (!barChart) return;
    
    // Очищаем предыдущие столбцы
    barChart.innerHTML = '';
    
    // Если нет данных - показываем сообщение
    if (!scores || scores.length === 0) {
        barChart.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 50px;">Нет данных о пробниках</div>';
        return;
    }
    
    // Находим максимальное значение для масштабирования
    const maxScore = Math.max(...scores.map(s => s.score));
    const chartHeight = 220; // Высота области диаграммы
    
    scores.forEach(scoreData => {
        const barItem = document.createElement('div');
        barItem.className = 'bar-item';
        
        // Вычисляем высоту столбца (минимум 20px)
        const height = Math.max(20, (scoreData.score / 100) * chartHeight);
        barItem.style.height = height + 'px';
        
        // Создаем тултип
        const tooltip = document.createElement('div');
        tooltip.className = 'bar-tooltip';
        tooltip.textContent = `${scoreData.date}: ${scoreData.score} баллов`;
        
        barItem.appendChild(tooltip);
        barChart.appendChild(barItem);
    });
}

// Отрисовка круговой диаграммы в стиле картинки
function renderPieChart(progress) {
    const pieChart = document.querySelector('#pieChart svg');
    
    if (!pieChart) return;
    
    // Очищаем предыдущие сегменты
    pieChart.innerHTML = '';
    
    const total = progress.fully + progress.questions + progress.needWork;
    const center = 100;
    const radius = 85;
    const segmentGap = 0; // Убираем зазор между сегментами
    
    // Цвета в стиле сайта
    const colors = [
        '#5ED9D7', // Основной цвет сайта - для "разобрано полностью"
        '#f472b6', // Розовый - для "есть вопросы"  
        '#60a5fa'  // Голубой - для "нужно закрепить"
    ];
    const values = [progress.fully, progress.questions, progress.needWork];
    const labels = ['Тема разобрана полностью', 'Есть вопросы по теме', 'Тему нужно закрепить'];
        
    let currentAngle = -90; // Начинаем сверху
    
    // Создаем градиенты для 3D эффекта
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    
    colors.forEach((color, index) => {
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
        gradient.setAttribute('id', `gradient-${index}`);
        gradient.setAttribute('cx', '30%');
        gradient.setAttribute('cy', '30%');
        
        const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop1.setAttribute('offset', '0%');
        stop1.setAttribute('stop-color', lightenColor(color, 20));
        
        const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop2.setAttribute('offset', '100%');
        stop2.setAttribute('stop-color', darkenColor(color, 15));
        
        gradient.appendChild(stop1);
        gradient.appendChild(stop2);
        defs.appendChild(gradient);
    });
    
    pieChart.appendChild(defs);
    
    values.forEach((value, index) => {
        if (value > 0) {
            const percentage = value / total;
            const angle = percentage * 360; // Убираем вычитание зазора
            
            // Создаем path для сектора
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            
            const startAngle = (currentAngle * Math.PI) / 180;
            const endAngle = ((currentAngle + angle) * Math.PI) / 180;
            
            const x1 = center + radius * Math.cos(startAngle);
            const y1 = center + radius * Math.sin(startAngle);
            const x2 = center + radius * Math.cos(endAngle);
            const y2 = center + radius * Math.sin(endAngle);
            
            const largeArc = angle > 180 ? 1 : 0;
            
            const pathData = [
                `M ${center} ${center}`,
                `L ${x1} ${y1}`,
                `A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`,
                'Z'
            ].join(' ');
            
            path.setAttribute('d', pathData);
            path.setAttribute('fill', `url(#gradient-${index})`);
            path.setAttribute('stroke', '#ffffff');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('class', 'pie-segment');
            path.setAttribute('data-index', index);
            
            // Добавляем title для тултипа
            const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            title.textContent = `${labels[index]}: ${value}%`;
            path.appendChild(title);
            
            pieChart.appendChild(path);
            
            currentAngle += angle; // Убираем добавление зазора
        }
    });
    
    // Обновляем цвета в легенде
    const legendColors = document.querySelectorAll('.legend-color');
    legendColors.forEach((colorEl, index) => {
        if (colors[index]) {
            colorEl.style.background = colors[index];
        }
    });
}

// Функция осветления цвета
function lightenColor(color, percent) {
    const num = parseInt(color.replace("#", ""), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
        (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
        (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
}

// Функция затемнения цвета
function darkenColor(color, percent) {
    const num = parseInt(color.replace("#", ""), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) - amt;
    const G = (num >> 8 & 0x00FF) - amt;
    const B = (num & 0x0000FF) - amt;
    return "#" + (0x1000000 + (R > 255 ? 255 : R < 0 ? 0 : R) * 0x10000 +
        (G > 255 ? 255 : G < 0 ? 0 : G) * 0x100 +
        (B > 255 ? 255 : B < 0 ? 0 : B)).toString(16).slice(1);
}

// Функция для добавления нового урока в таблицу (сверху)
function addNewLesson(lessonData) {
    const tableBody = document.getElementById('lessonsTableBody');
    if (!tableBody) return;
    
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <td>${lessonData.date}</td>
        <td>${lessonData.topic}</td>
        <td>${lessonData.shortSummary}</td>
        <td class="score-cell ${!progressData[currentClass].hasExamScores ? 'hidden' : ''}">${lessonData.score || '-'}</td>
        <td>${lessonData.fullSummary}</td>
        <td>${lessonData.homework}</td>
    `;
    
    // Добавляем новую строку в начало (сверху)
    tableBody.insertBefore(newRow, tableBody.firstChild);
    
    // Анимация появления
    newRow.style.opacity = '0';
    newRow.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        newRow.style.transition = 'all 0.5s ease';
        newRow.style.opacity = '1';
        newRow.style.transform = 'translateY(0)';
    }, 50);
}

// Пример использования (можно вызвать из консоли для тестирования)
function testAddLesson() {
    addNewLesson({
        date: '08.02.2025',
        topic: 'Тригонометрия',
        shortSummary: 'Отлично усвоено',
        score: 95,
        fullSummary: 'Ученик показал отличное понимание основных тригонометрических функций.',
        homework: 'Решить задачи 15-20'
    });
}

// ===== ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ ПРОСМОТРА (НЕДЕЛЯ/МЕСЯЦ) =====

let currentViewMode = 'week'; // 'week' или 'month'
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth(); // 0-11 (январь = 0)
let currentWeek = getWeekNumber(new Date());

// Инициализация обработчиков режимов просмотра
document.addEventListener('DOMContentLoaded', function() {
    // Ждем немного, чтобы все элементы загрузились
    setTimeout(function() {
        const weekBtn = document.querySelector('.toggle-btn:first-child'); // Кнопка "Неделя"
        const monthBtn = document.querySelector('.toggle-btn:last-child');  // Кнопка "Месяц"
        
        if (weekBtn && monthBtn) {
            console.log('✅ Кнопки переключения найдены!');
            
            // Обработчик кнопки "Неделя"
            weekBtn.addEventListener('click', function() {
                console.log('🗓️ Переключение на режим НЕДЕЛЯ');
                switchToWeekView();
            });
            
            // Обработчик кнопки "Месяц"
            monthBtn.addEventListener('click', function() {
                console.log('📅 Переключение на режим МЕСЯЦ');
                switchToMonthView();
            });
            
        } else {
            console.log('❌ Кнопки переключения не найдены!');
        }
    }, 1000);
});

// Переключение на недельный вид
function switchToWeekView() {
    if (currentViewMode === 'week') {
        console.log('Уже в режиме недели');
        return;
    }
    
    currentViewMode = 'week';
    
    // Обновляем активную кнопку
    updateViewButtons();
    
    // Показываем недельный календарь, скрываем месячный
    const weekGrid = document.querySelector('.schedule-grid');
    const monthCalendar = document.getElementById('monthCalendar');
    
    if (weekGrid) {
        weekGrid.style.display = 'grid';
    }
    
    if (monthCalendar) {
        monthCalendar.classList.remove('active');
    }
    
    // Обновляем заголовки навигации для недельного режима
    updateNavigationForWeek();
    
    console.log('🗓️ Переключено на недельный вид');

    // Обновляем название периода для недельного режима
    updatePeriodTitle();
}

// Переключение на месячный вид
function switchToMonthView() {
    if (currentViewMode === 'month') {
        console.log('Уже в режиме месяца');
        return;
    }
    
    currentViewMode = 'month';
    
    // Обновляем активную кнопку
    updateViewButtons();
    
    // Скрываем недельный календарь, показываем месячный
    const weekGrid = document.querySelector('.schedule-grid');
    const monthCalendar = document.getElementById('monthCalendar');
    
    if (weekGrid) {
        weekGrid.style.display = 'none';
    }
    
    if (monthCalendar) {
        monthCalendar.classList.add('active');
    }
    
    // Загружаем и показываем месячный календарь
    loadMonthCalendar(currentYear, currentMonth);
    
    // Обновляем заголовки навигации для месячного режима
    updateNavigationForMonth();
    
    console.log('📅 Переключено на месячный вид');

    // Обновляем название периода для месячного режима
    updatePeriodTitle();
}

// Обновление активной кнопки
function updateViewButtons() {
    const weekBtn = document.querySelector('.toggle-btn:first-child');
    const monthBtn = document.querySelector('.toggle-btn:last-child');
    
    if (weekBtn && monthBtn) {
        // Убираем активный класс у обеих кнопок
        weekBtn.classList.remove('active');
        monthBtn.classList.remove('active');
        
        // Добавляем активный класс к нужной кнопке
        if (currentViewMode === 'week') {
            weekBtn.classList.add('active');
        } else {
            monthBtn.classList.add('active');
        }
        
        console.log(`Активная кнопка: ${currentViewMode}`);
    }
}

// Обновление навигации для недельного режима
function updateNavigationForWeek() {
    const prevBtn = document.getElementById('prevWeekBtn');
    const nextBtn = document.getElementById('nextWeekBtn');
    
    if (prevBtn && nextBtn) {
        prevBtn.textContent = '← Назад';
        nextBtn.textContent = 'Вперед →';
    }
}

// Обновление навигации для месячного режима  
function updateNavigationForMonth() {
    const prevBtn = document.getElementById('prevWeekBtn');
    const nextBtn = document.getElementById('nextWeekBtn');
    
    if (prevBtn && nextBtn) {
        prevBtn.textContent = '← Предыдущий месяц';
        nextBtn.textContent = 'Следующий месяц →';
    }
}

// Загрузка месячного календаря
function loadMonthCalendar(year, month) {
    console.log(`📅 Загружаем календарь: ${getMonthName(month)} ${year}`);
    
    // Создаем календарную сетку
    createMonthGrid(year, month);
    
    // Загружаем данные уроков для всего месяца
    loadMonthLessons(year, month);

    // Обновляем название периода
    updatePeriodTitle();
}

// Создание календарной сетки 7x6
function createMonthGrid(year, month) {
    const monthGrid = document.getElementById('monthGrid');
    if (!monthGrid) return;
    
    // Находим все ячейки дней (не заголовки)
    const existingDayCells = monthGrid.querySelectorAll('.month-day-cell');
    existingDayCells.forEach(cell => cell.remove());
    
    // Вычисляем первый день месяца и количество дней
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    
    // Первый день недели (0=воскресенье, 1=понедельник, ...)
    // Преобразуем в нашу систему (0=понедельник)
    let firstDayOfWeek = firstDay.getDay();
    firstDayOfWeek = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;
    
    // Вычисляем предыдущий месяц
    const prevMonth = month === 0 ? 11 : month - 1;
    const prevYear = month === 0 ? year - 1 : year;
    const daysInPrevMonth = new Date(prevYear, prevMonth + 1, 0).getDate();
    
    // Сегодняшняя дата для подсветки
    const today = new Date();
    const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
    const todayDate = today.getDate();
    
    console.log(`📅 Создаем сетку: ${daysInMonth} дней, начинается с ${firstDayOfWeek} дня недели`);
    
    // Создаем 42 ячейки (7x6 = максимум недель в месяце)
    for (let i = 0; i < 42; i++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'month-day-cell';
        
        let dayNumber, cellMonth, cellYear, isCurrentMonthDay;
        
        if (i < firstDayOfWeek) {
            // Дни предыдущего месяца
            dayNumber = daysInPrevMonth - firstDayOfWeek + i + 1;
            cellMonth = prevMonth;
            cellYear = prevYear;
            isCurrentMonthDay = false;
            dayCell.classList.add('other-month');
        } else if (i < firstDayOfWeek + daysInMonth) {
            // Дни текущего месяца
            dayNumber = i - firstDayOfWeek + 1;
            cellMonth = month;
            cellYear = year;
            isCurrentMonthDay = true;
            
            // Подсвечиваем сегодняшний день
            if (isCurrentMonth && dayNumber === todayDate) {
                dayCell.classList.add('today');
            }
        } else {
            // Дни следующего месяца
            dayNumber = i - firstDayOfWeek - daysInMonth + 1;
            cellMonth = month === 11 ? 0 : month + 1;
            cellYear = month === 11 ? year + 1 : year;
            isCurrentMonthDay = false;
            dayCell.classList.add('other-month');
        }
        
        // Создаем содержимое ячейки
        dayCell.innerHTML = `
            <div class="month-day-number">${dayNumber}</div>
            <div class="month-day-lessons" data-date="${cellYear}-${String(cellMonth + 1).padStart(2, '0')}-${String(dayNumber).padStart(2, '0')}">
                <!-- Уроки будут добавлены позже -->
            </div>
        `;
        
        // Скрываем 6-ю неделю, если она не нужна
        const weekRow = Math.floor(i / 7);
        if (weekRow === 5 && i >= firstDayOfWeek + daysInMonth) {
            dayCell.classList.add('empty-week');
        }
        
        monthGrid.appendChild(dayCell);
    }
    
    console.log('📅 Календарная сетка создана!');
}

// Загрузка уроков для месяца
function loadMonthLessons(year, month) {
    console.log(`📚 Загружаем уроки для ${getMonthName(month)} ${year}`);
    
    // Вычисляем первую и последнюю неделю месяца
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    const firstWeek = getWeekNumber(firstDay);
    const lastWeek = getWeekNumber(lastDay);
    
    console.log(`📅 Загружаем недели с ${firstWeek} по ${lastWeek}`);
    
    // Загружаем данные для каждой недели
    const promises = [];
    for (let week = firstWeek; week <= lastWeek; week++) {
        const promise = fetch(`/proxy-schedule/${year}/${week}`)
            .then(response => response.json())
            .catch(error => {
                console.error(`Ошибка загрузки недели ${week}:`, error);
                return { week_data: [] };
            });
        promises.push(promise);
    }
    
    // Когда все недели загружены, отображаем уроки
    Promise.all(promises).then(weekDataArray => {
        console.log('📚 Все недели загружены, отображаем уроки...');
        displayMonthLessons(weekDataArray);
    });
}

// Отображение уроков в месячном календаре
function displayMonthLessons(weekDataArray) {
    weekDataArray.forEach(weekData => {
        if (!weekData.week_data) return;
        
        weekData.week_data.forEach(day => {
            if (!day.lessons || day.lessons.length === 0) return;
            
            // Находим ячейку для этого дня
            const dateStr = day.full_date; // формат: 2025-02-19
            const lessonsContainer = document.querySelector(`[data-date="${dateStr}"]`);
            
            if (lessonsContainer) {
                // Очищаем предыдущие уроки
                lessonsContainer.innerHTML = '';
                
                // Добавляем каждый урок
                day.lessons.forEach(lesson => {
                    const lessonDiv = document.createElement('div');
                    lessonDiv.className = 'month-lesson';
                    lessonDiv.innerHTML = `
                        <div class="month-lesson-time">${lesson.time}</div>
                        <div class="month-lesson-subject">${lesson.subject}</div>
                    `;
                    lessonsContainer.appendChild(lessonDiv);
                });
                
                console.log(`📚 Добавлены уроки для ${dateStr}: ${day.lessons.length} урок(ов)`);
            }
        });
    });
    
    console.log('✅ Все уроки отображены в месячном календаре!');
}

// Получение названия месяца
function getMonthName(monthIndex) {
    const months = [
        'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ];
    return months[monthIndex];
}

// ===== НАВИГАЦИЯ ПО НЕДЕЛЯМ И МЕСЯЦАМ =====

// Универсальная навигация - запускается после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    // Переменные для отслеживания текущей недели (для недельного режима)
    let scheduleYear = new Date().getFullYear();
    let scheduleWeek = getWeekNumber(new Date());

    // Функция для загрузки расписания недели
    function loadWeekSchedule(year, week) {
        const apiUrl = `/proxy-schedule/${year}/${week}`;
        
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                if (typeof renderSchedule === 'function') {
                    renderSchedule(data);
                }
                // Обновляем название только если мы в недельном режиме
                if (currentViewMode === 'week') {
                    const periodElement = document.getElementById('currentPeriod');
                    if (periodElement) {
                        periodElement.textContent = data.week_info ? data.week_info.title : `Неделя ${week}, ${year}`;
                    }
                }
            })
    }

    // Ждем загрузки элементов
    setTimeout(function() {
        const prevBtn = document.getElementById('prevWeekBtn');
        const nextBtn = document.getElementById('nextWeekBtn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', function() {
                if (currentViewMode === 'week') {
                    // Недельный режим
                    scheduleWeek--;
                    if (scheduleWeek < 1) {
                        scheduleWeek = 52;
                        scheduleYear--;
                    }
                    loadWeekSchedule(scheduleYear, scheduleWeek);
                    
                } else if (currentViewMode === 'month') {
                    // Месячный режим
                    currentMonth--;
                    if (currentMonth < 0) {
                        currentMonth = 11;
                        currentYear--;
                    }
                    loadMonthCalendar(currentYear, currentMonth);
                    console.log(`📅 Предыдущий месяц: ${getMonthName(currentMonth)} ${currentYear}`);
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', function() {
                if (currentViewMode === 'week') {
                    // Недельный режим  
                    scheduleWeek++;
                    if (scheduleWeek > 52) {
                        scheduleWeek = 1;
                        scheduleYear++;
                    }
                    loadWeekSchedule(scheduleYear, scheduleWeek);
                    
                } else if (currentViewMode === 'month') {
                    // Месячный режим
                    currentMonth++;
                    if (currentMonth > 11) {
                        currentMonth = 0;
                        currentYear++;
                    }
                    loadMonthCalendar(currentYear, currentMonth);
                    console.log(`📅 Следующий месяц: ${getMonthName(currentMonth)} ${currentYear}`);
                }
            });
        }
        
        console.log('✅ Навигация по неделям и месяцам подключена!');
        
    }, 1000); // Ждем 1 секунду для загрузки всех элементов
});

// Обновление названия текущего периода
function updatePeriodTitle() {
    const periodElement = document.getElementById('currentPeriod');
    if (!periodElement) return;
    
    if (currentViewMode === 'week') {
        // НЕ обновляем тут, пусть это делает loadWeekSchedule
        return;
    } else if (currentViewMode === 'month') {
        // Для месячного режима показываем месяц и год
        periodElement.textContent = `${getMonthName(currentMonth)} ${currentYear}`;
    }
}

// Функция инициализации для конкретного ученика
function initChartsForStudentClass() {
    // Получаем данные из window.studentData
    const data = window.studentData;
    if (!data) {
        console.error('❌ Нет данных ученика');
        return;
    }
    
    const hasExamScores = data.hasExamScores;
    const titleElement = document.getElementById('barChartTitle');
    
    console.log('🔍 ОТЛАДКА: Инициализация диаграмм, hasExamScores:', hasExamScores);
    console.log('🔍 ОТЛАДКА: Данные домашек:', data.homework);
    console.log('🔍 ОТЛАДКА: Данные экзаменов:', data.examResults);
    
    if (hasExamScores) {
        // Для 9 и 11 классов - показываем пробники
        if (titleElement) titleElement.textContent = 'Баллы за пробники ОГЭ/ЕГЭ';
        renderBarChart();
    } else {
        // Для 7, 8, 10 классов - показываем домашки
        if (titleElement) titleElement.textContent = 'Оценки: Оформление и Решение';
        
        // ИСПРАВЛЕНИЕ: Передаем правильные данные
        if (data.homework && data.homework.length > 0) {
            console.log('📊 Отрисовываем двойную диаграмму с данными:', data.homework);
            renderDoubleBarChart(data.homework);
        } else {
            console.log('⚠️ Нет данных домашек для двойной диаграммы');
            renderDoubleBarChart([]);
        }
    }
    
    // Круговая диаграмма для всех классов
    const topicProgress = data.topicProgress || { fully: 0, questions: 0, needWork: 0 };
    renderPieChart(topicProgress);
    
    // Обновляем таблицу домашних заданий
    updateHomeworkTable();
}