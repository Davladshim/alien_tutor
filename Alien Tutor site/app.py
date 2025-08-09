from flask import Flask, render_template
import requests  # ← ПЕРЕНЕС НАВЕРХ

# Создаем Flask приложение
app = Flask(__name__)

# Базовая конфигурация
app.config['SECRET_KEY'] = 'your-secret-key-here'

@app.route('/')
@app.route('/login')
def login():
    """Страница входа в систему"""
    return render_template('login.html')

@app.route('/student')
def student_dashboard():
    """Личный кабинет ученика"""
    return render_template('student/dashboard.html')

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

if __name__ == '__main__':
    # Запуск в режиме разработки
    app.run(debug=True, host='127.0.0.1', port=8080)