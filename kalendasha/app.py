from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import calendar
import pytz
import uuid
import json

app = Flask(__name__)
app.secret_key = 'darya_shim_kalendasha_key'
app.permanent_session_lifetime = timedelta(days=30)

# Настройки подключения к PostgreSQL
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

# Словарь часовых поясов
TIMEZONE_MAPPING = {
    'КЛД': 'Europe/Kaliningrad',
    'МСК': 'Europe/Moscow',
    'МСК+1': 'Europe/Samara',
    'ЕКБ': 'Asia/Yekaterinburg',
    'ОМС': 'Asia/Omsk',
    'НСК': 'Asia/Novosibirsk',
    'ИРК': 'Asia/Irkutsk',
    'ЯКТ': 'Asia/Yakutsk',
    'ВЛД': 'Asia/Vladivostok',
    'МГД': 'Asia/Magadan',
    'КАМ': 'Asia/Kamchatka',
    'КРД': 'Europe/Moscow',
    'КЗН': 'Europe/Moscow',
    'UTC+0': 'UTC',
    'UTC+1': 'Etc/GMT-1',
    'UTC+2': 'Etc/GMT-2',
    'UTC+3': 'Etc/GMT-3',
    'UTC+4': 'Etc/GMT-4',
    'UTC+5': 'Etc/GMT-5',
    'UTC+6': 'Etc/GMT-6',
    'UTC+7': 'Etc/GMT-7',
    'UTC+8': 'Etc/GMT-8',
    'UTC+9': 'Etc/GMT-9',
    'UTC+10': 'Etc/GMT-10',
    'UTC+11': 'Etc/GMT-11',
    'UTC+12': 'Etc/GMT-12'
}

