// ===== ИНТЕРАКТИВНОСТЬ ЛЭНДИНГА "О ПРЕПОДАВАТЕЛЕ" =====

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== ПЕРЕМЕННЫЕ И КОНСТАНТЫ =====
    let currentSectionIndex = 0;
    let isScrolling = false;
    const scrollDelay = 800; // Задержка между переключениями секций
    
    const sections = document.querySelectorAll('.landing-section');
    const navItems = document.querySelectorAll('.nav-item');
    const totalSections = sections.length;
    
    console.log(`🚀 Лэндинг загружен! Найдено ${totalSections} секций`);
    
    // ===== ИНИЦИАЛИЗАЦИЯ =====
    function initLanding() {
        // Показываем первую секцию
        showSection(0);
        
        // Добавляем обработчики событий
        addScrollListeners();
        addNavigationListeners();
        addKeyboardListeners();
        
        console.log('✅ Лэндинг инициализирован!');
    }
    
    // ===== ПОКАЗ СЕКЦИИ =====
    function showSection(index) {
        // Проверяем границы
        if (index < 0 || index >= totalSections) return;
        
        // Убираем активный класс со всех секций
        sections.forEach(section => {
            section.classList.remove('active');
        });
        
        // Убираем активный класс со всех навигационных элементов
        navItems.forEach(item => {
            item.classList.remove('active');
        });
        
        // Показываем нужную секцию с анимацией
        setTimeout(() => {
            sections[index].classList.add('active');
            navItems[index].classList.add('active');
        }, 100);
        
        // Обновляем текущий индекс
        currentSectionIndex = index;
        
        console.log(`📍 Показана секция ${index}: ${sections[index].id}`);
    }
    
    // ===== ПРОКРУТКА КОЛЕСОМ МЫШИ =====
    function addScrollListeners() {
        let wheelTimeout;
        
        // Обработчик колеса мыши
        document.addEventListener('wheel', function(e) {
            e.preventDefault();
            
            // Если уже прокручиваем - игнорируем
            if (isScrolling) return;
            
            // Очищаем предыдущий таймаут
            clearTimeout(wheelTimeout);
            
            // Устанавливаем новый таймаут для предотвращения спама
            wheelTimeout = setTimeout(() => {
                const direction = e.deltaY > 0 ? 1 : -1; // Вниз = 1, Вверх = -1
                
                // Вычисляем новый индекс
                const newIndex = currentSectionIndex + direction;
                
                // Переключаемся на новую секцию
                if (newIndex >= 0 && newIndex < totalSections) {
                    isScrolling = true;
                    showSection(newIndex);
                    
                    // Разблокируем прокрутку через задержку
                    setTimeout(() => {
                        isScrolling = false;
                    }, scrollDelay);
                }
            }, 50); // Дебаунс 50мс
            
        }, { passive: false });
        
        console.log('🖱️ Обработчик колеса мыши добавлен');
    }
    
    // ===== НАВИГАЦИЯ ПО КЛИКУ =====
    function addNavigationListeners() {
        navItems.forEach((item, index) => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Если уже прокручиваем - игнорируем
                if (isScrolling) return;
                
                // Переключаемся на нужную секцию
                if (index !== currentSectionIndex) {
                    isScrolling = true;
                    showSection(index);
                    
                    // Разблокируем через задержку
                    setTimeout(() => {
                        isScrolling = false;
                    }, scrollDelay);
                }
            });
        });
        
        console.log('🔗 Обработчики навигации добавлены');
    }
    
    // ===== КЛАВИАТУРНАЯ НАВИГАЦИЯ =====
    function addKeyboardListeners() {
        document.addEventListener('keydown', function(e) {
            // Если уже прокручиваем - игнорируем
            if (isScrolling) return;
            
            let newIndex = currentSectionIndex;
            
            switch(e.key) {
                case 'ArrowDown':
                case 'PageDown':
                case ' ': // Пробел
                    e.preventDefault();
                    newIndex = currentSectionIndex + 1;
                    break;
                    
                case 'ArrowUp':
                case 'PageUp':
                    e.preventDefault();
                    newIndex = currentSectionIndex - 1;
                    break;
                    
                case 'Home':
                    e.preventDefault();
                    newIndex = 0;
                    break;
                    
                case 'End':
                    e.preventDefault();
                    newIndex = totalSections - 1;
                    break;
                    
                default:
                    // Цифры 1-9 для быстрого перехода
                    const num = parseInt(e.key);
                    if (num >= 1 && num <= 9 && num <= totalSections) {
                        e.preventDefault();
                        newIndex = num - 1;
                    }
                    break;
            }
            
            // Переключаемся на новую секцию
            if (newIndex >= 0 && newIndex < totalSections && newIndex !== currentSectionIndex) {
                isScrolling = true;
                showSection(newIndex);
                
                setTimeout(() => {
                    isScrolling = false;
                }, scrollDelay);
            }
        });
        
        console.log('⌨️ Клавиатурная навигация добавлена');
    }
    
    // ===== ФУНКЦИИ ДЛЯ ВНЕШНЕГО ИСПОЛЬЗОВАНИЯ =====
    
    // Переход к определенной секции (для кнопок)
    window.scrollToSection = function(sectionId) {
        const targetSection = document.getElementById(sectionId);
        if (!targetSection) return;
        
        const targetIndex = Array.from(sections).indexOf(targetSection);
        if (targetIndex !== -1) {
            isScrolling = true;
            showSection(targetIndex);
            
            setTimeout(() => {
                isScrolling = false;
            }, scrollDelay);
        }
    };
    
    // Следующая секция
    window.nextSection = function() {
        if (currentSectionIndex < totalSections - 1) {
            isScrolling = true;
            showSection(currentSectionIndex + 1);
            
            setTimeout(() => {
                isScrolling = false;
            }, scrollDelay);
        }
    };
    
    // Предыдущая секция
    window.prevSection = function() {
        if (currentSectionIndex > 0) {
            isScrolling = true;
            showSection(currentSectionIndex - 1);
            
            setTimeout(() => {
                isScrolling = false;
            }, scrollDelay);
        }
    };
    
    // ===== ОБРАБОТКА ФОРМЫ ЗАПИСИ =====
    function initContactForm() {
        const form = document.querySelector('.contact-form');
        if (!form) return;
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Получаем данные формы
            const formData = new FormData(form);
            const data = {
                student_name: formData.get('student_name'),
                contact_method: formData.get('contact_method'),
                contact_info: formData.get('contact_info')
            };
            
            // Проверяем заполненность
            if (!data.student_name || !data.contact_method || !data.contact_info) {
                showNotification('Пожалуйста, заполните все поля!', 'error');
                return;
            }
            
            // Имитируем отправку (здесь будет реальная отправка)
            showNotification('Заявка отправлена! Мы свяжемся с вами в ближайшее время.', 'success');
            
            // Очищаем форму
            form.reset();
            
            console.log('📝 Форма отправлена:', data);
        });
        
        console.log('📋 Обработчик формы добавлен');
    }
    
    // ===== УВЕДОМЛЕНИЯ =====
    function showNotification(message, type = 'info') {
        // Удаляем предыдущие уведомления
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        // Создаем новое уведомление
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Добавляем стили
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 10000;
            background: ${type === 'success' ? 'rgba(16, 185, 129, 0.9)' : 'rgba(239, 68, 68, 0.9)'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 400px;
        `;
        
        // Добавляем в DOM
        document.body.appendChild(notification);
        
        // Анимация появления
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Автоматическое скрытие
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 5000);
    }
    
    // ===== АНИМАЦИИ ПРИ ПРОКРУТКЕ =====
    function addScrollAnimations() {
        // Intersection Observer для анимаций элементов
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);
        
        // Наблюдаем за карточками и элементами
        const animatedElements = document.querySelectorAll(`
            .pricing-card,
            .review-placeholder,
            .contact-item,
            .feature-item,
            .screenshot-placeholder,
            .chart-placeholder
        `);
        
        animatedElements.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'all 0.6s ease';
            observer.observe(el);
        });
        
        console.log('✨ Анимации прокрутки добавлены');
    }
    
    // ===== ПЛАВНАЯ ТИПИЗАЦИЯ ТЕКСТА =====
    function initTypewriter() {
        const typewriterElements = document.querySelectorAll('[data-typewriter]');
        
        typewriterElements.forEach(element => {
            const text = element.textContent;
            const speed = parseInt(element.dataset.typewriter) || 50;
            
            element.textContent = '';
            element.style.borderRight = '2px solid var(--text-accent)';
            
            let i = 0;
            const timer = setInterval(() => {
                element.textContent += text[i];
                i++;
                
                if (i >= text.length) {
                    clearInterval(timer);
                    // Убираем курсор через 2 секунды
                    setTimeout(() => {
                        element.style.borderRight = 'none';
                    }, 2000);
                }
            }, speed);
        });
    }
    
    // ===== ЭФФЕКТ ПАРАЛЛАКСА ДЛЯ ФОНА =====
    function addParallaxEffect() {
        document.addEventListener('mousemove', (e) => {
            const mouseX = e.clientX / window.innerWidth;
            const mouseY = e.clientY / window.innerHeight;
            
            // Получаем фоновый контейнер
            const backgroundContainer = document.querySelector('.background-container');
            if (backgroundContainer) {
                const moveX = (mouseX - 0.5) * 20;
                const moveY = (mouseY - 0.5) * 20;
                
                backgroundContainer.style.transform = `translate(${moveX}px, ${moveY}px)`;
            }
        });
        
        console.log('🌌 Эффект параллакса добавлен');
    }
    
    // ===== АДАПТИВНОЕ МЕНЮ ДЛЯ МОБИЛЬНЫХ =====
    function initMobileNavigation() {
        const nav = document.querySelector('.landing-nav');
        let lastScrollY = window.scrollY;
        
        // Скрытие навигации при прокрутке на мобильных
        window.addEventListener('scroll', () => {
            if (window.innerWidth <= 768) {
                if (window.scrollY > lastScrollY && window.scrollY > 100) {
                    nav.style.transform = 'translateY(-100%)';
                } else {
                    nav.style.transform = 'translateY(0)';
                }
                lastScrollY = window.scrollY;
            }
        });
        
        console.log('📱 Мобильная навигация инициализирована');
    }
    
    // ===== ЗАПУСК ВСЕХ ФУНКЦИЙ =====
    initLanding();
    initContactForm();
    addScrollAnimations();
    addParallaxEffect();
    initMobileNavigation();
    
    // Типизация текста запускается с задержкой
    setTimeout(initTypewriter, 1000);
    
    console.log('🎉 Все функции лэндинга запущены!');
});

// ===== УТИЛИТЫ =====

// Дебаунс функция
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Плавная прокрутка (для обычных ссылок)
function smoothScrollTo(target, duration = 800) {
    const targetElement = document.querySelector(target);
    if (!targetElement) return;
    
    const targetPosition = targetElement.offsetTop;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;
    
    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }
    
    // Easing функция
    function ease(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }
    
    requestAnimationFrame(animation);
}

// Проверка видимости элемента
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

console.log('🚀 Landing.js загружен полностью!');