from flask import Flask, render_template
import requests  # ← ПЕРЕНЕС НАВЕРХ

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
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
    # Пока возвращаем заглушку, позже добавим реальные данные
    return {
        'week_data': [],
        'week_info': {'title': 'Расписание на неделю'}
    }

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

from flask import Flask, render_template, request, redirect, url_for, session

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    if request.method == 'POST':
        login_input = request.form.get('login')
        password_input = request.form.get('password')
        
        # Проверяем логин и пароль
        user = check_user_login(login_input, password_input)
        
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
        return redirect(url_for('login'))
    
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
        'topic_progress': topic_progress
    }
    
    # ОТЛАДКА - смотрим что передаем в шаблон
    print("=== ДАННЫЕ ДЛЯ ЛКУ ===")
    print(f"Данные ученика: {student_data}")
    print("======================")
    

    return render_template('student/dashboard.html', student=student_data)

@app.route('/parent')
def parent_dashboard():
    """Личный кабинет родителя"""
    return render_template('parent/dashboard.html')

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

@app.route('/proxy-schedule/<int:year>/<int:week>')  # ← ПЕРЕНЕС СЮДА
def proxy_schedule(year, week):
    """Прокси для получения данных расписания"""
    try:
        api_url = f"http://127.0.0.1:5000/виджет/Ясмина/api/week/{year}/{week}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "API недоступен"}, 500
            
    except Exception as e:
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

if __name__ == '__main__':
    # Запуск в режиме разработки
    app.run(debug=True, host='127.0.0.1', port=8080)