# ============================================================================
# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# ============================================================================

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
            print(f"🔍 Выполняем запрос: {query}")
            print(f"🔍 Параметры: {params}")
            
            cur.execute(query, params)
            
            if fetch_one:
                result = cur.fetchone()
            elif fetch:
                result = cur.fetchall()
            else:
                result = cur.rowcount  # ✅ Изменение здесь!
                print(f"🔍 Количество затронутых строк: {result}")
                
            conn.commit()
            return result
    except psycopg2.Error as e:
        print(f"❌ Ошибка выполнения запроса: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

# ============================================================================
# ФУНКЦИИ ДЛЯ УЧЕНИКОВ
# ============================================================================

def load_students():
    """Загрузить всех учеников"""
    query = """
        SELECT id, name, class_level as class, city, timezone, parent_name, 
               contact, notes, lesson_price, created_at
        FROM students 
        ORDER BY name
    """
    result = execute_query(query, fetch=True)
    return [dict(row) for row in result] if result else []

def verify_admin_login(login, password):
    """Проверка логина и пароля админа"""
    query = """
        SELECT id, login, role, full_name 
        FROM user_accounts 
        WHERE login = %s AND password = %s AND role = 'admin'
    """
    result = execute_query(query, (login, password), fetch_one=True)
    return dict(result) if result else None

def require_admin_login():
    """Декоратор для проверки админского доступа"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not session.get('admin_logged_in'):
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def save_student(student_data):
    """Сохранить нового ученика"""
    from datetime import datetime
    
    query = """
        INSERT INTO students (name, class_level, city, timezone, parent_name, contact, notes, lesson_price, created_at)
        VALUES (%(name)s, %(class)s, %(city)s, %(timezone)s, %(parent_name)s, %(contact)s, %(notes)s, %(lesson_price)s, NOW())
        RETURNING id
    """
    result = execute_query(query, student_data, fetch_one=True)
    
    if result:
        student_id = result['id']
        registration_time = datetime.now()
        
        # Создаем учетные записи для ученика и родителя
        login, password = create_user_account(student_id, student_data['name'], registration_time)
        
        print(f"✅ Создан ученик: {student_data['name']}")
        print(f"📝 Логин: {login}")
        print(f"🔑 Пароль: {password}")
        
        return student_id
    
    return None

def update_student(student_id, student_data):
    """Обновить данные ученика"""
    query = """
        UPDATE students 
        SET name=%(name)s, class_level=%(class)s, city=%(city)s, timezone=%(timezone)s, 
            parent_name=%(parent_name)s, contact=%(contact)s, notes=%(notes)s, lesson_price=%(lesson_price)s
        WHERE id=%(student_id)s
    """
    student_data['student_id'] = student_id
    execute_query(query, student_data)

def delete_student_completely(student_id):
    """Полное удаление ученика и всех его данных"""
    print(f"🗑️ Начинаем удаление ученика с ID: {student_id}")
    
    # Удаляем в правильном порядке - сначала связанные данные, потом основные
    queries = [
        # 1. Сначала удаляем все отчеты и задания (они ссылаются на lessons)
        "DELETE FROM lesson_reports WHERE student_id = %s",
        "DELETE FROM homework_assignments WHERE student_id = %s", 
        "DELETE FROM exam_results WHERE student_id = %s",
        "DELETE FROM topic_progress WHERE student_id = %s",
        
        # 2. Потом удаляем уроки и шаблоны
        "DELETE FROM lessons WHERE student_id = %s",
        "DELETE FROM lesson_templates WHERE student_id = %s",
        
        # 3. Удаляем платежи
        "DELETE FROM payments WHERE student_id = %s",
        
        # 4. Удаляем аккаунты ученика и родителя
        "DELETE FROM user_accounts WHERE student_id = %s",
        
        # 5. И наконец удаляем самого ученика
        "DELETE FROM students WHERE id = %s"
    ]
    
    try:
        for i, query in enumerate(queries, 1):
            print(f"🗑️ Шаг {i}: {query}")
            result = execute_query(query, (student_id,))
            print(f"✅ Удалено записей: {result}")
        
        print(f"🎉 Ученик {student_id} полностью удален!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении ученика {student_id}: {e}")
        return False

def get_student_by_name(student_name):
    """Получить ученика по имени"""
    query = "SELECT * FROM students WHERE name = %s"
    result = execute_query(query, (student_name,), fetch_one=True)
    return dict(result) if result else None

def get_student_by_id(student_id):
    """Получить ученика по ID"""
    query = "SELECT * FROM students WHERE id = %s"
    result = execute_query(query, (student_id,), fetch_one=True)
    return dict(result) if result else None

def generate_credentials(student_name, registration_time):
    """Генерация логина и пароля для ученика"""
    # Логин: убираем пробелы из имени
    login = student_name.replace(" ", "")
    
    # Пароль: имя + дата-время в формате ддммггччмм
    password = login + registration_time.strftime("%d%m%y%H%M")
    
    return login, password

def create_user_account(student_id, student_name, registration_time):
    """Создать учетную запись для ученика"""
    login, password = generate_credentials(student_name, registration_time)
    
    # Создаем аккаунт ученика
    student_query = """
        INSERT INTO user_accounts (login, password, role, student_id, full_name, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """
    execute_query(student_query, (login, password, 'student', student_id, student_name))
    
    # Создаем аккаунт родителя (если указан родитель)
    student = get_student_by_id(student_id)
    if student and student.get('parent_name'):
        parent_name = student['parent_name']
        parent_login = parent_name.replace(" ", "")
        parent_password = parent_login + registration_time.strftime("%d%m%y%H%M")
        
        # Проверяем, нет ли уже такого родителя
        check_parent_query = "SELECT id FROM user_accounts WHERE login = %s"
        existing_parent = execute_query(check_parent_query, (parent_login,), fetch_one=True)
        
        if not existing_parent:
            parent_query = """
                INSERT INTO user_accounts (login, password, role, student_id, full_name, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            execute_query(parent_query, (parent_login, parent_password, 'parent', student_id, parent_name))
    
    return login, password

# ============================================================================
# ФУНКЦИИ ДЛЯ УРОКОВ
# ============================================================================

def load_slots():
    """Загрузить все уроки"""
    query = """
        SELECT l.*, s.name as student_name
        FROM lessons l
        LEFT JOIN students s ON l.student_id = s.id
        ORDER BY l.date, l.time
    """
    result = execute_query(query, fetch=True)
    
    # Преобразуем в формат, совместимый со старым кодом
    slots = []
    for row in result:
        slot = {
            'id': row['id'],
            'student': row['student_name'],
            'subject': row['subject'],
            'time': str(row['time']),
            'status': row['status'],
            'lesson_type': row['lesson_type'],
            'lesson_duration': row['lesson_duration'],
            'from_template': row['from_template'],
            'is_paid': row['is_paid']
        }
        
        if row['date']:
            slot['date'] = row['date'].strftime('%Y-%m-%d')
        if row['day_of_week']:
            slot['day'] = row['day_of_week']
            
        slots.append(slot)
    
    return slots

def create_lesson(lesson_data):
    """Создать новый урок"""
    student = get_student_by_name(lesson_data.get('student'))
    if not student:
        return None
        
    query = """
        INSERT INTO lessons (id, student_id, date, time, day_of_week, subject, status, 
                        lesson_type, lesson_duration, from_template, is_paid, 
                        original_date, original_time, is_moved, moved_reason, created_at)
        VALUES (%(id)s, %(student_id)s, %(date)s, %(time)s, %(day_of_week)s, %(subject)s, %(status)s,
                %(lesson_type)s, %(lesson_duration)s, %(from_template)s, %(is_paid)s,
                %(original_date)s, %(original_time)s, %(is_moved)s, %(moved_reason)s, NOW())
        RETURNING id
    """
    
    lesson_params = {
        'id': lesson_data.get('id', generate_slot_id()),
        'student_id': student['id'],
        'date': lesson_data.get('date'),
        'time': lesson_data.get('time'),
        'day_of_week': lesson_data.get('day'),
        'subject': lesson_data.get('subject'),
        'status': lesson_data.get('status', 'scheduled'),
        'lesson_type': lesson_data.get('lesson_type', 'regular'),
        'lesson_duration': lesson_data.get('lesson_duration', 60),
        'from_template': lesson_data.get('from_template', False),
        'is_paid': lesson_data.get('is_paid', False),
        # НОВЫЕ ПОЛЯ для переносов:
        'original_date': lesson_data.get('original_date', lesson_data.get('date')),
        'original_time': lesson_data.get('original_time', lesson_data.get('time')),
        'is_moved': lesson_data.get('is_moved', False),
        'moved_reason': lesson_data.get('moved_reason', None)
    }
    
    result = execute_query(query, lesson_params, fetch_one=True)
    return result['id'] if result else None

def update_lesson(lesson_id, lesson_data):
    """Обновить урок"""
    print(f"🔄 Начинаем обновление урока {lesson_id}")
    print(f"🔄 Новые данные: {lesson_data}")
    
    # Сначала получаем текущие данные урока
    current_lesson = get_lesson_by_id(lesson_id)
    if not current_lesson:
        print(f"❌ Урок {lesson_id} не найден")
        return False
    
    print(f"🔄 Текущий урок: {current_lesson}")
    
    student = get_student_by_name(lesson_data.get('student'))
    if not student:
        print(f"❌ Ученик {lesson_data.get('student')} не найден")
        return False
    
    # Проверяем, переносится ли урок в будущее
    new_date = lesson_data.get('date')
    new_time = lesson_data.get('time')
    current_status = current_lesson.get('status')
    
    print(f"🔄 Проверяем перенос: статус={current_status}, новая дата={new_date}, новое время={new_time}")
    
    # Если урок был completed и переносится в будущее - отменяем оплату
    if current_status == 'completed' and new_date and new_time:
        try:
            from datetime import datetime, date, time
            
            # Парсим новую дату и время
            new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
            new_time_obj = datetime.strptime(new_time, '%H:%M').time()
            new_datetime = datetime.combine(new_date_obj, new_time_obj)
            
            print(f"🔄 Новое время урока: {new_datetime}")
            print(f"🔄 Текущее время: {datetime.now()}")
            
            # Если урок переносится в будущее
            if new_datetime > datetime.now():
                print(f"🔄 Урок {lesson_id} переносится в будущее - отменяем оплату")
                
                # Возвращаем оплату - находим платеж за этот урок
                refund_query = """
                    SELECT id, amount FROM payments 
                    WHERE lesson_id = %s AND payment_type = 'expense'
                    ORDER BY created_at DESC LIMIT 1
                """
                payment_result = execute_query(refund_query, (lesson_id,), fetch_one=True)
                
                print(f"🔄 Найден платеж: {payment_result}")
                
                if payment_result:
                    # Создаем возврат средств
                    refund_amount = abs(payment_result['amount'])  # Делаем положительным
                    refund_query = """
                        INSERT INTO payments (id, student_id, amount, payment_type, description, lesson_id, payment_date, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    refund_id = generate_slot_id()
                    execute_query(refund_query, (
                        refund_id, student['id'], refund_amount, 'refund', 
                        f"Возврат за перенос урока {lesson_id}", lesson_id
                    ))
                    print(f"✅ Создан возврат {refund_amount} руб. за урок {lesson_id}")
                
                # Меняем статус на scheduled
                lesson_data['status'] = 'scheduled'
                print(f"🔄 Статус изменен на scheduled")
            else:
                print(f"🔄 Урок не переносится в будущее, оплату не возвращаем")
        
        except Exception as e:
            print(f"❌ Ошибка при обработке переноса урока: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"🔄 Условия для возврата не выполнены: статус={current_status}, дата={new_date}, время={new_time}")
    
    # Обновляем урок
    query = """
        UPDATE lessons 
        SET student_id=%(student_id)s, date=%(date)s, time=%(time)s, day_of_week=%(day_of_week)s,
            subject=%(subject)s, status=%(status)s, lesson_duration=%(lesson_duration)s
        WHERE id=%(lesson_id)s
    """
    
    lesson_params = {
        'lesson_id': lesson_id,
        'student_id': student['id'],
        'date': lesson_data.get('date'),
        'time': lesson_data.get('time'),
        'day_of_week': lesson_data.get('day'),
        'subject': lesson_data.get('subject'),
        'status': lesson_data.get('status', 'scheduled'),
        'lesson_duration': lesson_data.get('lesson_duration', 60)
    }
    
    print(f"🔄 Обновляем урок с параметрами: {lesson_params}")
    
    execute_query(query, lesson_params)
    print(f"✅ Урок {lesson_id} обновлен")
    return True

def update_lesson_status(lesson_id, new_status):
    """Обновить только статус урока"""
    query = "UPDATE lessons SET status = %s WHERE id = %s"
    execute_query(query, (new_status, lesson_id))
    return True

def delete_lesson(lesson_id):
    """Удалить урок"""
    print(f"🎯 Пытаемся удалить урок с ID: {lesson_id}")
    query = "DELETE FROM lessons WHERE id = %s"
    result = execute_query(query, (lesson_id,))
    
    print(f"🎯 Результат execute_query: {result}")
    success = result is not None and result > 0
    print(f"🎯 Успешность удаления: {success}")
    
    return success
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))
            deleted_count = cur.rowcount  # Количество удаленных строк
            conn.commit()
            return deleted_count > 0  # True если удалили хотя бы одну строку
    except psycopg2.Error as e:
        print(f"Ошибка удаления урока: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_lesson_by_id(lesson_id):
    """Получить урок по ID"""
    query = """
        SELECT l.*, s.name as student_name
        FROM lessons l
        LEFT JOIN students s ON l.student_id = s.id
        WHERE l.id = %s
    """
    result = execute_query(query, (lesson_id,), fetch_one=True)
    
    if result:
        lesson = {
            'id': result['id'],
            'student': result['student_name'],
            'subject': result['subject'],
            'time': str(result['time']),
            'status': result['status'],
            'lesson_type': result['lesson_type'],
            'lesson_duration': result['lesson_duration'],
            'from_template': result['from_template'],
            'is_paid': result['is_paid']
        }
        
        if result['date']:
            lesson['date'] = result['date'].strftime('%Y-%m-%d')
        if result['day_of_week']:
            lesson['day'] = result['day_of_week']
            
        return lesson
    
    return None

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def generate_slot_id():
    """Генерирует уникальный ID для занятия"""
    return str(uuid.uuid4())[:8]

def convert_time_for_user(time_str, from_timezone='МСК', to_timezone='МСК'):
    """Конвертирует время между часовыми поясами"""
    try:
        # Парсим время
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        
        # Создаем datetime объект с произвольной датой
        today = datetime.now().date()
        dt = datetime.combine(today, time_obj)
        
        # Получаем часовые пояса
        from_tz = pytz.timezone(TIMEZONE_MAPPING.get(from_timezone, 'Europe/Moscow'))
        to_tz = pytz.timezone(TIMEZONE_MAPPING.get(to_timezone, 'Europe/Moscow'))
        
        # Локализуем время исходного пояса
        dt_localized = from_tz.localize(dt)
        
        # Конвертируем в целевой пояс
        dt_converted = dt_localized.astimezone(to_tz)
        
        return dt_converted.strftime('%H:%M')
    except Exception as e:
        print(f"Ошибка конвертации времени: {e}")
        return time_str
# ============================================================================
# ФУНКЦИИ ДЛЯ ШАБЛОНА НЕДЕЛИ
# ============================================================================

def load_template_week():
    """Загрузить шаблон недели"""
    query = """
        SELECT lt.*, s.name as student_name
        FROM lesson_templates lt
        LEFT JOIN students s ON lt.student_id = s.id
        ORDER BY 
            CASE lt.day_of_week
                WHEN 'Понедельник' THEN 1
                WHEN 'Вторник' THEN 2
                WHEN 'Среда' THEN 3
                WHEN 'Четверг' THEN 4
                WHEN 'Пятница' THEN 5
                WHEN 'Суббота' THEN 6
                WHEN 'Воскресенье' THEN 7
            END, lt.time
    """
    result = execute_query(query, fetch=True)
    
    templates = []
    for row in result:
        template = {
            'day': row['day_of_week'],
            'time': str(row['time']),
            'student': row['student_name'],
            'subject': row['subject'],
            'lesson_type': row['lesson_type'],
            'lesson_duration': row['lesson_duration']
        }
        
        if row['start_date']:
            template['start_date'] = row['start_date'].strftime('%Y-%m-%d')
        else:
            template['start_date'] = ""
            
        if row['end_date']:
            template['end_date'] = row['end_date'].strftime('%Y-%m-%d')
        else:
            template['end_date'] = ""
            
        templates.append(template)
    
    return templates

def add_template_lesson(lesson_data):
    """Добавить новый урок в шаблон недели"""
    student = get_student_by_name(lesson_data.get("student"))
    if not student:
        return False
        
    # Проверяем дублирование
    check_query = """
        SELECT id FROM lesson_templates 
        WHERE day_of_week = %s AND time = %s AND student_id = %s
    """
    existing = execute_query(check_query, (lesson_data.get("day"), lesson_data.get("time"), student['id']), fetch_one=True)
    
    if existing:
        return False  # дубликат найден
    
    query = """
        INSERT INTO lesson_templates (day_of_week, time, student_id, subject, start_date, end_date,
                                    lesson_type, lesson_duration, created_at)
        VALUES (%(day)s, %(time)s, %(student_id)s, %(subject)s, %(start_date)s, %(end_date)s,
                %(lesson_type)s, %(lesson_duration)s, NOW())
    """
    
    template_params = {
        'day': lesson_data.get("day"),
        'time': lesson_data.get("time"),
        'student_id': student['id'],
        'subject': lesson_data.get("subject"),
        'start_date': lesson_data.get("start_date") if lesson_data.get("start_date") else None,
        'end_date': lesson_data.get("end_date") if lesson_data.get("end_date") else None,
        'lesson_type': lesson_data.get("lesson_type", "regular"),
        'lesson_duration': lesson_data.get("lesson_duration", 60)
    }
    
    execute_query(query, template_params)
    return True

def update_template_lesson(index, lesson_data):
    """Обновить урок в шаблоне недели"""
    # Получаем список всех шаблонов для определения ID по индексу
    templates = load_template_week()
    if index < 0 or index >= len(templates):
        return False
        
    # Получаем ID шаблона по порядковому номеру
    query_get_id = """
        SELECT id FROM lesson_templates 
        ORDER BY 
            CASE day_of_week
                WHEN 'Понедельник' THEN 1
                WHEN 'Вторник' THEN 2
                WHEN 'Среда' THEN 3
                WHEN 'Четверг' THEN 4
                WHEN 'Пятница' THEN 5
                WHEN 'Суббота' THEN 6
                WHEN 'Воскресенье' THEN 7
            END, time
        LIMIT 1 OFFSET %s
    """
    result = execute_query(query_get_id, (index,), fetch_one=True)
    if not result:
        return False
        
    template_id = result['id']
    student = get_student_by_name(lesson_data.get("student"))
    if not student:
        return False
    
    query = """
        UPDATE lesson_templates 
        SET day_of_week=%(day)s, time=%(time)s, student_id=%(student_id)s, subject=%(subject)s,
            start_date=%(start_date)s, end_date=%(end_date)s, lesson_type=%(lesson_type)s,
            lesson_duration=%(lesson_duration)s
        WHERE id=%(template_id)s
    """
    
    template_params = {
        'template_id': template_id,
        'day': lesson_data.get("day"),
        'time': lesson_data.get("time"),
        'student_id': student['id'],
        'subject': lesson_data.get("subject"),
        'start_date': lesson_data.get("start_date") if lesson_data.get("start_date") else None,
        'end_date': lesson_data.get("end_date") if lesson_data.get("end_date") else None,
        'lesson_type': lesson_data.get("lesson_type", "regular"),
        'lesson_duration': lesson_data.get("lesson_duration", 60)
    }
    
    execute_query(query, template_params)
    return True

def delete_template_lesson(index):
    """Удалить урок из шаблона недели"""
    # Получаем ID шаблона по порядковому номеру
    query_get_id = """
        SELECT id FROM lesson_templates 
        ORDER BY 
            CASE day_of_week
                WHEN 'Понедельник' THEN 1
                WHEN 'Вторник' THEN 2
                WHEN 'Среда' THEN 3
                WHEN 'Четверг' THEN 4
                WHEN 'Пятница' THEN 5
                WHEN 'Суббота' THEN 6
                WHEN 'Воскресенье' THEN 7
            END, time
        LIMIT 1 OFFSET %s
    """
    result = execute_query(query_get_id, (index,), fetch_one=True)
    if not result:
        return False
        
    template_id = result['id']
    
    # Удаляем связанные уроки из расписания
    delete_related_query = """
        DELETE FROM lessons 
        WHERE from_template = true 
        AND student_id = (SELECT student_id FROM lesson_templates WHERE id = %s)
        AND day_of_week = (SELECT day_of_week FROM lesson_templates WHERE id = %s)
        AND time = (SELECT time FROM lesson_templates WHERE id = %s)
        AND subject = (SELECT subject FROM lesson_templates WHERE id = %s)
    """
    execute_query(delete_related_query, (template_id, template_id, template_id, template_id))
    
    # Удаляем сам шаблон
    query = "DELETE FROM lesson_templates WHERE id = %s"
    execute_query(query, (template_id,))
    return True

# ============================================================================
# ФУНКЦИИ ДЛЯ ПРИМЕНЕНИЯ ШАБЛОНА
# ============================================================================

def apply_template_to_schedule_with_periods():
    """Применить шаблон недели с учетом указанных периодов"""
    template = load_template_week()
    added_count = 0
    today = datetime.now().date()
    
    for template_lesson in template:
        start_date = template_lesson.get('start_date')
        end_date = template_lesson.get('end_date')
        
        # Пропускаем пустые записи
        if not template_lesson.get('day') or not template_lesson.get('time') or not template_lesson.get('student'):
            continue
        
        # Определяем период действия урока
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except:
                start_date_obj = today
        else:
            start_date_obj = today
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except:
                end_date_obj = today + timedelta(days=365)
        else:
            end_date_obj = today + timedelta(days=365)
        
        # Находим все даты в указанном периоде для нужного дня недели
        day_name = template_lesson['day']
        target_weekday = get_weekday_num(day_name)
        
        current_date = start_date_obj
        while current_date <= end_date_obj:
            if current_date.weekday() == target_weekday:
                # Проверяем, нет ли уже урока с этим учеником на эту "исходную" дату/время
                check_query = """
                    SELECT id FROM lessons 
                    WHERE student_id = (SELECT id FROM students WHERE name = %s)
                    AND original_date = %s 
                    AND original_time = %s
                """

                print(f"🔍 ПРОВЕРЯЕМ: {template_lesson['student']} на {current_date} в {template_lesson['time']}")
                existing = execute_query(check_query, (template_lesson['student'], current_date, template_lesson['time']), fetch_one=True)
                print(f"🔍 РЕЗУЛЬТАТ ПРОВЕРКИ: {existing}")

                if not existing:
                    print(f"✅ СОЗДАЕМ УРОК: {template_lesson['student']} на {current_date} в {template_lesson['time']}")
                    
                    # Создаем новый урок с правильными полями
                    lesson_data = {
                        'id': generate_slot_id(),
                        'date': current_date.strftime('%Y-%m-%d'),
                        'time': template_lesson['time'],
                        'student': template_lesson['student'],
                        'subject': template_lesson['subject'],
                        'status': 'scheduled',
                        'from_template': True,
                        'lesson_type': template_lesson.get('lesson_type', 'regular'),
                        'lesson_duration': template_lesson.get('lesson_duration', 60),
                        'original_date': current_date.strftime('%Y-%m-%d'),
                        'original_time': template_lesson['time'],
                        'is_moved': False,
                        'moved_reason': None
                    }
                    
                    print(f"🔍 ДАННЫЕ УРОКА: {lesson_data}")
                    
                    if create_lesson(lesson_data):
                        added_count += 1
                        print(f"✅ УРОК СОЗДАН! Всего создано: {added_count}")
                    else:
                        print(f"❌ ОШИБКА СОЗДАНИЯ УРОКА!")
                else:
                    print(f"⏭️ УРОК УЖЕ СУЩЕСТВУЕТ, ПРОПУСКАЕМ")
            
            current_date += timedelta(days=1)
    
    return added_count

# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С СЕМЬЯМИ
# ============================================================================

def get_families():
    """Определить все семьи по parent_name (2+ детей)"""
    query = """
        SELECT parent_name, COUNT(*) as children_count
        FROM students 
        WHERE parent_name IS NOT NULL AND parent_name != ''
        GROUP BY parent_name
        HAVING COUNT(*) > 1
    """
    families_result = execute_query(query, fetch=True)
    
    families = {}
    for family in families_result:
        parent_name = family['parent_name']
        
        # Получаем детей этой семьи
        children_query = """
            SELECT id, name, class_level, city, timezone, contact, notes, lesson_price
            FROM students 
            WHERE parent_name = %s
            ORDER BY name
        """
        children = execute_query(children_query, (parent_name,), fetch=True)
        families[parent_name] = [dict(child) for child in children]
    
    return families

def get_family_members(parent_name):
    """Получить список детей в семье"""
    families = get_families()
    return families.get(parent_name, [])

def is_student_in_family(student_name):
    """Проверить, принадлежит ли ученик к семье"""
    student = get_student_by_name(student_name)
    if not student:
        return False, None
    
    parent_name = student.get('parent_name', '').strip()
    if not parent_name:
        return False, None
    
    family_members = get_family_members(parent_name)
    return len(family_members) > 1, parent_name

def get_student_family_parent(student_name):
    """Получить родителя ученика"""
    student = get_student_by_name(student_name)
    return student.get('parent_name', '').strip() if student else None

# ============================================================================
# ФУНКЦИИ ДЛЯ СЕМЕЙНЫХ БАЛАНСОВ
# ============================================================================

def get_family_balance(parent_name):
    """Получить баланс семьи"""
    query = "SELECT * FROM families WHERE parent_name = %s"
    result = execute_query(query, (parent_name,), fetch_one=True)
    
    if not result:
        # Создаем новый семейный баланс
        family_balance = {
            "family_balance": 0,
            "total_family_paid": 0,
            "total_family_spent": 0,
            "created_at": datetime.now().isoformat()
        }
        
        create_query = """
            INSERT INTO families (parent_name, family_balance, total_family_paid, total_family_spent, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        execute_query(create_query, (parent_name, 0, 0, 0))
        return family_balance
    
    return {
        "family_balance": float(result['family_balance']),
        "total_family_paid": float(result['total_family_paid']),
        "total_family_spent": float(result['total_family_spent']),
        "created_at": result['created_at'].isoformat() if result['created_at'] else ""
    }

def save_family_balance(parent_name, balance_data):
    """Сохранить семейный баланс"""
    query = """
        UPDATE families 
        SET family_balance = %s, total_family_paid = %s, total_family_spent = %s
        WHERE parent_name = %s
    """
    execute_query(query, (
        balance_data["family_balance"],
        balance_data["total_family_paid"], 
        balance_data["total_family_spent"],
        parent_name
    ))

def add_family_payment(parent_name, amount, description="Семейное пополнение"):
    """Пополнить семейный баланс"""
    # Создаем запись о платеже
    payment_query = """
        INSERT INTO payments (id, student_id, amount, payment_type, description, payment_date, created_at)
        VALUES (%s, NULL, %s, %s, %s, NOW(), NOW())
    """
    payment_id = generate_slot_id()
    execute_query(payment_query, (payment_id, amount, 'family_payment', f"СЕМЬЯ: {parent_name} - {description}"))
    
    # Обновляем семейный баланс
    family_balance = get_family_balance(parent_name)
    family_balance["family_balance"] += amount
    family_balance["total_family_paid"] += amount
    save_family_balance(parent_name, family_balance)
    
    return {
        "id": payment_id,
        "student_name": f"СЕМЬЯ: {parent_name}",
        "amount": amount,
        "type": "family_payment",
        "description": description,
        "date": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat()
    }

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ВРЕМЕННЫЕ ФУНКЦИИ
# ============================================================================

def get_weekday_num(day_name_ru):
    """Получить номер дня недели (0-6) по русскому названию"""
    days_mapping = {
        "Понедельник": 0,
        "Вторник": 1,
        "Среда": 2,
        "Четверг": 3,
        "Пятница": 4,
        "Суббота": 5,
        "Воскресенье": 6
    }
    return days_mapping.get(day_name_ru)

def get_weekday_ru(weekday_num):
    """Конвертация номера дня недели в русское название"""
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    return days[weekday_num]

def get_week_dates(year, week_number):
    """Получить даты для конкретной недели"""
    # Создаем дату для 4 января указанного года (это всегда в первой неделе ISO)
    jan_4 = datetime(year, 1, 4)
    
    # Находим понедельник первой недели
    first_monday = jan_4 - timedelta(days=jan_4.weekday())
    
    # Находим нужную неделю
    target_week_start = first_monday + timedelta(weeks=week_number - 1)
    
    week_dates = []
    days_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    
    for i in range(7):
        date = target_week_start + timedelta(days=i)
        week_dates.append({
            "date": date.strftime("%d.%m"),
            "full_date": date.strftime("%Y-%m-%d"),
            "day_name": days_names[i],
            "day_short": date.strftime("%a"),
            "is_today": date.date() == datetime.now().date()
        })
    
    return week_dates
# ============================================================================
# ФУНКЦИИ ДЛЯ ПЛАТЕЖЕЙ И БАЛАНСОВ
# ============================================================================

def add_payment(student_name, amount, description="Пополнение баланса", payment_date=None):
    """Добавить платеж ученика"""
    student = get_student_by_name(student_name)
    if not student:
        return None
    
    if payment_date is None:
        payment_date = datetime.now()
    elif isinstance(payment_date, str):
        try:
            payment_date = datetime.strptime(payment_date, '%Y-%m-%d')
        except:
            payment_date = datetime.now()
    
    # Создаем запись о платеже
    payment_query = """
        INSERT INTO payments (id, student_id, amount, payment_type, description, payment_date, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        RETURNING id
    """
    payment_id = generate_slot_id()
    result = execute_query(payment_query, (
        payment_id, student['id'], amount, 'payment', description, payment_date
    ), fetch_one=True)
    
    if result:
        return {
            "id": payment_id,
            "student_name": student_name,
            "amount": amount,
            "type": "payment",
            "description": description,
            "date": payment_date.isoformat(),
            "created_at": datetime.now().isoformat()
        }
    
    return None

def get_student_balance(student_name):
    """Получить баланс ученика"""
    student = get_student_by_name(student_name)
    if not student:
        return {
            "balance": 0,
            "lesson_price": 0,
            "total_paid": 0,
            "total_spent": 0,
            "lessons_taken": 0
        }
    
    # Получаем все платежи ученика
    payments_query = """
        SELECT SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_paid,
               SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_spent,
               SUM(amount) as balance
        FROM payments
        WHERE student_id = %s
    """
    payments_result = execute_query(payments_query, (student['id'],), fetch_one=True)
    
    # Подсчитываем проведенные уроки
    lessons_query = """
        SELECT COUNT(*) as lessons_taken
        FROM lessons
        WHERE student_id = %s AND status = 'completed'
    """
    lessons_result = execute_query(lessons_query, (student['id'],), fetch_one=True)
    
    return {
        "balance": float(payments_result['balance']) if payments_result['balance'] else 0,
        "lesson_price": float(student['lesson_price']) if student['lesson_price'] else 0,
        "total_paid": float(payments_result['total_paid']) if payments_result['total_paid'] else 0,
        "total_spent": float(payments_result['total_spent']) if payments_result['total_spent'] else 0,
        "lessons_taken": int(lessons_result['lessons_taken']) if lessons_result['lessons_taken'] else 0
    }

def get_student_payment_history(student_name, limit=None):
    """Получить историю платежей ученика"""
    student = get_student_by_name(student_name)
    if not student:
        return []
    
    query = """
        SELECT id, amount, payment_type as type, description, payment_date as date, created_at
        FROM payments
        WHERE student_id = %s
        ORDER BY payment_date DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    result = execute_query(query, (student['id'],), fetch=True)
    
    payments = []
    for row in result:
        payment = dict(row)
        if payment['date']:
            payment['date'] = payment['date'].isoformat()
            payment['date_formatted'] = payment['date'][:10]  # YYYY-MM-DD
        payments.append(payment)
    
    return payments

def process_lesson_payment(student_name, lesson_id):
    """Списать средства за проведенный урок"""
    # Проверяем, не является ли урок пробным
    lesson = get_lesson_by_id(lesson_id)
    if lesson and lesson.get('lesson_type') == 'trial':
        return True, "Пробный урок завершен (бесплатно)"
    print(f"🔄 СПИСАНИЕ: урок {lesson_id}, ученик {student_name}")
    print(f"🔄 Данные урока: {lesson}")
    
    student = get_student_by_name(student_name)
    if not student:
        return False, "Ученик не найден в системе"
    
    lesson_price = float(student['lesson_price']) if student['lesson_price'] else 0
    
    # Создаем запись о расходе
    expense_query = """
        INSERT INTO payments (id, student_id, amount, payment_type, description, lesson_id, payment_date, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
    """
    expense_id = generate_slot_id()
    result = execute_query(expense_query, (
        expense_id, student['id'], -lesson_price, 'expense', 
        f"Оплата урока {lesson_id}", lesson_id
    ))
    print(f"🔄 Запись о списании создана: result={result}, amount={-lesson_price}")

    # Помечаем урок как оплаченный
    mark_paid_query = "UPDATE lessons SET is_paid = true WHERE id = %s"
    result2 = execute_query(mark_paid_query, (lesson_id,))
    print(f"🔄 Урок помечен как оплаченный: result={result2}")

    # Получаем текущий баланс
    balance = get_student_balance(student_name)
    
    return True, f"Урок оплачен. Остаток на балансе: {balance['balance']} руб."

def reset_student_balance(student_name):
    """Обнулить баланс ученика"""
    student = get_student_by_name(student_name)
    if not student:
        return False
    
    # Удаляем все записи о платежах этого ученика
    delete_query = "DELETE FROM payments WHERE student_id = %s"
    execute_query(delete_query, (student['id'],))
    
    return True

def get_financial_overview():
    """Получить общий финансовый обзор по всем ученикам"""
    # Общий баланс всех студентов
    query = """
        SELECT 
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_paid,
            SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_spent,
            SUM(amount) as total_balance
        FROM payments p
        JOIN students s ON p.student_id = s.id
    """
    result = execute_query(query, fetch_one=True)
    
    # Подсчитываем долги как отрицательные балансы учеников
    debt_query = """
        SELECT SUM(ABS(balance)) as total_debt
        FROM (
            SELECT student_id, SUM(amount) as balance
            FROM payments p
            JOIN students s ON p.student_id = s.id
            GROUP BY student_id
            HAVING SUM(amount) < 0
        ) negative_balances
    """
    debt_result = execute_query(debt_query, fetch_one=True)
    
    if not result:
        return {
            'total_prepaid': 0,
            'total_debt': 0,
            'total_balance': 0,
            'students_with_positive_balance': 0,
            'students_with_negative_balance': 0
        }
    
    total_balance = float(result['total_balance']) if result['total_balance'] else 0
    total_debt = float(debt_result['total_debt']) if debt_result and debt_result['total_debt'] else 0
    total_prepaid = total_balance if total_balance > 0 else 0
    
    # Подсчитываем студентов с положительным и отрицательным балансом
    students_balances_query = """
        SELECT 
            COUNT(CASE WHEN balance > 0 THEN 1 END) as positive_count,
            COUNT(CASE WHEN balance < 0 THEN 1 END) as negative_count
        FROM (
            SELECT student_id, SUM(amount) as balance
            FROM payments p
            JOIN students s ON p.student_id = s.id
            GROUP BY student_id
        ) balances
    """
    balances_result = execute_query(students_balances_query, fetch_one=True)
    
    return {
        'total_prepaid': total_prepaid,
        'total_debt': total_debt,
        'total_balance': total_balance,
        'students_with_positive_balance': int(balances_result['positive_count']) if balances_result['positive_count'] else 0,
        'students_with_negative_balance': int(balances_result['negative_count']) if balances_result['negative_count'] else 0
    }

# ============================================================================
# ФУНКЦИИ ДЛЯ АВТОМАТИЧЕСКОЙ ОБРАБОТКИ УРОКОВ
# ============================================================================

def auto_update_lesson_statuses():
    """Автоматически обновляет статусы уроков на основе даты, времени и длительности урока"""
    today = datetime.now()
    
    # Находим уроки, которые должны были закончиться
    query = """
        SELECT l.*, s.name as student_name
        FROM lessons l
        JOIN students s ON l.student_id = s.id
        WHERE l.status = 'scheduled'
        AND l.date IS NOT NULL
        AND l.time IS NOT NULL
        AND l.date + l.time + INTERVAL '1 minute' * COALESCE(l.lesson_duration, 60) < NOW()
    """
    
    overdue_lessons = execute_query(query, fetch=True)
    modified = False
    
    for lesson in overdue_lessons:
        # Обновляем статус урока (убираем автоматическую пометку как оплаченный)
        update_query = """
            UPDATE lessons 
            SET status = 'completed'
            WHERE id = %s
        """
        execute_query(update_query, (lesson['id'],))

        # Списываем оплату
        success, message = process_lesson_payment(lesson['student_name'], lesson['id'])
        print(f"[AUTO_UPDATE] Урок {lesson['id']}: success={success}, message={message}")
        if success:
            # Помечаем урок как оплаченный только после успешного списания
            paid_query = "UPDATE lessons SET is_paid = true WHERE id = %s"
            execute_query(paid_query, (lesson['id'],))
            print(f"✅ Урок {lesson['id']} помечен как оплаченный")
        else:
            print(f"❌ Ошибка списания для урока {lesson['id']}: {message}")
        if success:
            print(f"[AUTO_UPDATE] Автоматически списана оплата: {message}")
        else:
            print(f"[AUTO_UPDATE] Ошибка списания оплаты: {message}")
        
        modified = True
    
    return modified

# ============================================================================
# ФУНКЦИИ ДЛЯ СТАТИСТИКИ
# ============================================================================

def get_lessons_stats(students):
    """Получить статистику проведенных уроков для каждого ученика"""
    lessons_stats = {}
    
    for student in students:
        # Считаем проведенные уроки
        completed_query = """
            SELECT COUNT(*) as completed_lessons
            FROM lessons
            WHERE student_id = %s AND status = 'completed'
        """
        result = execute_query(completed_query, (student['id'],), fetch_one=True)
        
        lessons_stats[student['name']] = {
            'actual_completed': int(result['completed_lessons']) if result['completed_lessons'] else 0,
            'regular_planned_actual': 0  # Пока оставим 0
        }
    
    return lessons_stats

def get_student_widget_stats(student_name):
    """Получить статистику ученика для виджетов"""
    student = get_student_by_name(student_name)
    if not student:
        return {
            'completed_lessons': 0,
            'cancelled_lessons': 0,
            'planned_this_month': 0
        }
    
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year
    
    # Статистика за все время
    all_time_query = """
        SELECT 
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_lessons,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_lessons
        FROM lessons
        WHERE student_id = %s
    """
    all_time_result = execute_query(all_time_query, (student['id'],), fetch_one=True)
    
    # Запланированные уроки в текущем месяце
    month_query = """
        SELECT COUNT(*) as planned_this_month
        FROM lessons
        WHERE student_id = %s
        AND status = 'scheduled'
        AND from_template = true
        AND EXTRACT(MONTH FROM date) = %s
        AND EXTRACT(YEAR FROM date) = %s
    """
    month_result = execute_query(month_query, (student['id'], current_month, current_year), fetch_one=True)
    
    return {
        'completed_lessons': int(all_time_result['completed_lessons']) if all_time_result['completed_lessons'] else 0,
        'cancelled_lessons': int(all_time_result['cancelled_lessons']) if all_time_result['cancelled_lessons'] else 0,
        'planned_this_month': int(month_result['planned_this_month']) if month_result['planned_this_month'] else 0
    }

def get_student_payment_stats(student_name):
    """Получить финансовую статистику ученика"""
    balance = get_student_balance(student_name)
    
    # Запас уроков (оплачено вперед)
    lesson_price = balance.get('lesson_price', 0)
    current_balance = balance.get('balance', 0)
    
    if lesson_price > 0 and current_balance > 0:
        lessons_in_stock = int(current_balance / lesson_price)
    else:
        lessons_in_stock = 0
    
    # Ожидают оплаты (проведенные, но неоплаченные)
    student = get_student_by_name(student_name)
    unpaid_lessons = 0
    
    if student:
        unpaid_query = """
            SELECT COUNT(*) as unpaid_lessons
            FROM lessons
            WHERE student_id = %s
            AND status = 'completed'
            AND (is_paid = false OR is_paid IS NULL)
            AND lesson_type != 'trial'
        """
        unpaid_result = execute_query(unpaid_query, (student['id'],), fetch_one=True)
        unpaid_lessons = int(unpaid_result['unpaid_lessons']) if unpaid_result['unpaid_lessons'] else 0
    
    return {
        'lessons_in_stock': lessons_in_stock,
        'unpaid_lessons': unpaid_lessons,
        'lesson_price': lesson_price
    }

def get_month_calendar(year, month):
    """Получить календарь месяца с полными датами"""
    cal = calendar.monthcalendar(year, month)
    month_data = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                date_obj = datetime(year, month, day)
                week_data.append({
                    'day': day,
                    'date': date_obj.strftime('%Y-%m-%d'),
                    'display_date': date_obj.strftime('%d.%m'),
                    'weekday': date_obj.strftime('%A'),
                    'weekday_ru': get_weekday_ru(date_obj.weekday()),
                    'is_today': date_obj.date() == datetime.now().date()
                })
        month_data.append(week_data)
    
    return month_data

def get_lessons_for_date(date_str, slots=None):
    """Получить все занятия для конкретной даты"""
    if slots is None:
        slots = load_slots()
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    weekday_ru = get_weekday_ru(date_obj.weekday())
    
    lessons = []
    for slot in slots:
        # Проверяем разовые занятия с конкретной датой
        if slot.get('date') == date_str:
            lessons.append(slot)
        # Проверяем регулярные занятия по дням недели (без конкретной даты)
        elif not slot.get('date') and slot.get('day') == weekday_ru:
            lessons.append(slot)
    
    # Сортируем по времени
    lessons.sort(key=lambda x: x['time'])
    return lessons

def get_current_week_number():
    """Получить номер текущей недели"""
    today = datetime.now()
    return today.isocalendar()[1]

def clear_all_lessons():
    """Очистить все занятия"""
    try:
        execute_query("DELETE FROM lessons")
        return True, "Все занятия удалены"
    except Exception as e:
        return False, f"Ошибка при очистке: {e}"

# ============================================================================
# ФУНКЦИИ ДЛЯ ДОСТУПНЫХ СЛОТОВ
# ============================================================================

def load_available_slots():
    """Загрузить доступные слоты"""
    query = """
        SELECT id, day_of_week as day, time, duration, slot_type as type, created_at
        FROM available_slots
        ORDER BY 
            CASE day_of_week
                WHEN 'Понедельник' THEN 1
                WHEN 'Вторник' THEN 2
                WHEN 'Среда' THEN 3
                WHEN 'Четверг' THEN 4
                WHEN 'Пятница' THEN 5
                WHEN 'Суббота' THEN 6
                WHEN 'Воскресенье' THEN 7
            END, time
    """
    result = execute_query(query, fetch=True)
    
    slots = []
    for row in result:
        slot = {
            'id': row['id'],
            'day': row['day'],
            'time': str(row['time']),
            'duration': row['duration'],
            'type': row['type']
        }
        
        if row['created_at']:
            slot['created_at'] = row['created_at'].isoformat()
            
        slots.append(slot)
    
    return slots

def create_available_slot(slot_data):
    """Создать новый доступный слот"""
    query = """
        INSERT INTO available_slots (id, day_of_week, time, duration, slot_type, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """
    
    slot_id = slot_data.get('id', generate_slot_id())
    execute_query(query, (
        slot_id,
        slot_data.get('day'),
        slot_data.get('time'),
        slot_data.get('duration', 60),
        slot_data.get('type', 'permanent')
    ))
    
    return slot_id

def delete_available_slot(slot_index):
    """Удалить доступный слот по индексу"""
    # Получаем ID слота по порядковому номеру
    query_get_id = """
        SELECT id FROM available_slots 
        ORDER BY 
            CASE day_of_week
                WHEN 'Понедельник' THEN 1
                WHEN 'Вторник' THEN 2
                WHEN 'Среда' THEN 3
                WHEN 'Четверг' THEN 4
                WHEN 'Пятница' THEN 5
                WHEN 'Суббота' THEN 6
                WHEN 'Воскресенье' THEN 7
            END, time
        LIMIT 1 OFFSET %s
    """
    result = execute_query(query_get_id, (slot_index,), fetch_one=True)
    if not result:
        return False
        
    slot_id = result['id']
    
    # Удаляем слот
    delete_query = "DELETE FROM available_slots WHERE id = %s"
    execute_query(delete_query, (slot_id,))
    return True

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ
# ============================================================================

def initialize_app():
    """Инициализация приложения при запуске"""
    print("Инициализация Календаши...")
    
    # Автоматически обновляем статусы уроков и списываем оплату
    print("Проверяем статусы уроков...")
    auto_update_lesson_statuses()
    
    print("Календаша готова к работе!")

# ============================================================================
# ФУНКЦИИ ДЛЯ ФИНАНСОВОЙ СТАТИСТИКИ ОПЛАТЫ  
# ============================================================================

def get_predicted_income_current_month():
    """Получить прогнозируемый доход за текущий месяц (БЫСТРО)"""
    today = datetime.now()
    year, month = today.year, today.month
    
    query = """
        SELECT SUM(s.lesson_price) as predicted_income
        FROM lessons l
        JOIN students s ON l.student_id = s.id
        WHERE l.lesson_type = 'regular'
        AND l.from_template = true
        AND l.status IN ('scheduled', 'completed')
        AND EXTRACT(MONTH FROM l.date) = %s
        AND EXTRACT(YEAR FROM l.date) = %s
    """
    result = execute_query(query, (month, year), fetch_one=True)
    
    return float(result['predicted_income']) if result and result['predicted_income'] else 0

def get_actual_income_current_month():
    """Получить фактический доход за текущий месяц (БЫСТРО)"""
    today = datetime.now()
    year, month = today.year, today.month
    
    query = """
        SELECT SUM(ABS(amount)) as actual_income
        FROM payments
        WHERE amount < 0
        AND payment_type = 'expense'
        AND EXTRACT(MONTH FROM payment_date) = %s
        AND EXTRACT(YEAR FROM payment_date) = %s
    """
    result = execute_query(query, (month, year), fetch_one=True)
    
    return float(result['actual_income']) if result and result['actual_income'] else 0

def get_month_student_detailed_stats(year, month):
    """Получить детальную статистику по каждому ученику за месяц (БЫСТРО)"""
    print(f"🔍 Считаем статистику для {month}/{year}")
    
    query = """
        SELECT 
            s.name,
            COUNT(CASE 
                WHEN l.from_template = true 
                AND l.status IN ('scheduled', 'completed', 'cancelled') 
                THEN 1 
            END) as regular_planned,
            COUNT(CASE WHEN l.status = 'completed' THEN 1 END) as total_completed,
            COUNT(CASE 
                WHEN l.status = 'cancelled' 
                AND l.from_template = true 
                THEN 1 
            END) as regular_cancelled
        FROM students s
        LEFT JOIN lessons l ON s.id = l.student_id 
            AND EXTRACT(MONTH FROM l.date) = %s
            AND EXTRACT(YEAR FROM l.date) = %s
        GROUP BY s.id, s.name
        ORDER BY s.name
    """
    result = execute_query(query, (month, year), fetch=True)
    
    student_stats = {}
    for row in result:
        print(f"📊 {row['name']}: регулярных={row['regular_planned']}, завершенных={row['total_completed']}")
        student_stats[row['name']] = {
            'regular_planned': int(row['regular_planned']),
            'total_completed': int(row['total_completed']),
            'regular_cancelled': int(row['regular_cancelled']),
            'regular_planned_actual': int(row['regular_planned']),
            'actual_completed': int(row['total_completed'])
        }
    
    return student_stats

def get_student_by_id(student_id):
    """Получить ученика по ID"""
    query = "SELECT * FROM students WHERE id = %s"
    result = execute_query(query, (student_id,), fetch_one=True)
    return dict(result) if result else None

def get_student_balance(student_id):
    """Получить баланс ученика"""
    # Временная заглушка - позже подключим к системе оплат
    return {'balance': 0}

def get_student_lessons_count(student_id):
    """Получить количество уроков ученика"""
    query = """
        SELECT 
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_lessons,
            COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_lessons,
            COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as planned_lessons
        FROM lessons 
        WHERE student_id = %s
    """
    result = execute_query(query, (student_id,), fetch_one=True)
    if result:
        return {
            'completed_lessons': result['completed_lessons'] or 0,
            'cancelled_lessons': result['cancelled_lessons'] or 0,
            'planned_lessons': result['planned_lessons'] or 0
        }
    return {'completed_lessons': 0, 'cancelled_lessons': 0, 'planned_lessons': 0}

def get_student_schedule_data(student_id):
    """Получить расписание ученика"""
    from datetime import datetime, timedelta
    
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

def get_student_exam_results(student_id):
    """Получить результаты экзаменов ученика"""
    # Временная заглушка
    return []

def get_student_topic_progress(student_id):
    """Получить прогресс по темам"""
    # Временная заглушка
    return {'fully': 0, 'questions': 0, 'needwork': 0}

def get_student_lesson_reports(student_id):
    """Получить отчеты по урокам ученика"""
    # Временная заглушка
    return []

def get_student_homework(student_id):
    """Получить домашние задания ученика"""
    # Временная заглушка
    return []

def get_parent_children(parent_name):
    """Получить детей родителя"""
    query = "SELECT * FROM students WHERE parent_name = %s ORDER BY name"
    result = execute_query(query, (parent_name,), fetch=True)
    return [dict(row) for row in result] if result else []

# ============================================================================
# FLASK МАРШРУТЫ
# ============================================================================

@app.route("/")
def home():
    """Главная страница с админскими функциями"""
    
    # Простая проверка: если есть токен в URL - авторизуем
    token = request.args.get('token')
    if token and not session.get('admin_logged_in'):
        # Не проверяем токен на сайте, просто авторизуем
        session['admin_logged_in'] = True
        session.permanent = True
        session['admin_token'] = token
        # Убираем токен из URL
        return redirect(url_for('home'))
    
    # Проверяем авторизацию
    if not session.get('admin_logged_in') and not request.args.get('token'):
        return redirect("http://127.0.0.1:8080/admin-auth")

    # Получаем недавние проведенные уроки (последние 4 дня)
    from datetime import datetime, timedelta
    four_days_ago = datetime.now().date() - timedelta(days=4)
    
    recent_lessons_query = """
        SELECT l.id, l.date, l.time, l.subject, s.name as student_name
        FROM lessons l
        JOIN students s ON l.student_id = s.id
        WHERE l.status = 'completed'
        AND l.date >= %s
        ORDER BY l.date DESC, l.time DESC
        LIMIT 10
    """
    recent_lessons = execute_query(recent_lessons_query, (four_days_ago,), fetch=True)
    
    # Форматируем данные уроков
    lessons_data = []
    if recent_lessons:
        for lesson in recent_lessons:
            lessons_data.append({
                'id': lesson['id'],
                'date': lesson['date'].strftime('%d.%m.%Y'),
                'time': lesson['time'].strftime('%H:%M'),
                'subject': lesson['subject'],
                'student_name': lesson['student_name']
            })

    # Получаем всех учеников с их аккаунтами
    students_accounts_query = """
        SELECT 
            s.id, s.name, s.class_level, s.parent_name,
            us.login as student_login, us.password as student_password,
            up.login as parent_login, up.password as parent_password
        FROM students s
        LEFT JOIN user_accounts us ON s.id = us.student_id AND us.role = 'student'
        LEFT JOIN user_accounts up ON s.id = up.student_id AND up.role = 'parent'
        ORDER BY s.name
    """
    students_accounts = execute_query(students_accounts_query, fetch=True)
    
    # Формируем данные для таблицы учеников
    accounts_data = []
    if students_accounts:
        for row in students_accounts:
            accounts_data.append({
                'student_id': row['id'],
                'student_name': row['name'],
                'student_class': row['class_level'] or 'Не указан',
                'student_login': row['student_login'] or 'Нет аккаунта',
                'student_password': row['student_password'] or 'Нет аккаунта',
                'parent_name': row['parent_name'] or 'Не указан',
                'has_student_account': bool(row['student_login']),
                'has_parent_account': bool(row['parent_login'])
            })

    # Группируем родителей по семьям (БЕЗ ЛИШНЕГО ОТСТУПА!)
    families_data = {}
    if students_accounts:
        for row in students_accounts:
            parent_name = row['parent_name']
            if parent_name and parent_name != '' and parent_name != 'Не указан':
                if parent_name not in families_data:
                    families_data[parent_name] = {
                        'parent_name': parent_name,
                        'children': [],
                        'parent_login': row['parent_login'] or 'Нет аккаунта',
                        'parent_password': row['parent_password'] or 'Нет аккаунта',
                        'has_parent_account': bool(row['parent_login'])
                    }
                
                families_data[parent_name]['children'].append(row['name'])

    # Преобразуем в список для шаблона
    families_list = list(families_data.values())

    return render_template("home.html", 
                        recent_lessons=lessons_data,
                        accounts_data=accounts_data,
                        families_data=families_list,
                        admin_token=session.get('admin_token'))

@app.route("/add-lesson-report", methods=["POST"])
def add_lesson_report():
    # Тут уже есть проверка, но можно заменить на нашу:
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Добавить отчет по уроку"""
    try:
        lesson_id = request.form.get('lesson_id')
        topic = request.form.get('topic')
        understanding_level = request.form.get('understanding_level')
        teacher_comment = request.form.get('teacher_comment')
        homework_assigned = request.form.get('homework_assigned')
        exam_score = request.form.get('exam_score')
        
        # Получаем информацию об уроке
        lesson = get_lesson_by_id(lesson_id)
        if not lesson:
            return f"<script>alert('Урок не найден!'); window.location.href='/';</script>"
        
        # Получаем ученика
        student = get_student_by_name(lesson['student'])
        if not student:
            return f"<script>alert('Ученик не найден!'); window.location.href='/';</script>"
        
        # Сохраняем отчет по уроку
        report_query = """
            INSERT INTO lesson_reports (lesson_id, student_id, topic, understanding_level, teacher_comment, homework_assigned, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        execute_query(report_query, (lesson_id, student['id'], topic, understanding_level, teacher_comment, homework_assigned))
        
        # Если есть баллы за пробник - сохраняем их
        if exam_score and exam_score.strip():
            exam_query = """
                INSERT INTO exam_results (student_id, exam_date, secondary_score, created_at)
                VALUES (%s, %s, %s, NOW())
            """
            lesson_date = datetime.strptime(lesson['date'], '%Y-%m-%d').date()
            execute_query(exam_query, (student['id'], lesson_date, int(exam_score)))
        
        return f"<script>alert('Отчет успешно сохранен!'); window.location.href='/';</script>"
        
    except Exception as e:
        print(f"Ошибка сохранения отчета: {e}")
        return f"<script>alert('Ошибка: {e}'); window.location.href='/';</script>"

@app.route("/admin/student/<int:student_id>")
def admin_student_view(student_id):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Перенаправление в ЛКУ ученика на сайте"""
    # Проверяем авторизацию
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Переход...</title>
    </head>
    <body>
        <p>Открываем ЛКУ ученика...</p>
        <script>
            window.open("http://127.0.0.1:8080/admin-student/{student_id}", "_blank");
            setTimeout(function() {{
                window.location.href = "/";
            }}, 500);
        </script>
    </body>
    </html>
    '''

@app.route("/admin/parent/<parent_name>")
def admin_parent_view(parent_name):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Перенаправление в ЛКР родителя на сайте"""
    # Проверяем авторизацию
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    import urllib.parse
    encoded_name = urllib.parse.quote(parent_name)
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Переход...</title>
    </head>
    <body>
        <p>Открываем ЛКР родителя...</p>
        <script>
            window.open("http://127.0.0.1:8080/admin-parent/{encoded_name}", "_blank");
            setTimeout(function() {{
                window.location.href = "/";
            }}, 500);
        </script>
    </body>
    </html>
    '''

@app.route("/ученики")
def ucheniki():
    if not session.get('admin_logged_in'):
        print(f"🔍 ОТЛАДКА: session = {dict(session)}")
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    students = load_students()
    return render_template("ucheniki.html", students=students)

@app.route("/ученики/добавить", methods=["GET", "POST"])
def add_student():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    if request.method == "POST":
        # Обработка кастомного класса
        class_value = request.form.get("class", "").strip()
        custom_class = request.form.get("custom_class", "").strip()
        
        if class_value == "Другое" and custom_class:
            class_value = custom_class
        
        # Добавляем сохранение стоимости урока
        lesson_price = request.form.get("lesson_price", "0")
        try:
            lesson_price = float(lesson_price)
        except (ValueError, TypeError):
            lesson_price = 0
        
        student_data = {
            "name": request.form.get("name", "").strip(),
            "class": class_value,
            "city": request.form.get("city", "").strip(),
            "timezone": request.form.get("timezone", "МСК"),
            "parent_name": request.form.get("parent_name", "").strip(),
            "contact": request.form.get("contact", "").strip(),
            "notes": request.form.get("notes", "").strip(),
            "lesson_price": lesson_price
        }
        
        if student_data["name"]:
            save_student(student_data)
            return redirect(url_for("ucheniki"))
    
    return render_template("add_student.html")

@app.route("/ученики/редактировать/<int:index>", methods=["GET", "POST"])
def edit_student(index):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    students = load_students()
    
    if index < 0 or index >= len(students):
        return redirect(url_for("ucheniki"))
    
    student = students[index]
    
    if request.method == "POST":
        # Обработка кастомного класса
        class_value = request.form.get("class", "").strip()
        custom_class = request.form.get("custom_class", "").strip()
        
        if class_value == "Другое" and custom_class:
            class_value = custom_class
        
        # Получаем новую стоимость урока
        lesson_price = request.form.get("lesson_price", "0")
        try:
            lesson_price = float(lesson_price)
        except (ValueError, TypeError):
            lesson_price = student.get('lesson_price', 0)
        
        old_name = student["name"]
        new_name = request.form.get("name", "").strip()
        
        # Обновляем данные ученика
        student_data = {
            "name": new_name,
            "class": class_value,
            "city": request.form.get("city", "").strip(),
            "timezone": request.form.get("timezone", "МСК"),
            "parent_name": request.form.get("parent_name", "").strip(),
            "contact": request.form.get("contact", "").strip(),
            "notes": request.form.get("notes", "").strip(),
            "lesson_price": lesson_price
        }
        
        update_student(student['id'], student_data)
        
        # Если имя изменилось, обновляем все связанные данные
        if old_name != new_name:
            # Обновляем уроки
            update_query = "UPDATE lessons SET student_id = %s WHERE student_id = %s"
            execute_query(update_query, (student['id'], student['id']))
        
        return redirect(url_for("ucheniki"))
    
    return render_template("edit_student.html", student=student, index=index)

@app.route("/ученики/удалить/<int:index>", methods=["POST"])
def delete_student(index):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    students = load_students()
    if 0 <= index < len(students):
        student = students[index]
        delete_student_completely(student['id'])
    return redirect(url_for("ucheniki"))

@app.route("/расписание")
@app.route("/расписание/<view_type>")
@app.route("/расписание/<view_type>/<int:year>/<int:period>")
def raspisanie(view_type=None, year=None, period=None):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    # Автоматически обновляем статусы уроков
    auto_update_lesson_statuses()
    
    today = datetime.now()
    
    # Если view_type не указан, используем текущую неделю по умолчанию
    if view_type is None:
        view_type = "week"
        current_year = today.year
        current_week = today.isocalendar()[1]
        return redirect(url_for("raspisanie", view_type="week", year=current_year, period=current_week))
    
    if view_type == "week":
        if year is None or period is None:
            year, period = today.year, today.isocalendar()[1]
        
        # Навигация по неделям
        prev_week = period - 1 if period > 1 else 52
        prev_year = year if period > 1 else year - 1
        next_week = period + 1 if period < 52 else 1
        next_year = year if period < 52 else year + 1
        
        # Получаем данные недели
        week_dates = get_week_dates(year, period)
        slots = load_slots()
        
        # Добавляем занятия к каждому дню
        for date_info in week_dates:
            date_lessons = get_lessons_for_date(date_info['full_date'], slots)
            date_info['lessons'] = date_lessons
        
        # Правильные русские названия месяцев для недели
        week_start = datetime.strptime(f"{year}-W{period:02d}-1", "%Y-W%W-%w")
        week_end = week_start + timedelta(days=6)
        
        month_names = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
            7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        
        start_month = month_names.get(week_start.month, "")
        end_month = month_names.get(week_end.month, "")
        
        if week_start.month == week_end.month:
            week_info = f"с {week_start.day} по {week_end.day} {end_month}"
        else:
            week_info = f"с {week_start.day} {start_month} по {week_end.day} {end_month}"
        
        return render_template("raspisanie.html",
                             view_type="week",
                             week_dates=week_dates,
                             week_info=week_info,
                             year=year,
                             week=period,
                             prev_year=prev_year,
                             prev_week=prev_week,
                             next_year=next_year,
                             next_week=next_week)
    else:  # month view
        if year is None or period is None:
            year, period = today.year, today.month
        
        # Навигация по месяцам
        if period == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, period - 1
        
        if period == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, period + 1
        
        # Получаем календарь месяца
        month_calendar = get_month_calendar(year, period)
        slots = load_slots()
        
        # Добавляем занятия к каждому дню
        for week in month_calendar:
            for day in week:
                if day:
                    date_lessons = get_lessons_for_date(day['date'], slots)
                    day['lessons'] = date_lessons
        
        # Название месяца
        month_names = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
            5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
            9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        month_name = month_names.get(period, "Месяц")
        
        return render_template("raspisanie.html",
                             view_type="month",
                             month_calendar=month_calendar,
                             year=year,
                             month=period,
                             month_name=month_name,
                             prev_year=prev_year,
                             prev_month=prev_month,
                             next_year=next_year,
                             next_month=next_month)

@app.route("/админ/очистить-расписание", methods=["POST"])
def clear_schedule():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Полная очистка расписания"""
    success, message = clear_all_lessons()
    if success:
        return f"<script>alert('{message}'); window.location.href='/расписание';</script>"
    else:
        return f"<script>alert('Ошибка: {message}'); window.location.href='/расписание';</script>"

@app.route("/добавить-занятие", methods=["GET", "POST"])
def add_slot():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    students = load_students()
    
    if request.method == "POST":
        subject = request.form.get("subject")
        if subject == "Другое":
            subject = request.form.get("custom_subject", "Урок")
        
        # Получаем длительность урока
        lesson_duration = request.form.get("lesson_duration", "60")
        try:
            lesson_duration = int(lesson_duration)
            if lesson_duration < 10:
                lesson_duration = 60
            elif lesson_duration > 300:
                lesson_duration = 300
        except (ValueError, TypeError):
            lesson_duration = 60

        lesson_data = {
            "id": generate_slot_id(),
            "date": request.form.get("specific_date"),
            "time": request.form.get("time"),
            "student": request.form.get("student_name"),
            "subject": subject,
            "status": "scheduled",
            "from_template": False,
            "lesson_duration": lesson_duration
        }
        
        create_lesson(lesson_data)
        return redirect(url_for("raspisanie"))
    
    return render_template("add_slot.html", students=students)

@app.route("/шаблон-недели", methods=["GET", "POST"])
def shablon_nedeli():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    students = load_students()
    template = load_template_week()
    
    if request.method == "POST":
        # Проверяем, какое действие выполняется
        if 'edit_index' in request.form:
            # Редактирование существующего урока
            try:
                edit_index = int(request.form.get('edit_index'))
                
                # Получаем длительность урока для редактирования
                edit_lesson_duration = request.form.get("edit_lesson_duration", "60")
                try:
                    edit_lesson_duration = int(edit_lesson_duration)
                    if edit_lesson_duration < 10:
                        edit_lesson_duration = 60
                    elif edit_lesson_duration > 300:
                        edit_lesson_duration = 300
                except (ValueError, TypeError):
                    edit_lesson_duration = 60

                lesson_data = {
                    "day": request.form.get("edit_day"),
                    "time": request.form.get("edit_time"),
                    "student": request.form.get("edit_student"),
                    "subject": request.form.get("edit_subject"),
                    "start_date": request.form.get("edit_start_date", ""),
                    "end_date": request.form.get("edit_end_date", ""),
                    "lesson_type": request.form.get("edit_lesson_type", "regular"),
                    "lesson_duration": edit_lesson_duration
                }
                update_template_lesson(edit_index, lesson_data)
            except (ValueError, IndexError):
                pass
        else:
            # Добавление нового урока
            subject = request.form.get("subject")
            if subject == "Другое":
                subject = request.form.get("custom_subject", "Урок")
            
            # Получаем длительность урока
            lesson_duration = request.form.get("lesson_duration", "60")
            try:
                lesson_duration = int(lesson_duration)
                if lesson_duration < 10:
                    lesson_duration = 60
                elif lesson_duration > 300:
                    lesson_duration = 300
            except (ValueError, TypeError):
                lesson_duration = 60

            lesson_data = {
                "day": request.form.get("day"),
                "time": request.form.get("time"),
                "student": request.form.get("student_name"),
                "subject": subject,
                "start_date": request.form.get("start_date", ""),
                "end_date": request.form.get("end_date", ""),
                "lesson_type": request.form.get("lesson_type", "regular"),
                "lesson_duration": lesson_duration
            }
            
            # Добавляем урок в шаблон
            add_template_lesson(lesson_data)
        
        return redirect(url_for("shablon_nedeli"))
    
    return render_template("shablon_nedeli.html", students=students, template=template)

@app.route("/шаблон-недели/удалить/<int:index>", methods=["POST"])
def delete_template_lesson_route(index):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Удаление урока из шаблона недели"""
    print(f" Удаляем урок из шаблона с индексом: {index}")
    success = delete_template_lesson(index)
    
    if success:
        print(f"✅ Урок {index} успешно удален из шаблона")
    else:
        print(f"❌ Ошибка удаления урока {index} из шаблона")
    
    return redirect(url_for("shablon_nedeli"))

@app.route("/шаблон-недели/урок/<int:index>/редактировать", methods=["GET", "POST"])
def edit_template_lesson_page(index):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Редактирование урока в шаблоне недели на отдельной странице"""
    template = load_template_week()
    students = load_students()
    
    if index < 0 or index >= len(template):
        return "Урок не найден", 404
    
    lesson = template[index]
    
    if request.method == "POST":
        # Обработка кастомного предмета
        subject = request.form.get("subject")
        if subject == "Другое":
            subject = request.form.get("custom_subject", "Урок")
        
        # Получаем длительность урока
        lesson_duration = request.form.get("lesson_duration", "60")
        try:
            lesson_duration = int(lesson_duration)
            if lesson_duration < 10:
                lesson_duration = 60
            elif lesson_duration > 300:
                lesson_duration = 300
        except (ValueError, TypeError):
            lesson_duration = 60

        lesson_data = {
            "day": request.form.get("day"),
            "time": request.form.get("time"),
            "student": request.form.get("student"),
            "subject": subject,
            "start_date": request.form.get("start_date", ""),
            "end_date": request.form.get("end_date", ""),
            "lesson_type": request.form.get("lesson_type", "regular"),
            "lesson_duration": lesson_duration
        }
        
        success = update_template_lesson(index, lesson_data)
        if success:
            return f"<script>alert('Урок в шаблоне обновлен!'); window.location.href='/шаблон-недели';</script>"
        else:
            return "Ошибка обновления урока", 500
    
    return render_template("edit_template_lesson.html", lesson=lesson, students=students, index=index)

@app.route("/применить-шаблон", methods=["POST"])
def apply_template_week():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Применить шаблон недели к основному расписанию с учетом периодов"""
    try:
        added_count = apply_template_to_schedule_with_periods()
        
        if added_count > 0:
            message = f'Добавлено {added_count} занятий с учетом указанных периодов!'
        else:
            message = 'Новые занятия не добавлены (возможно, все уроки уже существуют)'
        
        return f"<script>alert('{message}'); window.location.href='/шаблон-недели';</script>"
        
    except Exception as e:
        return f"<script>alert('Ошибка применения шаблона: {e}'); window.location.href='/шаблон-недели';</script>"

@app.route("/оплата")
@app.route("/оплата/<int:year>/<int:month>")
def oplata(year=None, month=None):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    # Убираем медленную функцию!
    auto_update_lesson_statuses()

    # Устанавливаем текущий месяц
    if year is None or month is None:
        today = datetime.now()
        year, month = today.year, today.month
    
    # Навигация по месяцам
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    
    # Загружаем только основные данные
    students = load_students()
    
    # ОПТИМИЗИРОВАННАЯ ВЕРСИЯ - получаем все балансы одним запросом
    balances = {}
    balances_query = """
        SELECT 
            s.name,
            s.lesson_price,
            COALESCE(SUM(CASE WHEN p.amount > 0 THEN p.amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN p.amount < 0 THEN ABS(p.amount) ELSE 0 END), 0) as total_spent,
            COALESCE(SUM(p.amount), 0) as balance
        FROM students s
        LEFT JOIN payments p ON s.id = p.student_id
        GROUP BY s.id, s.name, s.lesson_price
        ORDER BY s.name
    """

    balances_result = execute_query(balances_query, fetch=True)

    # Отдельно считаем завершенные уроки
    lessons_count_query = """
        SELECT s.name, COUNT(l.id) as lessons_taken
        FROM students s
        LEFT JOIN lessons l ON s.id = l.student_id AND l.status = 'completed'
        GROUP BY s.id, s.name
    """
    lessons_counts = execute_query(lessons_count_query, fetch=True)

    # Создаем словарь с количеством уроков
    lessons_dict = {row['name']: row['lessons_taken'] for row in lessons_counts}

    for row in balances_result:
        balances[row['name']] = {
            'balance': float(row['balance']),
            'lesson_price': float(row['lesson_price']) if row['lesson_price'] else 0,
            'total_paid': float(row['total_paid']),
            'total_spent': float(row['total_spent']),
            'lessons_taken': lessons_dict.get(row['name'], 0)  # Берем из отдельного запроса
        }
    
    # Настоящий финансовый обзор
    financial_overview = get_financial_overview()
    
    # Название месяца
    month_names = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    current_month_name = month_names.get(month, "Месяц")
    
    # Получаем семейные данные
    families = get_families()
    families_data = {}

    for parent_name, children in families.items():
        family_balance = get_family_balance(parent_name)
        
        families_data[parent_name] = {
            'children': children,
            'balance': family_balance['family_balance'],
            'total_paid': family_balance['total_family_paid'],
            'total_spent': family_balance['total_family_spent']
        }

    return render_template("oplata.html", 
                         students=students,
                         balances=balances,
                         financial_overview=financial_overview,
                         predicted_income=get_predicted_income_current_month(),
                         actual_income=get_actual_income_current_month(),
                         student_detailed_stats=get_month_student_detailed_stats(year, month),
                         current_month_name=current_month_name,
                         current_year=year,
                         prev_year=prev_year, 
                         prev_month=prev_month,
                         next_year=next_year, 
                         next_month=next_month,
                         families=families_data)

@app.route("/добавить-платеж", methods=["GET", "POST"])
def add_payment_page():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    if request.method == "GET":
        # Показываем страницу добавления платежа
        students = load_students()
        families = get_families()
        return render_template("add_payment.html", students=students, families=families)
    
    # Обработка POST запроса
    payment_type = request.form.get("payment_type", "student")
    recipient = request.form.get("recipient")
    amount = float(request.form.get("amount", 0))
    description = request.form.get("description", "Пополнение баланса")
    payment_date = request.form.get("payment_date")
    
    if payment_type == "family":
        # Семейный платеж
        if recipient and amount > 0:
            add_family_payment(recipient, amount, description)
    else:
        # Обычный платеж ученику
        if recipient and amount > 0:
            add_payment(recipient, amount, description, payment_date)
    
    return redirect(url_for("oplata"))

@app.route("/история-платежей")
@app.route("/история-платежей/<student_name>")
def payment_history_page(student_name=None):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Страница истории платежей"""
    students = load_students()
    
    if not student_name:
        # Показываем выбор ученика
        return render_template("payment_history.html", students=students)
    
    # Показываем историю конкретного ученика
    payments = get_student_payment_history(student_name)
    balance = get_student_balance(student_name)
    
    # Форматируем даты для отображения
    for payment in payments:
        try:
            if payment['date']:
                date_obj = datetime.fromisoformat(payment['date'])
                payment['date_formatted'] = date_obj.strftime('%d.%m.%Y')
            else:
                payment['date_formatted'] = payment['date']
        except:
            payment['date_formatted'] = payment['date']
    
    return render_template("payment_history.html", 
                         students=students,
                         student_name=student_name,
                         payments=payments,
                         total_paid=balance.get('total_paid', 0),
                         total_spent=balance.get('total_spent', 0),
                         current_balance=balance.get('balance', 0),
                         lessons_taken=balance.get('lessons_taken', 0))

@app.route("/обнулить-баланс/<student_name>", methods=["POST"])
def reset_balance_route(student_name):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    success = reset_student_balance(student_name)
    if success:
        return f"<script>alert('Баланс ученика {student_name} обнулен!'); window.location.href='/оплата';</script>"
    else:
        return f"<script>alert('Ошибка при обнулении баланса'); window.location.href='/оплата';</script>"

@app.route("/нагрузка")
def nagruzka():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    """Главная страница нагрузки"""
    return render_template("nagruzka.html")

@app.route("/настройка-слотов", methods=["GET", "POST"])
def setup_slots():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Страница настройки доступных слотов"""
    if request.method == "POST":
        try:
            slots = load_available_slots()
            
            add_type = request.form.get("add_type")
            time_scope = request.form.get("time_scope")
            slot_duration = int(request.form.get("slot_duration", 60))
            slot_gap = int(request.form.get("slot_gap", 0))
            
            new_slots = []
            
            if add_type == "single":
                # Добавление одного слота
                day = request.form.get("single_day")
                time = request.form.get("single_time")
                
                if day and time:
                    new_slot_data = {
                        "day": day,
                        "time": time,
                        "duration": slot_duration,
                        "type": time_scope
                    }
                    create_available_slot(new_slot_data)
            
            else:
                # Добавление группы слотов
                selected_days = request.form.getlist("group_days")
                start_time = request.form.get("time_start")
                end_time = request.form.get("time_end")
                
                if selected_days and start_time and end_time:
                    # Генерируем временные слоты
                    time_slots = generate_time_slots(start_time, end_time, slot_duration, slot_gap)
                    
                    for day in selected_days:
                        for time_slot in time_slots:
                            new_slot_data = {
                                "day": day,
                                "time": time_slot,
                                "duration": slot_duration,
                                "type": time_scope
                            }
                            create_available_slot(new_slot_data)
        
        except Exception as e:
            print(f"Ошибка при добавлении слотов: {e}")
        
        return redirect(url_for("setup_slots"))
    
    # GET запрос - показываем форму
    slots = load_available_slots()
    return render_template("setup_slots.html", slots=slots)

@app.route("/удалить-слот/<int:slot_id>", methods=["POST"])
def delete_slot(slot_id):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Удаление слота"""
    delete_available_slot(slot_id)
    return redirect(url_for("setup_slots"))

@app.route("/api/delete-slot/<slot_id>", methods=["POST"])
def delete_slot_by_id(slot_id):
    """Удаление слота по ID через API"""
    print(f"Удаляем слот с ID: {slot_id}")
    
    # Находим индекс слота в списке
    slots = load_available_slots()
    slot_index = None
    
    for i, slot in enumerate(slots):
        if slot.get('id') == slot_id:
            slot_index = i
            break
    
    if slot_index is not None:
        success = delete_available_slot(slot_index)
        if success:
            return {"success": True, "message": "Слот удален"}
        else:
            return {"success": False, "message": "Ошибка удаления"}, 500
    else:
        return {"success": False, "message": "Слот не найден"}, 404

@app.route("/schedule/lesson/<lesson_id>/edit", methods=["GET", "POST"])
def edit_lesson_from_schedule(lesson_id):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    students = load_students()
    lesson = get_lesson_by_id(lesson_id)
    
    if not lesson:
        return render_template("edit_lesson.html", 
                             lesson=None, 
                             students=students, 
                             error="Урок не найден")
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "cancel":
            # Отмена урока с возвратом денег
            lesson = get_lesson_by_id(lesson_id)
            if lesson and lesson.get('status') == 'completed':
                # Если урок был проведен - возвращаем деньги
                student = get_student_by_name(lesson['student'])
                if student:
                    lesson_price = float(student['lesson_price']) if student['lesson_price'] else 0
                    
                    # Создаем возвратный платеж
                    if lesson_price > 0:
                        refund_query = """
                            INSERT INTO payments (id, student_id, amount, payment_type, description, lesson_id, payment_date, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """
                        refund_id = generate_slot_id()
                        execute_query(refund_query, (
                            refund_id, student['id'], lesson_price, 'refund', 
                            f"Возврат за отмененный урок {lesson_id}", lesson_id
                        ))
                        print(f"✅ Возвращено {lesson_price} руб. за отмененный урок {lesson_id}")
                    
                    # Убираем отметку об оплате
                    unpaid_query = "UPDATE lessons SET is_paid = false WHERE id = %s"
                    execute_query(unpaid_query, (lesson_id,))
            
            # Отменяем урок
            update_lesson_status(lesson_id, 'cancelled')
            return redirect(url_for("raspisanie"))
        
        elif action == "save":
            # Сохранение изменений
            new_date = request.form.get("date")
            new_time = request.form.get("time") 
            new_student = request.form.get("student")
            new_subject = request.form.get("subject")
            
            # Обработка кастомного предмета
            if new_subject == "Другое":
                new_subject = request.form.get("custom_subject", "Урок")
            
            # Получаем длительность урока
            lesson_duration = request.form.get("lesson_duration", "60")
            try:
                lesson_duration = int(lesson_duration)
                if lesson_duration < 10:
                    lesson_duration = 60
                elif lesson_duration > 300:
                    lesson_duration = 300
            except (ValueError, TypeError):
                lesson_duration = 60
            
            lesson_data = {
                'date': new_date,
                'time': new_time,
                'student': new_student,
                'subject': new_subject,
                'lesson_duration': lesson_duration
            }
            
            update_lesson(lesson_id, lesson_data)
            return redirect(url_for("raspisanie"))
        
        elif action == "delete":
            # Полное удаление урока
            print(f"Удаляем урок с ID: {lesson_id}")
            success = delete_lesson(lesson_id)
            print(f"Результат удаления: {success}")
            return redirect(url_for("raspisanie"))
        
            # Добавь эту проверку:
            if success:
                print(f"Урок {lesson_id} успешно удален")
            else:
                print(f"Ошибка: урок {lesson_id} не был удален")
            
            return redirect(url_for("raspisanie"))
    
    return render_template("edit_lesson.html", lesson=lesson, students=students)

def generate_time_slots(start_time, end_time, duration, gap):
    """Генерация временных слотов"""
    slots = []
    
    # Парсим время начала и конца
    start_hour, start_minute = map(int, start_time.split(':'))
    end_hour, end_minute = map(int, end_time.split(':'))
    
    # Переводим в минуты
    start_minutes = start_hour * 60 + start_minute
    end_minutes = end_hour * 60 + end_minute
    
    # Генерируем слоты
    current_minutes = start_minutes
    while current_minutes + duration <= end_minutes:
        hours = current_minutes // 60
        minutes = current_minutes % 60
        time_str = f"{hours:02d}:{minutes:02d}"
        slots.append(time_str)
        
        # Переходим к следующему слоту
        current_minutes += duration + gap
    
    return slots

# Обработка ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html'), 500

@app.route("/добавить-пробный-урок", methods=["GET", "POST"])
def add_trial_lesson_route():
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    if request.method == "GET":
        return render_template("add_trial_lesson.html")
    
    # Обработка POST запроса
    try:
        date = request.form.get('date')
        time = request.form.get('time') 
        student_name = request.form.get('student_name', '').strip()
        subject = request.form.get('subject', 'Пробный урок')
        lesson_duration = int(request.form.get('lesson_duration', 60))
        
        if not date or not time or not student_name:
            return jsonify({"success": False, "error": "Заполните обязательные поля"}), 400
        
        # Создаем пробный урок
        lesson_data = {
            "id": generate_slot_id(),
            "date": date,
            "time": time,
            "student": student_name,
            "subject": subject,
            "status": "scheduled",
            "lesson_type": "trial",
            "from_template": False,
            "lesson_duration": lesson_duration
        }
        
        lesson_id = create_lesson(lesson_data)
        
        return f"<script>alert('Пробный урок с {student_name} добавлен на {date} в {time}!'); window.location.href='/расписание';</script>"
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# API ДЛЯ НАГРУЗКИ
# ============================================================================

@app.route("/api/available-slots")
def get_available_slots_api():
    """API для получения доступных слотов"""
    slots = load_available_slots()
    return jsonify(slots)

@app.route("/api/template-week")
def get_template_week_api():
    """API для получения шаблона недели"""
    template = load_template_week()
    return jsonify(template)

@app.route("/api/week-schedule/<int:year>/<int:week>")
def get_week_schedule_api(year, week):
    """API для получения расписания конкретной недели"""
    slots = load_slots()
    
    # Получаем даты недели
    week_dates = get_week_dates(year, week)
    week_schedule = []
    
    # Фильтруем уроки по датам недели
    for date_info in week_dates:
        date_str = date_info['full_date']
        day_lessons = get_lessons_for_date(date_str, slots)
        
        for lesson in day_lessons:
            week_schedule.append({
                'date': date_str,
                'time': lesson['time'],
                'student': lesson['student'],
                'subject': lesson['subject'],
                'status': lesson.get('status', 'scheduled'),
                'lesson_type': lesson.get('lesson_type', 'regular')
            })
    
    return jsonify(week_schedule)

@app.route("/restore-lesson/<lesson_id>", methods=["POST"])
def restore_lesson(lesson_id):
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    """Восстановить отмененный урок"""
    print(f"🔄 Восстанавливаем урок {lesson_id}")
    
    # Проверяем, что урок действительно отменен
    lesson = get_lesson_by_id(lesson_id)
    if not lesson:
        return jsonify({"success": False, "error": "Урок не найден"}), 404
    
    if lesson.get('status') != 'cancelled':
        return jsonify({"success": False, "error": "Урок не отменен"}), 400
    
    # Восстанавливаем урок
    restore_query = "UPDATE lessons SET status = 'scheduled' WHERE id = %s"
    result = execute_query(restore_query, (lesson_id,))
    
    if result is not None:
        print(f"✅ Урок {lesson_id} восстановлен")
        return jsonify({"success": True, "message": "Урок восстановлен"})
    else:
        print(f"❌ Ошибка восстановления урока {lesson_id}")
        return jsonify({"success": False, "error": "Ошибка восстановления"}), 500

@app.route("/создать-аккаунты-учеников", methods=["GET", "POST"])
def create_existing_student_accounts():
    """Создать аккаунты для существующих учеников"""
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    if request.method == "POST":
        # Получаем всех учеников без аккаунтов
        students_query = """
            SELECT s.id, s.name, s.created_at, s.parent_name
            FROM students s
            LEFT JOIN user_accounts ua ON s.id = ua.student_id
            WHERE ua.id IS NULL
            ORDER BY s.name
        """
        students_without_accounts = execute_query(students_query, fetch=True)
        
        created_count = 0
        results = []
        
        for student in students_without_accounts:
            try:
                student_id = student['id']
                student_name = student['name']
                registration_time = student['created_at']
                
                # Создаем аккаунт
                login, password = create_user_account(student_id, student_name, registration_time)
                
                results.append({
                    'name': student_name,
                    'login': login,
                    'password': password,
                    'status': 'успешно'
                })
                created_count += 1
                
            except Exception as e:
                results.append({
                    'name': student['name'],
                    'login': '',
                    'password': '',
                    'status': f'ошибка: {e}'
                })
        
        return render_template("create_accounts_result.html", 
                             results=results, 
                             created_count=created_count)
    
    # GET - показываем список учеников без аккаунтов
    students_query = """
        SELECT s.id, s.name, s.created_at, s.parent_name
        FROM students s
        LEFT JOIN user_accounts ua ON s.id = ua.student_id
        WHERE ua.id IS NULL
        ORDER BY s.name
    """
    students_without_accounts = execute_query(students_query, fetch=True)
    
    return render_template("create_accounts.html", 
                         students=students_without_accounts)

@app.route("/пересоздать-все-аккаунты", methods=["GET", "POST"])
def recreate_all_accounts():
    """Пересоздать аккаунты для ВСЕХ учеников"""
    if not session.get('admin_logged_in'):
        return redirect("http://127.0.0.1:8080/admin-auth")
    
    if request.method == "POST":
        # 1. Удаляем ВСЕ старые аккаунты (кроме админа)
        delete_query = "DELETE FROM user_accounts WHERE role IN ('student', 'parent')"
        execute_query(delete_query)
        print("🗑️ Удалены все старые аккаунты учеников и родителей")
        
        # 2. Получаем всех учеников
        students_query = "SELECT id, name, created_at, parent_name FROM students ORDER BY name"
        all_students = execute_query(students_query, fetch=True)
        
        created_count = 0
        results = []
        
        # 3. Создаем новые аккаунты для каждого ученика
        for student in all_students:
            try:
                student_id = student['id']
                student_name = student['name']
                registration_time = student['created_at']
                
                # Создаем аккаунт
                login, password = create_user_account(student_id, student_name, registration_time)
                
                results.append({
                    'name': student_name,
                    'login': login,
                    'password': password,
                    'parent_name': student['parent_name'],
                    'status': 'успешно'
                })
                created_count += 1
                
                print(f"✅ {student_name}: {login} / {password}")
                
            except Exception as e:
                results.append({
                    'name': student['name'],
                    'login': '',
                    'password': '',
                    'parent_name': student['parent_name'],
                    'status': f'ошибка: {e}'
                })
                print(f"❌ Ошибка для {student['name']}: {e}")
        
        print(f"\n🎉 ГОТОВО! Создано {created_count} аккаунтов!")
        
        # Возвращаем результат
        results_text = f"Создано {created_count} аккаунтов!\\n\\n"
        for result in results:
            if result['status'] == 'успешно':
                results_text += f"✅ {result['name']}: {result['login']} / {result['password']}\\n"
        
        return f"<script>alert('{results_text}'); window.location.href='/';</script>"
    
    # GET - показываем кнопку подтверждения
    students_count_query = "SELECT COUNT(*) as count FROM students"
    students_count = execute_query(students_count_query, fetch_one=True)['count']
    
    return f"""
    <html>
    <head><title>Пересоздание аккаунтов</title></head>
    <body style="font-family: Arial; padding: 50px; text-align: center;">
        <h1>⚠️ Пересоздание всех аккаунтов</h1>
        <p>Будут пересозданы аккаунты для <strong>{students_count} учеников</strong></p>
        <p style="color: red;">ВНИМАНИЕ: Все старые логины/пароли будут удалены!</p>
        
        <form method="POST" style="margin-top: 30px;">
            <button type="submit" style="padding: 15px 30px; font-size: 18px; background: #e74c3c; color: white; border: none; border-radius: 8px; cursor: pointer;">
                Да, пересоздать все аккаунты
            </button>
        </form>
        
        <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #95a5a6; color: white; text-decoration: none; border-radius: 8px;">
            Отмена
        </a>
    </body>
    </html>
    """

@app.route("/admin-logout")
def admin_logout():
    """Выход из админской панели"""
    session.clear()  # Очищаем всю сессию
    return redirect("http://127.0.0.1:8080/admin-auth")

# Запуск приложения
if __name__ == "__main__":
    initialize_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
