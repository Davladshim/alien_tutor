from flask import Flask, render_template
import requests  # ← ПЕРЕНЕС НАВЕРХ

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import secrets
import os
from dotenv import load_dotenv

# Загружаем настройки из .env файла
load_dotenv()

DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def get_db_connection():
    """Получить подключение к базе данных"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Ошибка подключения к БД: {e}")
        return None

def execute_query(query, params=None, fetch=False, fetch_one=False):
    """Выполнить SQL запрос"""
    conn = get_db_connection()
    if not conn:
        print("❌ Нет подключения к БД")
        return None
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            
            if fetch_one:
                result = cur.fetchone()
            elif fetch:
                result = cur.fetchall()
            else:
                result = cur.rowcount
                
            conn.commit()
            return result
    except psycopg2.Error as e:
        print(f"❌ Ошибка выполнения запроса: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_student_by_name(student_name):
    """Получить ученика по имени"""
    query = "SELECT * FROM students WHERE name = %s"
    result = execute_query(query, (student_name,), fetch_one=True)
    return dict(result) if result else None

def get_all_students():
    """Получить всех учеников"""
    query = "SELECT * FROM students ORDER BY name"
    result = execute_query(query, fetch=True)
    return [dict(row) for row in result] if result else []

def check_user_login(login, password):
    """Проверить логин и пароль пользователя"""
    query = "SELECT * FROM user_accounts WHERE login = %s AND password = %s"
    result = execute_query(query, (login, password), fetch_one=True)
    return dict(result) if result else None

def get_student_info(student_id):
    """Получить информацию об ученике по ID"""
    query = "SELECT * FROM students WHERE id = %s"
    result = execute_query(query, (student_id,), fetch_one=True)
    return dict(result) if result else None

def authenticate_user(login, password):
    """Проверка логина и пароля пользователя"""
    query = """
        SELECT id, login, role, student_id, full_name 
        FROM user_accounts 
        WHERE login = %s AND password = %s
    """
    result = execute_query(query, (login, password), fetch_one=True)
    return dict(result) if result else None

def get_student_balance(student_id):
    """Получить баланс ученика"""
    query = """
        SELECT 
            COALESCE(SUM(amount), 0) as balance,
            COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as total_spent
        FROM payments
        WHERE student_id = %s
    """
    result = execute_query(query, (student_id,), fetch_one=True)
    return dict(result) if result else {'balance': 0, 'total_paid': 0, 'total_spent': 0}

def get_student_lessons_count(student_id):
    """Получить количество уроков ученика"""
    query = """
        SELECT 
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_lessons,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_lessons,
            COUNT(CASE WHEN status = 'scheduled' AND date >= CURRENT_DATE THEN 1 END) as planned_lessons
        FROM lessons
        WHERE student_id = %s
    """
    result = execute_query(query, (student_id,), fetch_one=True)
    return dict(result) if result else {'completed_lessons': 0, 'cancelled_lessons': 0, 'planned_lessons': 0}

def get_student_schedule_data(student_id):
    """Получить данные расписания ученика"""
    from datetime import datetime, timedelta
    
    # Получаем уроки на текущую неделю
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    query = """
        SELECT date, time, subject, status, lesson_duration
        FROM lessons
        WHERE student_id = %s
        AND date BETWEEN %s AND %s
        ORDER BY date, time
    """
    result = execute_query(query, (student_id, monday, sunday), fetch=True)
    
    # Создаем структуру недели
    week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    week_data = []
    
    for i, day_name in enumerate(week_days):
        current_date = monday + timedelta(days=i)
        day_lessons = []
        
        if result:
            for lesson in result:
                if lesson['date'] == current_date:
                    day_lessons.append({
                        'time': lesson['time'].strftime('%H:%M'),
                        'subject': lesson['subject'],
                        'status': lesson['status']
                    })
        
        week_data.append({
            'day_name': day_name,
            'day_number': current_date.day,
            'full_date': current_date.strftime('%Y-%m-%d'),
            'is_today': current_date == today,
            'lessons': day_lessons
        })
    
    return {
        'week_data': week_data,
        'week_info': {
            'title': f'Неделя {today.isocalendar()[1]}, {today.year}',
            'period': f'с {monday.strftime("%d.%m")} по {sunday.strftime("%d.%m")}'
        }
    }

# Получаем данные уроков для таблицы
def get_student_lesson_reports(student_id):
    """Получить отчеты по урокам ученика"""
    query = """
        SELECT lr.created_at, lr.topic, lr.understanding_level, 
               lr.teacher_comment, er.secondary_score
        FROM lesson_reports lr
        LEFT JOIN exam_results er ON lr.student_id = er.student_id 
                                  AND DATE(lr.created_at) = er.exam_date
        WHERE lr.student_id = %s
        ORDER BY lr.created_at DESC
        LIMIT 10
    """
    result = execute_query(query, (student_id,), fetch=True)
    
    lessons = []
    if result:
        for row in result:
            lessons.append({
                'date': row['created_at'].strftime('%d.%m.%Y'),
                'topic': row['topic'],
                'understanding': row['understanding_level'],
                'score': row['secondary_score'] or '',
                'feedback': row['teacher_comment']
            })
    
    return lessons

def get_student_homework(student_id):
    """Получить домашние задания ученика"""
    query = """
        SELECT assignment_date, topic, primary_score, secondary_score, 
               design_score, solution_score, tasks_solved, tasks_assigned
        FROM homework_assignments
        WHERE student_id = %s
        ORDER BY assignment_date DESC
        LIMIT 10
    """
    result = execute_query(query, (student_id,), fetch=True)
    
    homework = []
    if result:
        for row in result:
            # Автоматически копируем первичные баллы во вторичные (пока нет алгоритма)
            secondary_score = row['secondary_score'] or row['primary_score'] or 0
            
            homework_item = {
                'date': row['assignment_date'].strftime('%d.%m.%Y'),
                'topic': row['topic'],
                'primary_score': row['primary_score'] or 0,
                'secondary_score': secondary_score,
                'design_score': row['design_score'] or 0,  # ← ВАЖНО: это поле для диаграммы
                'solution_score': row['solution_score'] or 0,  # ← ВАЖНО: это поле для диаграммы
                'tasks_solved': row['tasks_solved'] or 0,
                'tasks_assigned': row['tasks_assigned'] or 0
            }
            
            homework.append(homework_item)
            
            # Добавь отладку
            print(f"🔍 ДОМАШКА: {homework_item['date']} - Оформление: {homework_item['design_score']}, Решение: {homework_item['solution_score']}")
    
    print(f"🔍 ВСЕГО ДОМАШЕК: {len(homework)}")
    return homework

def get_student_exam_results(student_id):
    """Получить результаты пробников ученика"""
    query = """
        SELECT exam_date, primary_score, secondary_score
        FROM exam_results
        WHERE student_id = %s
        ORDER BY exam_date DESC
        LIMIT 10
    """
    result = execute_query(query, (student_id,), fetch=True)
    
    exam_scores = []
    if result:
        for row in result:
            exam_scores.append({
                'date': row['exam_date'].strftime('%d.%m'),
                'score': row['secondary_score'] or row['primary_score'] or 0
            })
    
    return exam_scores

def get_student_topic_progress(student_id):
    """Получить прогресс по темам ученика"""
    query = """
        SELECT understanding_level, COUNT(*) as count
        FROM lesson_reports
        WHERE student_id = %s
        GROUP BY understanding_level
    """
    result = execute_query(query, (student_id,), fetch=True)
    
    progress = {'fully': 0, 'questions': 0, 'needWork': 0}
    
    if result:
        for row in result:
            level = row['understanding_level']
            count = row['count']
            
            if level == 'Тема разобрана полностью':
                progress['fully'] = count
            elif level == 'Есть вопросы по теме':
                progress['questions'] = count
            elif level == 'Тему нужно закрепить':
                progress['needWork'] = count
    
    return progress

# Создаем Flask приложение
app = Flask(__name__)

# Базовая конфигурация
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.permanent_session_lifetime = timedelta(days=30)

from flask import Flask, render_template, request, redirect, url_for, session

@app.route('/')
def index():
    """Главная страница с выбором типа входа"""
    return render_template('index.html')

@app.route('/student-auth', methods=['GET', 'POST'])
def student_auth():
    """Авторизация ученика"""
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        user = authenticate_user(login, password)
        if user and user['role'] == 'student':
            session['user_id'] = user['id']
            session['login'] = user['login']
            session['role'] = user['role']
            session['student_id'] = user['student_id']
            return redirect(url_for('student_dashboard'))
        else:
            return render_template('login.html', error='Неверный логин или пароль', auth_type='student')
    
    return render_template('login.html', auth_type='student')

@app.route('/parent-auth', methods=['GET', 'POST'])
def parent_auth():
    """Авторизация родителя"""
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        user = authenticate_user(login, password)
        if user and user['role'] == 'parent':
            session['user_id'] = user['id']
            session['login'] = user['login']
            session['role'] = user['role']
            session['student_id'] = user['student_id']
            return redirect(url_for('parent_dashboard'))
        else:
            return render_template('login.html', error='Неверный логин или пароль', auth_type='parent')
    
    return render_template('login.html', auth_type='parent')

@app.route('/admin-auth', methods=['GET', 'POST'])
def admin_auth():
    """Авторизация админа"""
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        user = authenticate_user(login, password)
        if user and user['role'] == 'admin':
            session['user_id'] = user['id']
            session['login'] = user['login']
            session['role'] = user['role']
            session['admin_logged_in'] = True  # Для Календаши
            # Создаем токен для безопасной передачи в Календашу
            admin_token = secrets.token_urlsafe(32)
            session['admin_token'] = admin_token
            session.permanent = True
            print(f"🔍 СОЗДАН ТОКЕН: {admin_token}")  # ← Добавь эту строку
            print(f"🔍 СЕССИЯ ПОСЛЕ СОЗДАНИЯ ТОКЕНА: {dict(session)}")  # ← И эту
            return redirect(f"http://127.0.0.1:5000?token={admin_token}")
        else:
            return render_template('login.html', error='Неверный логин или пароль', auth_type='admin')
    
    return render_template('login.html', auth_type='admin')

@app.route('/verify-admin-token/<token>')
def verify_admin_token(token):
    """Проверка токена администратора"""
    print(f"🔍 ПРОВЕРКА ТОКЕНА: получен токен = {token}")  # ← Добавь
    print(f"🔍 Текущая сессия: {dict(session)}")  # ← Добавь
    
    if session.get('admin_token') == token and session.get('role') == 'admin':
        print("✅ ТОКЕН ВАЛИДНЫЙ")  # ← Добавь
        return {'valid': True, 'admin_id': session.get('user_id'), 'login': session.get('login')}
    
    print("❌ ТОКЕН НЕ ВАЛИДНЫЙ")  # ← Добавь
    print(f"🔍 Сохраненный токен: {session.get('admin_token')}")  # ← Добавь
    print(f"🔍 Роль: {session.get('role')}")  # ← Добавь
    return {'valid': False}

@app.route('/about-teacher')
def about_teacher():
    """Страница о преподавателе"""
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    if request.method == 'POST':
        login_input = request.form.get('login')
        password_input = request.form.get('password')
        
        # Проверяем логин и пароль
        user = check_user_login(login_input, password_input)

        # Вызываем функции
        lesson_reports = get_student_lesson_reports(student_id)
        homework_data = get_student_homework(student_id)
        
        if user:
            # Сохраняем данные пользователя в сессии
            session['user_id'] = user['id']
            session['student_id'] = user['student_id']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            # Перенаправляем в зависимости от роли
            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'parent':
                return redirect(url_for('parent_dashboard'))
            else:
                return redirect(url_for('admin_dashboard'))
        else:
            # Неправильный логин/пароль
            return render_template('login.html', error='Неправильный логин или пароль')
    
    # GET запрос - показываем форму входа
    return render_template('login.html')

@app.route('/student')
def student_dashboard():
    """Личный кабинет ученика"""
    # Проверяем авторизацию
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('index'))
    
    # Получаем данные ученика
    student_id = session.get('student_id')
    student = get_student_info(student_id)
    
    if not student:
        return redirect(url_for('login'))
    
    # Собираем все данные для ЛКУ
    balance_data = get_student_balance(student_id)
    lessons_data = get_student_lessons_count(student_id)
    schedule_data = get_student_schedule_data(student_id)
    
    # Данные для успеваемости
    exam_results = get_student_exam_results(student_id)
    topic_progress = get_student_topic_progress(student_id)
    
    # Рассчитываем запас уроков
    lesson_price = student.get('lesson_price', 0)
    current_balance = balance_data.get('balance', 0)
    lessons_in_stock = int(current_balance / lesson_price) if lesson_price > 0 else 0

    # Вызываем новые функции
    lesson_reports = get_student_lesson_reports(student_id)
    homework_data = get_student_homework(student_id)
        
    student_data = {
        'name': student['name'],
        'class': student.get('class_level', 'Не указан'),
        'lesson_price': lesson_price,
        'balance': current_balance,
        'lessons_in_stock': lessons_in_stock,
        'completed_lessons': lessons_data.get('completed_lessons', 0),
        'cancelled_lessons': lessons_data.get('cancelled_lessons', 0), 
        'planned_lessons': lessons_data.get('planned_lessons', 0),
        'schedule': schedule_data,
        'exam_results': exam_results,
        'topic_progress': get_student_topic_progress(student_id),
        'lesson_reports': lesson_reports,  # НОВОЕ
        'homework_data': homework_data     # НОВОЕ
    }
    
    # ОТЛАДКА - смотрим что передаем в шаблон
    print("=== ДАННЫЕ ДЛЯ ЛКУ ===")
    print(f"Данные ученика: {student_data}")
    print("======================")
    

    return render_template('student/dashboard.html', student=student_data)

def get_parent_info(parent_id):
    """Получить информацию о родителе по ID"""
    query = "SELECT * FROM students WHERE id = %s"
    result = execute_query(query, (parent_id,), fetch_one=True)
    return dict(result) if result else None

def get_parent_children(parent_name):
    """Получить всех детей родителя по parent_name"""
    query = "SELECT * FROM students WHERE parent_name = %s ORDER BY name"
    result = execute_query(query, (parent_name,), fetch=True)
    return [dict(row) for row in result] if result else []

@app.route('/parent')
def parent_dashboard():
    """Личный кабинет родителя"""
    # Проверяем авторизацию
    if 'user_id' not in session or session.get('role') != 'parent':
        return redirect(url_for('index'))
    
    # Получаем данные родителя
    parent_id = session.get('student_id')  # В БД это может быть parent_id
    parent_info = get_parent_info(parent_id)
    
    if not parent_info:
        return redirect(url_for('login'))
    
    # Получаем всех детей этого родителя
    children = get_parent_children(parent_info['parent_name'])
    
    # Собираем данные для каждого ребенка
    children_data = []
    for child in children:
        child_balance = get_student_balance(child['id'])
        child_lessons = get_student_lessons_count(child['id'])
        child_schedule = get_student_schedule_data(child['id'])
        child_exam_results = get_student_exam_results(child['id'])
        child_topic_progress = get_student_topic_progress(child['id'])
        child_lesson_reports = get_student_lesson_reports(child['id'])
        child_homework = get_student_homework(child['id'])
        
        # Рассчитываем запас уроков
        lesson_price = child.get('lesson_price', 0)
        current_balance = child_balance.get('balance', 0)
        lessons_in_stock = int(current_balance / lesson_price) if lesson_price > 0 else 0
        
        children_data.append({
            'id': child['id'],
            'name': child['name'],
            'class': child.get('class_level', 'Не указан'),
            'lesson_price': lesson_price,
            'balance': current_balance,
            'lessons_in_stock': lessons_in_stock,
            'completed_lessons': child_lessons.get('completed_lessons', 0),
            'cancelled_lessons': child_lessons.get('cancelled_lessons', 0),
            'planned_lessons': child_lessons.get('planned_lessons', 0),
            'schedule': child_schedule,
            'exam_results': child_exam_results,
            'topic_progress': child_topic_progress,
            'lesson_reports': child_lesson_reports,
            'homework_data': child_homework
        })
    
    parent_data = {
        'parent_name': parent_info.get('parent_name', 'Родитель'),
        'children': children_data
    }
    
    return render_template('parent/dashboard.html', parent=parent_data)

@app.route('/admin-student/<int:student_id>')
def admin_student_dashboard(student_id):
    """Админский доступ к ЛКУ ученика"""
    
    # Проверяем токен из URL
    admin_token = request.args.get('token')
    if not admin_token:
        return redirect(url_for('index'))

    # Получаем данные ученика (тот же код что в parent_dashboard для детей)
    student = get_student_info(student_id)
    if not student:
        return "Ученик не найден", 404
    
    # Собираем все данные
    student_balance = get_student_balance(student_id)
    lessons_data = get_student_lessons_count(student_id)
    schedule_data = get_student_schedule_data(student_id)
    exam_results = get_student_exam_results(student_id)
    topic_progress = get_student_topic_progress(student_id)
    lesson_reports = get_student_lesson_reports(student_id)
    homework_data = get_student_homework(student_id)
    
    # Рассчитываем запас уроков
    lesson_price = student.get('lesson_price', 0)
    current_balance = student_balance.get('balance', 0)
    lessons_in_stock = int(current_balance / lesson_price) if lesson_price > 0 else 0
    
    student_data = {
        'name': student['name'],
        'class': student.get('class_level', 'Не указан'),
        'lesson_price': lesson_price,
        'balance': current_balance,
        'lessons_in_stock': lessons_in_stock,
        'completed_lessons': lessons_data.get('completed_lessons', 0),
        'cancelled_lessons': lessons_data.get('cancelled_lessons', 0),
        'planned_lessons': lessons_data.get('planned_lessons', 0),
        'schedule': schedule_data,
        'exam_results': exam_results,
        'topic_progress': topic_progress,
        'lesson_reports': lesson_reports,
        'homework_data': homework_data
    }
    
    return render_template('student/dashboard.html', student=student_data)

@app.route('/admin-parent/<parent_name>')
def admin_parent_dashboard(parent_name):
    """Админский доступ к ЛКР родителя"""

    # Проверяем токен из URL
    admin_token = request.args.get('token')
    if not admin_token:
        return redirect(url_for('index'))

    import urllib.parse
    parent_name = urllib.parse.unquote(parent_name)
    
    # Получаем всех детей этого родителя
    children = get_parent_children(parent_name)
    
    if not children:
        return "Дети не найдены", 404
    
    # Тот же код что в parent_dashboard()
    children_data = []
    for child in children:
        child_balance = get_student_balance(child['id'])
        child_lessons = get_student_lessons_count(child['id'])
        child_schedule = get_student_schedule_data(child['id'])
        child_exam_results = get_student_exam_results(child['id'])
        child_topic_progress = get_student_topic_progress(child['id'])
        child_lesson_reports = get_student_lesson_reports(child['id'])
        child_homework = get_student_homework(child['id'])
        
        lesson_price = child.get('lesson_price', 0)
        current_balance = child_balance.get('balance', 0)
        lessons_in_stock = int(current_balance / lesson_price) if lesson_price > 0 else 0
        
        children_data.append({
            'id': child['id'],
            'name': child['name'],
            'class': child.get('class_level', 'Не указан'),
            'lesson_price': lesson_price,
            'balance': current_balance,
            'lessons_in_stock': lessons_in_stock,
            'completed_lessons': child_lessons.get('completed_lessons', 0),
            'cancelled_lessons': child_lessons.get('cancelled_lessons', 0),
            'planned_lessons': child_lessons.get('planned_lessons', 0),
            'schedule': child_schedule,
            'exam_results': child_exam_results,
            'topic_progress': child_topic_progress,
            'lesson_reports': child_lesson_reports,
            'homework_data': child_homework
        })
    
    parent_data = {
        'parent_name': parent_name,
        'children': children_data
    }
    
    return render_template('parent/dashboard.html', parent=parent_data)

@app.route('/admin')
def admin_dashboard():
    """Панель администратора"""
    return render_template('admin/main.html')

@app.route('/about')
def about():
    """Страница о преподавателе"""
    return render_template('about.html')

@app.route('/game')
def game():
    """Космическая игра-лабиринт"""
    return render_template('game/game.html')

@app.route('/proxy-schedule/<int:year>/<int:week>')  
def proxy_schedule(year, week):
    """Получить данные расписания для указанной недели"""
    try:
        from flask import request
        import re
        # Проверяем авторизацию с дополнительными вариантами
        if 'user_id' not in session and 'admin_logged_in' not in session:
            # Для AJAX запросов пробуем альтернативную проверку
            from flask import request
            referer = request.headers.get('Referer', '')
            if not referer or ('student' not in referer and 'admin' not in referer):
                return {"error": "Не авторизован"}, 401

        # Получаем ID ученика 
        student_id = None

        # Проверяем источник запроса
        referer = request.headers.get('Referer', '')
        admin_match = re.search(r'/admin-student/(\d+)', referer)

        if admin_match:
            # Если запрос с админской страницы
            student_id = int(admin_match.group(1))
            print(f"Админский запрос для ученика: {student_id}")
        else:
            # Обычный пользователь
            student_id = session.get('student_id')
            print(f"Обычный пользователь, student_id: {student_id}")

        if not student_id:
            return {"error": "Ученик не найден"}, 404
            
        # Вычисляем даты для указанной недели
        from datetime import datetime, timedelta
        
        # Находим первый день указанной недели
        jan_1 = datetime(year, 1, 1)
        jan_1_weekday = jan_1.weekday()
        
        # Находим понедельник первой недели
        days_to_monday = -jan_1_weekday if jan_1_weekday != 0 else 0
        first_monday = jan_1 + timedelta(days=days_to_monday)
        
        # Находим понедельник нужной недели
        target_monday = first_monday + timedelta(weeks=week-1)
        target_sunday = target_monday + timedelta(days=6)
        
        # Получаем уроки на эту неделю
        query = """
            SELECT date, time, subject, status, lesson_duration
            FROM lessons
            WHERE student_id = %s
            AND date BETWEEN %s AND %s
            ORDER BY date, time
        """
        result = execute_query(query, (student_id, target_monday.date(), target_sunday.date()), fetch=True)
        
        # Создаем структуру недели
        week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        week_data = []
        
        today = datetime.now().date()
        
        for i, day_name in enumerate(week_days):
            current_date = target_monday.date() + timedelta(days=i)
            day_lessons = []
            
            if result:
                for lesson in result:
                    if lesson['date'] == current_date:
                        day_lessons.append({
                            'time': lesson['time'].strftime('%H:%M'),
                            'subject': lesson['subject'],
                            'status': lesson['status']
                        })
            
            week_data.append({
                'day_name': day_name,
                'day_number': current_date.day,
                'date': current_date.strftime('%d.%m'),
                'full_date': current_date.strftime('%Y-%m-%d'),
                'is_today': current_date == today,
                'lessons': day_lessons
            })
        
        return {
            'week_data': week_data,
            'week_info': {
                'title': f'Неделя {week}, {year}',
                'period': f'с {target_monday.strftime("%d.%m")} по {target_sunday.strftime("%d.%m")}'
            }
        }
        
    except Exception as e:
        print(f"Ошибка в proxy_schedule: {e}")
        return {"error": str(e)}, 500

@app.errorhandler(404)
def page_not_found(e):
    """Обработка ошибки 404"""
    return render_template('login.html'), 404

@app.route("/test-db")
def test_db():
    """Тестовый маршрут для проверки подключения к БД"""
    try:
        students = get_all_students()
        return f"<h2>Подключение работает!</h2><p>Найдено учеников: {len(students)}</p><ul>{''.join([f'<li>{s["name"]}</li>' for s in students[:5]])}</ul>"
    except Exception as e:
        return f"<h2>Ошибка подключения:</h2><p>{str(e)}</p>"

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()  # Очищаем всю сессию
    return redirect(url_for('index'))  # На главную страницу выбора входа

if __name__ == '__main__':
    # Запуск в режиме разработки
    app.run(debug=True, host='127.0.0.1', port=8080)