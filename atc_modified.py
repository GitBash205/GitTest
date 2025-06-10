import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import os
import datetime

class Logger:
    def __init__(self):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def write_log(self, message):
        """Записывает сообщение в лог-файл"""
        now = datetime.datetime.now()
        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H.%M.%S")

        log_filename = f"log_{date_str}_{time_str.replace('.', '.')}.txt"
        log_path = os.path.join(self.log_dir, log_filename)

        log_entry = f"{date_str}_{time_str} {message}"

        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_entry)
            print(f"Лог записан: {log_entry}")
        except Exception as e:
            print(f"Ошибка записи лога: {e}")

    def log_system_start(self, username):
        """Логирует включение системы"""
        self.write_log(f"Включение ИС - Пользователь: {username}")

    def log_system_shutdown(self, username):
        """Логирует выключение системы"""
        self.write_log(f"Выключение ИС - Пользователь: {username}")

    def log_login(self, username, success=True):
        """Логирует попытку входа"""
        status = "успешный" if success else "неуспешный"
        self.write_log(f"Вход в систему ({status}) - Пользователь: {username}")

    def log_operation(self, operation, username, details=""):
        """Логирует операции с данными"""
        message = f"{operation} - Пользователь: {username}"
        if details:
            message += f" - {details}"
        self.write_log(message)


