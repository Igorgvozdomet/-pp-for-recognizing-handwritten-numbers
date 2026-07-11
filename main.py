import flet as ft
from flet.canvas import Canvas, Line
import numpy as np
import cv2
import os

from database import init_db, register_user, check_user
from model import predict_digit
from preprocess import preprocess_canvas

feedback_visible = False
current_processed = None

def main(page: ft.Page):
    # ===== ФУНКЦИИ ОБРАТНОЙ СВЯЗИ =====
    def show_correction_buttons():
        correction_row.visible = True
        wrong_button.visible = False
        result_text.value += " | Выберите правильную цифру:"
        result_text.update()
        correction_row.update()
        wrong_button.update()

    def hide_correction_buttons():
        correction_row.visible = False
        wrong_button.visible = True
        correction_row.update()
        wrong_button.update()

    def save_correction(correct_label):
        os.makedirs(f"corrections/{correct_label}", exist_ok=True)
        count = len(os.listdir(f"corrections/{correct_label}"))
        cv2.imwrite(f"corrections/{correct_label}/{count}.png", drawing_array)
        

        hide_correction_buttons()
        canvas.shapes.clear()
        drawing_array.fill(0)
        result_text.value = ""
        wrong_button.visible = False
        hide_correction_buttons()
        canvas.update()
        result_text.update()
        wrong_button.update()
        
        show_snackbar(f"Сохранено как {correct_label}! Спасибо!")

        
        # Авто-дообучение каждые 50
        total = 0
        for i in range(10):
            folder = f"corrections/{i}"
            if os.path.exists(folder):
                total += len(os.listdir(folder))
        
        if total > 0 and total % 50 == 0:
            show_snackbar(f"Собрано {total} примеров. Дообучаю модель...")
            page.update()
            import subprocess
            subprocess.run(["python", "retrain.py"], capture_output=True)
            from model import reload_model
            reload_model()
            show_snackbar("Готово! Модель обновлена.")
        
        result_text.value = ""
        result_text.update()
        wrong_button.update()
        page.update()

    # ===== КНОПКИ ОБРАТНОЙ СВЯЗИ =====
    wrong_button = ft.OutlinedButton(
        "Неверно",
        on_click=lambda _: show_correction_buttons(),
        visible=False
    )

    correction_buttons = []
    for i in range(10):
        btn = ft.ElevatedButton(
            str(i),
            on_click=lambda _, label=i: save_correction(label),
            width=40, height=40
        )
        correction_buttons.append(btn)

    correction_row = ft.Row(
        correction_buttons,
        alignment=ft.MainAxisAlignment.CENTER,
        visible=False
    )
    

    
    # ===== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ =====
    init_db()
    
    # ===== НАСТРОЙКИ ОКНА (АВТОРИЗАЦИЯ) =====
    page.title = "Регистрация с авторизацией"
    page.theme_mode = "dark"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window.resizable = False
    page.window.width = 350
    page.window.height = 400
    
    # ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
    def show_snackbar(message):
        snack = ft.SnackBar(ft.Text(message))
        page.overlay.append(snack)
        snack.open = True
        page.update()
    
    # ===== ФУНКЦИИ АВТОРИЗАЦИИ =====
    def register(e):
        if user_login.value and user_pass.value:
            success = register_user(user_login.value, user_pass.value)
            if success:
                user_login.value = ''
                user_pass.value = ''
                show_snackbar('Вы зарегистрированы!')
            else:
                show_snackbar('Пользователь уже существует!')
        page.update()
    
    def validate(e):
        if all([user_login.value, user_pass.value]):
            btn_reg.disabled = False
            btn_auth.disabled = False
        else:
            btn_reg.disabled = True
            btn_auth.disabled = True
        page.update()
    
    def auth_user(e):
        if check_user(user_login.value, user_pass.value):
            user_login.value = ''
            user_pass.value = ''
            show_drawing()
        else:
            show_snackbar('Данные введены неверно!')
    
    # ===== ЭЛЕМЕНТЫ АВТОРИЗАЦИИ =====
    user_login = ft.TextField(label='Логин', width=200, on_change=validate)
    user_pass = ft.TextField(label='Пароль', password=True, width=200, on_change=validate)
    btn_reg = ft.OutlinedButton('Зарегистрироваться', width=200, on_click=register, disabled=True)
    btn_auth = ft.OutlinedButton('Авторизоваться', width=200, on_click=auth_user, disabled=True)
    
    panel_register = ft.Row(
        [ft.Column([
            ft.Text('Регистрация', size=20, weight=500),
            user_login,
            user_pass,
            btn_reg
        ])],
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    panel_auth = ft.Row(
        [ft.Column([
            ft.Text('Авторизация', size=20, weight=500),
            user_login,
            user_pass,
            btn_auth
        ])],
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    def navigate(e):
        index = page.navigation_bar.selected_index
        page.clean()
        if index == 0:
            page.add(panel_register)
        elif index == 1:
            page.add(panel_auth)
        page.update()
    
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.VERIFIED_USER, label='Регистрация'),
            ft.NavigationBarDestination(icon=ft.Icons.VERIFIED_USER_OUTLINED, label='Авторизация')
        ],
        on_change=navigate
    )
    
    page.add(panel_register)
    
    # ===== ЭЛЕМЕНТЫ РИСОВАНИЯ =====
    canvas = Canvas(width=400, height=400)
    drawing_array = np.zeros((400, 400), dtype=np.uint8)  # чёрный массив

    
    canvas_container = ft.Container(
        content=canvas,
        width=400,
        height=400,
        bgcolor=ft.colors.BLACK,
        border_radius=10,
    )
    
    is_drawing = False
    last_x = 0
    last_y = 0
    
    def start_draw(e: ft.DragStartEvent):
        nonlocal is_drawing, last_x, last_y
        is_drawing = True
        last_x = e.local_x
        last_y = e.local_y
    
    def draw(e: ft.DragUpdateEvent):
        nonlocal last_x, last_y
        if is_drawing:
            # Рисуем на canvas Flet
            canvas.shapes.append(
                Line(
                    x1=last_x, y1=last_y,
                    x2=e.local_x, y2=e.local_y,
                    paint=ft.Paint(
                        color=ft.colors.WHITE,
                        stroke_width=40,
                        stroke_cap=ft.StrokeCap.ROUND,
                    )
                )
            )
            
            # Рисуем ту же линию на numpy-массиве
            cv2.line(drawing_array, 
                    (int(last_x), int(last_y)), 
                    (int(e.local_x), int(e.local_y)), 
                    255, 40)
            
            last_x = e.local_x
            last_y = e.local_y
            canvas.update()
    
    def stop_draw(e: ft.DragEndEvent):
        nonlocal is_drawing
        is_drawing = False
    
    result_text = ft.Text("", size=24, weight=700)
    def clear_canvas(e):
        canvas.shapes.clear()
        drawing_array.fill(0)
        result_text.value = ""
        wrong_button.visible = False
        hide_correction_buttons()
        canvas.update()
        result_text.update()
        page.update()


    def ai_module(e):
        global current_processed
        
        img_array = cv2.cvtColor(drawing_array, cv2.COLOR_GRAY2BGR)
        processed = preprocess_canvas(img_array)
        
        if processed is None:
            result_text.value = "Холст пуст!"
            wrong_button.visible = False
            hide_correction_buttons()
        else:
            current_processed = processed
            digit, confidence = predict_digit(processed)
            result_text.value = f"Цифра: {digit} ({confidence:.1f}%)"
            wrong_button.visible = True  # показываем кнопку "Неверно"
            hide_correction_buttons()    # скрываем цифры, если были открыты
        
        result_text.update()
        wrong_button.update()
        page.update()

    drawing_area = ft.GestureDetector(
        content=canvas_container,
        on_pan_start=start_draw,
        on_pan_update=draw,
        on_pan_end=stop_draw,
        drag_interval=10,
    )
    
    column_drawing = ft.Column([
        ft.Text("Нарисуйте цифру:", size=20, weight=500),
        drawing_area,
        ft.Row([
            ft.ElevatedButton("Очистить", on_click=clear_canvas),
            ft.ElevatedButton("Распознать", on_click=ai_module),
            ft.ElevatedButton("Выйти", on_click=lambda _: show_login()),
        ], alignment=ft.MainAxisAlignment.CENTER),
        result_text,
        wrong_button,      # ← кнопка "Неверно"
        correction_row,    # ← кнопки 0-9
    ],
    alignment=ft.MainAxisAlignment.CENTER,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def show_drawing():
        page.window.width = 500
        page.window.height = 650
        page.window.resizable = False
        page.navigation_bar = None
        page.clean()
        page.add(column_drawing)
        page.update()
    
    def show_login():
        page.window.width = 350
        page.window.height = 400
        page.window.resizable = False
        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.VERIFIED_USER, label='Регистрация'),
                ft.NavigationBarDestination(icon=ft.Icons.VERIFIED_USER_OUTLINED, label='Авторизация')
            ],
            on_change=navigate
        )
        page.clean()
        page.add(panel_register)
        page.update()


ft.app(target=main)