class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Авторизация - Картотека абонентов АТС")
        self.root.geometry("400x300")

        self.root.transient()
        self.root.grab_set()

        self.user_role = None
        self.username = None
        self.logged_in = False
        self.logger = Logger()

        self.create_login_widgets()

    def create_login_widgets(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="Картотека абонентов АТС",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        login_frame = ttk.LabelFrame(main_frame, text="Вход в систему", padding=20)
        login_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(login_frame, text="Логин:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(login_frame, width=25, font=("Arial", 10))
        self.username_entry.grid(row=0, column=1, padx=(10, 0), pady=5)

        ttk.Label(login_frame, text="Пароль:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(login_frame, width=25, show="*", font=("Arial", 10))
        self.password_entry.grid(row=1, column=1, padx=(10, 0), pady=5)

        button_frame = ttk.Frame(login_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        login_btn = ttk.Button(button_frame, text="Войти", command=self.login)
        login_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(button_frame, text="Отмена", command=self.root.quit)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        info_frame = ttk.LabelFrame(main_frame, text="")
        
        info_text = """Администратор: admin / admin123
Пользователь: user / user123"""
        ttk.Label(info_frame, text=info_text, font=("Arial", 9)).pack()

        self.password_entry.bind('<Return>', lambda e: self.login())
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())

        self.username_entry.focus()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль!")
            return

        try:
            conn = sqlite3.connect("ats_database.db")
            cursor = conn.cursor()

            cursor.execute("SELECT username, password, role FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and user[1] == password:
                self.username = user[0]
                self.user_role = user[2]
                self.logged_in = True

                self.logger.log_login(self.username, success=True)
                self.logger.log_system_start(self.username)

                messagebox.showinfo("Успех", f"Добро пожаловать, {self.username}!")
                self.root.destroy()
            else:
                self.logger.log_login(username, success=False)
                messagebox.showerror("Ошибка", "Неверный логин или пароль!")
                self.password_entry.delete(0, tk.END)

        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Ошибка подключения к базе данных: {e}")
        finally:
            if conn:
                conn.close()

    def show(self):
        self.root.mainloop()
        return self.logged_in, self.username, self.user_role


class SubscriberDirectoryGUI:
    def __init__(self, root, username, user_role):
        self.root = root
        self.username = username
        self.user_role = user_role
        self.logger = Logger()

        self.root.title(f"Картотека абонентов АТС - {username} ({user_role})")
        self.root.geometry("1000x700")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.initialize_database()
        self.create_menu()
        self.create_widgets()
        self.load_subscribers()

        if self.user_role != 'admin':
            self.disable_admin_functions()

    def on_closing(self):
        """Обработчик закрытия приложения с логированием"""
        self.logger.log_system_shutdown(self.username)
        self.conn.close()
        self.root.destroy()

    def initialize_database(self):
        self.conn = sqlite3.connect("ats_database.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT,
                subscriber_type TEXT,
                subscription_debt TEXT,
                damage_debt TEXT,
                tariff TEXT
            )
        """)
        self.conn.commit()

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Администрирование", command=self.show_admin_panel)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.logout)
        menubar.add_cascade(label="Файл", menu=file_menu)
      
        if self.user_role == 'admin':
            logs_menu = tk.Menu(menubar, tearoff=0)
            logs_menu.add_command(label="Просмотр логов", command=self.show_logs)
            logs_menu.add_command(label="Очистить логов", command=self.clear_logs)
            menubar.add_cascade(label="Логи", menu=logs_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)

    def show_admin_panel(self):
        """Показывает панель администрирования с таблицей абонентов"""
        if self.user_role != 'admin':
            messagebox.showerror("Ошибка", "У вас нет прав администратора!")
            return
            
        admin_window = tk.Toplevel(self.root)
        admin_window.title("Панель администрирования")
        admin_window.geometry("900x600")
        
        
        main_frame = ttk.Frame(admin_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Администрирование системы - Список абонентов", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        admin_tree = ttk.Treeview(tree_frame,
                                columns=("id", "name", "phone", "address", "type", "subscription_debt", "damage_debt", "tariff"),
                                show="headings")

        admin_tree.heading("id", text="ID")
        admin_tree.heading("name", text="ФИО")
        admin_tree.heading("phone", text="Телефон")
        admin_tree.heading("address", text="Адрес")
        admin_tree.heading("type", text="Тип")
        admin_tree.heading("subscription_debt", text="Абонплата")
        admin_tree.heading("damage_debt", text="Повреждения")
        admin_tree.heading("tariff", text="Тариф")

        admin_tree.column("id", width=50)
        admin_tree.column("name", width=150)
        admin_tree.column("phone", width=100)
        admin_tree.column("address", width=150)
        admin_tree.column("type", width=100)
        admin_tree.column("subscription_debt", width=80)
        admin_tree.column("damage_debt", width=100)
        admin_tree.column("tariff", width=100)

        admin_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=admin_tree.yview)
        admin_tree.configure(yscroll=admin_scrollbar.set)

        admin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        admin_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        
        self.cursor.execute("""
            SELECT id, name, phone, address, subscriber_type,
                   subscription_debt, damage_debt, tariff
            FROM subscribers
            ORDER BY name
        """)
        rows = self.cursor.fetchall()

        for row in rows:
            admin_tree.insert("", tk.END, values=row)

        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Обновить список",
                  command=lambda: self.refresh_admin_table(admin_tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Закрыть",
                  command=admin_window.destroy).pack(side=tk.RIGHT, padx=5)

        self.logger.log_operation("Открытие панели администрирования", self.username)

    def refresh_admin_table(self, admin_tree):
        """Обновляет таблицу в панели администрирования"""
        
        for row in admin_tree.get_children():
            admin_tree.delete(row)
        
        
        self.cursor.execute("""
            SELECT id, name, phone, address, subscriber_type,
                   subscription_debt, damage_debt, tariff
            FROM subscribers
            ORDER BY name
        """)
        rows = self.cursor.fetchall()

        for row in rows:
            admin_tree.insert("", tk.END, values=row)

    def show_logs(self):
        """Показывает окно с логами системы"""
        logs_window = tk.Toplevel(self.root)
        logs_window.title("Логи системы")
        logs_window.geometry("800x600")

        text_frame = ttk.Frame(logs_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        log_text = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)

        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        logs_dir = "logs"
        if os.path.exists(logs_dir):
            log_files = sorted([f for f in os.listdir(logs_dir) if f.startswith("log_")], reverse=True)

            for log_file in log_files[:50]: 
                try:
                    with open(os.path.join(logs_dir, log_file), 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        log_text.insert(tk.END, content + "\n")
                except Exception as e:
                    log_text.insert(tk.END, f"Ошибка чтения {log_file}: {e}\n")
        else:
            log_text.insert(tk.END, "Папка с логами не найдена.\n")

        log_text.config(state=tk.DISABLED)

    def clear_logs(self):
        """Очищает все лог-файлы"""
        if messagebox.askyesno("Подтверждение", "Удалить все лог-файлы?\n\nЭто действие нельзя отменить!"):
            logs_dir = "logs"
            if os.path.exists(logs_dir):
                try:
                    for filename in os.listdir(logs_dir):
                        if filename.startswith("log_"):
                            os.remove(os.path.join(logs_dir, filename))

                    self.logger.log_operation("Очистка логов", self.username)
                    messagebox.showinfo("Успех", "Все лог-файлы удалены!")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Ошибка при удалении логов: {e}")

    def logout(self):
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти из программы?"):
            self.logger.log_system_shutdown(self.username)
            self.conn.close()
            self.root.quit()

    def show_about(self):
        about_text = f"""Картотека абонентов АТС

Текущий пользователь: {self.username}
Роль: {self.user_role}

Разработчики:
•  Даниил
•  Лёня

Версия: 2.3"""
        messagebox.showinfo("О программе", about_text)

    def create_widgets(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=5, pady=2)

        self.status_label = ttk.Label(status_frame,
                                     text=f"Пользователь: {self.username} | Роль: {self.user_role}")
        self.status_label.pack(side=tk.LEFT)

        input_frame = ttk.LabelFrame(self.root, text="Данные абонента", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="ФИО:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.name_entry = ttk.Entry(input_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Телефон:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.phone_entry = ttk.Entry(input_frame, width=30)
        self.phone_entry.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Адрес:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.address_entry = ttk.Entry(input_frame, width=30)
        self.address_entry.grid(row=2, column=1, padx=5, pady=2)

        self.subscriber_type = tk.StringVar(value="частный")
        ttk.Label(input_frame, text="Тип абонента:").grid(row=0, column=2, sticky=tk.W, padx=15)
        ttk.Radiobutton(input_frame, text="Частный",
                       variable=self.subscriber_type, value="частный").grid(row=0, column=3, sticky=tk.W)
        ttk.Radiobutton(input_frame, text="Организация",
                       variable=self.subscriber_type, value="организация").grid(row=1, column=3, sticky=tk.W)

        self.subscription_debt = tk.BooleanVar()
        self.damage_debt = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="Задолженность по абонплате",
                       variable=self.subscription_debt).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Checkbutton(input_frame, text="Задолженность за повреждения",
                       variable=self.damage_debt).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)

        ttk.Label(input_frame, text="Тарифный план:").grid(row=2, column=2, sticky=tk.W, padx=15)
        self.tariff_combobox = ttk.Combobox(input_frame,
                                           values=["Базовый", "Расширенный", "Безлимитный"],
                                           state="readonly", width=15)
        self.tariff_combobox.grid(row=2, column=3, padx=5, pady=2, sticky=tk.W)
        self.tariff_combobox.set("Базовый")

        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.add_btn = ttk.Button(button_frame, text="Добавить", command=self.add_subscriber)
        self.add_btn.pack(side=tk.LEFT, padx=5)

        self.update_btn = ttk.Button(button_frame, text="Обновить", command=self.update_subscriber)
        self.update_btn.pack(side=tk.LEFT, padx=5)

        self.delete_btn = ttk.Button(button_frame, text="Удалить", command=self.delete_subscriber)
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Очистить", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(tree_frame,
                                columns=("id", "name", "phone", "address", "type", "subscription_debt", "damage_debt", "tariff"),
                                show="headings")

        self.tree.heading("id", text="ID", command=lambda: self.sort_treeview("id", False))
        self.tree.heading("name", text="ФИО", command=lambda: self.sort_treeview("name", False))
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("address", text="Адрес")
        self.tree.heading("type", text="Тип")
        self.tree.heading("subscription_debt", text="Абонплата")
        self.tree.heading("damage_debt", text="Повреждения")
        self.tree.heading("tariff", text="Тариф")

        self.tree.column("id", width=50)
        self.tree.column("name", width=150)
        self.tree.column("phone", width=100)
        self.tree.column("address", width=150)
        self.tree.column("type", width=100)
        self.tree.column("subscription_debt", width=80)
        self.tree.column("damage_debt", width=100)
        self.tree.column("tariff", width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<ButtonRelease-1>", self.load_selected_subscriber)

    def disable_admin_functions(self):
        """Отключает функции для обычных пользователей"""
        self.delete_btn.config(state='disabled')
        self.update_btn.config(state='disabled')

    def sort_treeview(self, col, reverse):
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]

        try:
            data.sort(key=lambda x: int(x[0]), reverse=reverse)
        except ValueError:
            data.sort(reverse=reverse)

        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)

        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def add_subscriber(self):
        if not self.validate_input():
            return

        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        address = self.address_entry.get().strip()
        subscriber_type = self.subscriber_type.get()
        subscription_debt = "Да" if self.subscription_debt.get() else "Нет"
        damage_debt = "Да" if self.damage_debt.get() else "Нет"
        tariff = self.tariff_combobox.get()

        try:
            self.cursor.execute("""
                INSERT INTO subscribers (name, phone, address, subscriber_type, subscription_debt, damage_debt, tariff)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, phone, address, subscriber_type, subscription_debt, damage_debt, tariff))
            self.conn.commit()

            self.logger.log_operation("Добавление абонента", self.username, f"ФИО: {name}, Телефон: {phone}")

            self.load_subscribers()
            self.clear_fields()
            messagebox.showinfo("Успех", "Абонент успешно добавлен!")

        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Ошибка при добавлении: {e}")

    def validate_input(self):
        if not self.name_entry.get().strip():
            messagebox.showerror("Ошибка", "Поле 'ФИО' обязательно для заполнения!")
            self.name_entry.focus()
            return False

        if not self.phone_entry.get().strip():
            messagebox.showerror("Ошибка", "Поле 'Телефон' обязательно для заполнения!")
            self.phone_entry.focus()
            return False

        return True

    def load_subscribers(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.cursor.execute("""
            SELECT id, name, phone, address, subscriber_type,
                   subscription_debt, damage_debt, tariff
            FROM subscribers
            ORDER BY name
        """)
        rows = self.cursor.fetchall()

        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def load_selected_subscriber(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            values = self.tree.item(selected_item, 'values')
            if values:
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, values[1])
                self.phone_entry.delete(0, tk.END)
                self.phone_entry.insert(0, values[2])
                self.address_entry.delete(0, tk.END)
                self.address_entry.insert(0, values[3])
                self.subscriber_type.set(values[4])
                self.subscription_debt.set(values[5] == "Да")
                self.damage_debt.set(values[6] == "Да")
                self.tariff_combobox.set(values[7])

    def update_subscriber(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите абонента для обновления!")
            return

        if not self.validate_input():
            return

        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        address = self.address_entry.get().strip()
        subscriber_type = self.subscriber_type.get()
        subscription_debt = "Да" if self.subscription_debt.get() else "Нет"
        damage_debt = "Да" if self.damage_debt.get() else "Нет"
        tariff = self.tariff_combobox.get()

        selected_id = self.tree.item(selected_item, 'values')[0]

        try:
            self.cursor.execute("""
                UPDATE subscribers
                SET name=?, phone=?, address=?, subscriber_type=?, subscription_debt=?, damage_debt=?, tariff=?
                WHERE id=?
            """, (name, phone, address, subscriber_type, subscription_debt, damage_debt, tariff, selected_id))
            self.conn.commit()

            self.logger.log_operation("Обновление абонента", self.username, f"ID: {selected_id}, ФИО: {name}")

            self.load_subscribers()
            self.clear_fields()
            messagebox.showinfo("Успех", "Данные абонента обновлены!")

        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Ошибка при обновлении: {e}")

    def delete_subscriber(self):
        if self.user_role != 'admin':
            messagebox.showerror("Ошибка", "У вас нет прав для удаления записей!")
            return

        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите абонента для удаления!")
            return

        values = self.tree.item(selected_item, 'values')
        name = values[1]
        selected_id = values[0]

        if messagebox.askyesno("Подтверждение", f"Удалить абонента '{name}'?\n\nЭто действие нельзя отменить!"):
            try:
                self.cursor.execute("DELETE FROM subscribers WHERE id=?", (selected_id,))
                self.conn.commit()

                self.logger.log_operation("Удаление абонента", self.username, f"ID: {selected_id}, ФИО: {name}")

                self.load_subscribers()
                self.clear_fields()
                messagebox.showinfo("Успех", "Абонент удален!")

            except sqlite3.Error as e:
                messagebox.showerror("Ошибка БД", f"Ошибка при удалении: {e}")

    def clear_fields(self):
        self.name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.subscriber_type.set("частный")
        self.subscription_debt.set(False)
        self.damage_debt.set(False)
        self.tariff_combobox.set("Базовый")


def main():
    login_window = LoginWindow()
    logged_in, username, user_role = login_window.show()

    if logged_in:
        root = tk.Tk()
        app = SubscriberDirectoryGUI(root, username, user_role)
        root.mainloop()
    else:
        print("Авторизация отменена или неуспешна")


if __name__ == "__main__":
    main()
