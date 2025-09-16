import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import datetime
import pytz
import tzlocal
import threading
import os
import winsound
import json
from plyer import notification

class AllInOneClock:
    def __init__(self, master):
        self.master = master
        self.master.title("多功能時鐘")
        
        self.is_floating_mode = False
        self.original_geometry = "500x350"
        self.floating_geometry = "250x100"
        
        self.master.geometry(self.original_geometry)

        self.stop_alarm = False
        self.timer_sound_thread = None
        self.alarm_sound_thread = None
        self.alarms = self.load_alarms()
        
        self.is_24_hour_format = True  # 預設為24小時制

        self.create_menubar()
        
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure("TNotebook", background="SystemButtonFace")
        self.style.configure("TNotebook.Tab", background="SystemButtonFace")
        self.style.map("TNotebook.Tab", background=[("selected", "white")])
        
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.clock_frame = tk.Frame(self.notebook, bg="SystemButtonFace")
        self.notebook.add(self.clock_frame, text="時鐘")
        self.setup_clock_tab()

        self.timer_frame = tk.Frame(self.notebook, bg="SystemButtonFace")
        self.notebook.add(self.timer_frame, text="計時器")
        self.setup_timer_tab()

        self.stopwatch_frame = tk.Frame(self.notebook, bg="SystemButtonFace")
        self.notebook.add(self.stopwatch_frame, text="碼表")
        self.setup_stopwatch_tab()
        
        self.alarm_frame = tk.Frame(self.notebook, bg="SystemButtonFace")
        self.notebook.add(self.alarm_frame, text="鬧鐘")
        self.setup_alarm_tab()
        
        self.create_context_menu()
        
        self.master.bind("<Button-3>", self.show_context_menu)
        
        self.master.bind('<Control-s>', self.start_stopwatch)
        self.master.bind('<Control-p>', self.pause_stopwatch)
        self.master.bind('<Control-r>', self.reset_stopwatch)
        self.master.bind('<Control-t>', self.toggle_mode)
        
        self.update_clock()
        self.update_timer()
        self.update_stopwatch()
        self.check_alarms()
        
    def create_menubar(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)
        help_menu = tk.Menu(self.menubar, tearoff=0, font=("Helvetica", 11))
        self.menubar.add_cascade(label="說明", menu=help_menu)
        help_menu.add_command(label="如何使用", command=self.show_help_window)

    def create_context_menu(self):
        self.menu = tk.Menu(self.master, tearoff=0)
        self.menu.add_command(label="切換到懸浮模式", command=self.toggle_mode, font=("Helvetica", 11, "bold"))
        self.menu.add_separator()
        timezone_menu = tk.Menu(self.menu, tearoff=0)
        self.timezone_var = tk.StringVar()
        self.timezone_options = self.get_common_timezones()
        try:
            self.current_timezone = tzlocal.get_localzone()
        except pytz.UnknownTimeZoneError:
            self.current_timezone = pytz.timezone('UTC')
        
        for tz in self.timezone_options:
            timezone_menu.add_radiobutton(label=tz, variable=self.timezone_var, value=tz, command=self.change_timezone, font=("Helvetica", 10))
        
        self.timezone_var.set(str(self.current_timezone))
        self.menu.add_cascade(label="選擇時區", menu=timezone_menu, font=("Helvetica", 11))
        
        format_menu = tk.Menu(self.menu, tearoff=0)
        self.format_var = tk.StringVar(value="24h")
        format_menu.add_radiobutton(label="24小時制", variable=self.format_var, value="24h", command=self.toggle_format, font=("Helvetica", 10))
        format_menu.add_radiobutton(label="12小時制", variable=self.format_var, value="12h", command=self.toggle_format, font=("Helvetica", 10))
        self.menu.add_cascade(label="選擇時間制", menu=format_menu, font=("Helvetica", 11))

        # Define theme_menu before using it
        theme_menu = tk.Menu(self.menu, tearoff=0)
        self.theme_var = tk.StringVar(value="light")
        theme_menu.add_radiobutton(label="淺色主題", variable=self.theme_var, value="light", command=self.apply_theme, font=("Helvetica", 10))
        theme_menu.add_radiobutton(label="深色主題", variable=self.theme_var, value="dark", command=self.apply_theme, font=("Helvetica", 10))

        self.stopwatch_menu = tk.Menu(self.master, tearoff=0)
        self.stopwatch_start_pause_item = self.stopwatch_menu.add_command(label="開始", command=self.start_stopwatch, font=("Helvetica", 11))
        self.stopwatch_menu.add_command(label="重置", command=self.reset_stopwatch, font=("Helvetica", 11))
        self.stopwatch_menu.add_separator()
        self.stopwatch_menu.add_command(label="切換回一般模式", command=self.toggle_mode, font=("Helvetica", 11, "bold"))
        
        self.floating_menu = tk.Menu(self.master, tearoff=0)
        self.floating_menu.add_command(label="切換回一般模式", command=self.toggle_mode, font=("Helvetica", 11, "bold"))
        self.floating_menu.add_separator()
        self.floating_menu.add_cascade(label="選擇時區", menu=timezone_menu, font=("Helvetica", 11))
        self.floating_menu.add_cascade(label="選擇時間制", menu=format_menu, font=("Helvetica", 11))
        self.floating_menu.add_cascade(label="切換主題", menu=theme_menu, font=("Helvetica", 11))

    def show_context_menu(self, event):
        try:
            if self.is_floating_mode:
                current_tab_id = self.notebook.index(self.notebook.select()) if hasattr(self, 'notebook') else None
                if current_tab_id == 2:  # 碼表分頁
                    if self.stopwatch_running:
                        self.stopwatch_menu.entryconfig(self.stopwatch_start_pause_item, label="暫停", command=self.pause_stopwatch)
                    else:
                        self.stopwatch_menu.entryconfig(self.stopwatch_start_pause_item, label="開始", command=self.start_stopwatch)
                    self.stopwatch_menu.tk_popup(event.x_root, event.y_root)
                else:
                    self.floating_menu.tk_popup(event.x_root, event.y_root)
            else:
                self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.master.grab_release()
    
    def show_help_window(self):
        messagebox.showinfo(
            "如何使用",
            "本應用程式有兩種模式：\n\n"
            "【一般模式】\n"
            "• 可自由拖動、調整視窗大小。\n"
            "• 可透過分頁切換「時鐘」、「計時器」和「碼表」、「鬧鐘」。\n"
            "• 在視窗任何地方按右鍵，可切換至懸浮模式或調整設定。\n\n"
            "【懸浮模式】\n"
            "• 視窗小巧，無邊框，永遠保持在最上層。\n"
            "• 只能顯示目前選中分頁的功能（時鐘、計時器或碼表）。\n"
            "• **按住左鍵**可拖動。\n"
            "• **按右鍵**可彈出選單，調整時區、時間制或返回一般模式。"
        )

    def open_add_alarm_window(self):
        add_window = tk.Toplevel(self.master)
        add_window.title("新增鬧鐘")
        add_window.geometry("300x250")
        bg_color, fg_color = "SystemButtonFace", "black"
        add_window.configure(bg=bg_color)
        
        tk.Label(add_window, text="鬧鐘名稱:", font=("Helvetica", 12), bg=bg_color, fg=fg_color).pack(pady=5)
        alarm_name_entry = tk.Entry(add_window, width=20, font=("Helvetica", 12), bg=bg_color, fg=fg_color, insertbackground=fg_color)
        alarm_name_entry.pack(pady=5)

        time_frame = tk.Frame(add_window, bg=bg_color)
        time_frame.pack(pady=5)
        tk.Label(time_frame, text="時間:", font=("Helvetica", 12), bg=bg_color, fg=fg_color).pack(side="left")
        hours_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, wrap=True, width=3, font=("Helvetica", 12))
        hours_spinbox.set("0")
        hours_spinbox.pack(side="left", padx=5)
        tk.Label(time_frame, text=":", font=("Helvetica", 12), bg=bg_color, fg=fg_color).pack(side="left")
        mins_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, wrap=True, width=3, font=("Helvetica", 12))
        mins_spinbox.set("0")
        mins_spinbox.pack(side="left", padx=5)

        tk.Label(add_window, text="重複:", font=("Helvetica", 12), bg=bg_color, fg=fg_color).pack(pady=5)
        repeat_frame = tk.Frame(add_window, bg=bg_color)
        repeat_frame.pack()
        
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        self.repeat_vars = [tk.IntVar() for _ in range(7)]
        for i, day in enumerate(weekdays):
            cb = tk.Checkbutton(repeat_frame, text=day, variable=self.repeat_vars[i], bg=bg_color, fg=fg_color, selectcolor=bg_color, activebackground=bg_color, activeforeground=fg_color)
            cb.pack(side="left")
        
        def save_and_add_alarm():
            name = alarm_name_entry.get()
            hours = int(hours_spinbox.get())
            minutes = int(mins_spinbox.get())
            repeat_days = [i for i, var in enumerate(self.repeat_vars) if var.get() == 1]
            
            if not name:
                messagebox.showerror("錯誤", "鬧鐘名稱不能為空！", parent=add_window)
                return
            
            new_alarm = {
                'name': name,
                'time': (hours, minutes),
                'repeat': repeat_days,
                'enabled': True
            }
            self.alarms.append(new_alarm)
            self.save_alarms()
            self.update_alarm_list()
            add_window.destroy()
            
        tk.Button(add_window, text="確認", command=save_and_add_alarm, bg=bg_color, fg=fg_color).pack(pady=10)
        
    def load_alarms(self):
        if os.path.exists('alarms.json'):
            try:
                with open('alarms.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError):
                return []
        return []
        
    def save_alarms(self):
        with open('alarms.json', 'w', encoding='utf-8') as f:
            json.dump(self.alarms, f, indent=4)

    def delete_alarm(self):
        selected_item = self.alarm_list.selection()
        if selected_item:
            index = self.alarm_list.index(selected_item)
            del self.alarms[index]
            self.save_alarms()
            self.update_alarm_list()
            
    def update_alarm_list(self):
        for item in self.alarm_list.get_children():
            self.alarm_list.delete(item)
        
        weekdays_map = ["一", "二", "三", "四", "五", "六", "日"]
        for alarm in self.alarms:
            time_str = f"{alarm['time'][0]:02}:{alarm['time'][1]:02}"
            
            if not alarm['repeat']:
                repeat_str = "一次"
            else:
                repeat_str = "每週 " + "、".join([weekdays_map[day] for day in alarm['repeat']])

            self.alarm_list.insert('', 'end', values=(alarm['name'], time_str, repeat_str))
            
    def check_alarms(self):
        now = datetime.datetime.now()
        current_hours = now.hour
        current_minutes = now.minute
        current_weekday = now.weekday() # 星期一為0，星期日為6
        
        for alarm in list(self.alarms):
            alarm_repeat = alarm.get('repeat', [])
            
            is_once = not alarm_repeat
            is_repeating = current_weekday in alarm_repeat
            
            if alarm['time'][0] == current_hours and alarm['time'][1] == current_minutes and now.second == 0:
                if is_once or is_repeating:
                    self.trigger_alarm(alarm['name'])
                
                if is_once and self.alarms:
                    self.alarms.remove(alarm)
                    self.save_alarms()
                    self.update_alarm_list()
                    
        self.master.after(1000, self.check_alarms)
                
    def trigger_alarm(self, name):
        if not (self.alarm_sound_thread and self.alarm_sound_thread.is_alive()):
            self.alarm_sound_thread = threading.Thread(target=self.play_beep_sound, args=(500, 2000))
            self.alarm_sound_thread.start()
            self.send_notification("鬧鐘", f"「{name}」時間到了！")
            
    def trigger_timer(self):
        self.play_beep_sound_in_thread()
        self.send_notification("計時器", "計時器時間到！")

    def play_beep_sound(self, frequency, duration):
        winsound.Beep(frequency, duration)

    def send_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            app_name='多功能時鐘'
        )
        
    def get_common_timezones(self):
        return sorted(['UTC', 'Asia/Taipei', 'America/New_York', 'Asia/Tokyo', 'Europe/London', 'Australia/Sydney'])

    def toggle_mode(self):
        self.is_floating_mode = not self.is_floating_mode
        
        if self.is_floating_mode:
            self.master.overrideredirect(True)
            self.master.attributes("-topmost", True)
            self.master.geometry(self.floating_geometry)
            self.notebook.pack_forget()

            current_tab_id = self.notebook.index(self.notebook.select())
            
            self.floating_label = tk.Label(self.master, text="", font=("Helvetica", 36, "bold"), fg="black", bg="white")
            self.floating_label.pack(fill=tk.BOTH, expand=True)
            
            if self.theme_var.get() == "dark":
                self.floating_label.configure(bg="#2e2e2e", fg="#f0f0f0")
                self.master.configure(bg="#2e2e2e")
            else:
                self.floating_label.configure(bg="white", fg="black")
                self.master.configure(bg="white")

            self.master.bind("<Button-1>", self.start_move)
            self.master.bind("<B1-Motion>", self.do_move)
            self.master.config(menu="")
            
            self.menu.entryconfig(0, label="切換回一般模式")
            
            if current_tab_id == 0:  # 時鐘
                self.floating_label_updater = self.update_clock_floating
            elif current_tab_id == 1: # 計時器
                self.floating_label_updater = self.update_timer_floating
            elif current_tab_id == 2: # 碼表
                self.floating_label_updater = self.update_stopwatch_floating
            else:
                self.floating_label.config(text="不支援此模式")
                self.floating_label_updater = lambda: None
            
        else:
            self.master.overrideredirect(False)
            self.master.attributes("-topmost", False)
            self.master.geometry(self.original_geometry)
            self.notebook.pack(fill=tk.BOTH, expand=True)
            self.floating_label.destroy()
            self.master.unbind("<Button-1>")
            self.master.unbind("<B1-Motion>")
            self.master.config(menu=self.menubar)
            self.menu.entryconfig(0, label="切換到懸浮模式")
            self.floating_label_updater = lambda: None
            self.apply_theme()


    def change_timezone(self):
        selected_tz = self.timezone_var.get()
        self.current_timezone = pytz.timezone(selected_tz)

    def toggle_format(self):
        format_val = self.format_var.get()
        self.is_24_hour_format = (format_val == "24h")

    def update_clock(self):
        current_time_utc = datetime.datetime.now(pytz.utc)
        localized_time = current_time_utc.astimezone(self.current_timezone)
        if self.is_24_hour_format:
            time_string = localized_time.strftime("%H:%M:%S")
        else:
            time_string = localized_time.strftime("%I:%M:%S %p")
        self.clock_label.config(text=time_string)
        
        if self.is_floating_mode and self.notebook.index(self.notebook.select()) == 0:
            self.floating_label.config(text=time_string)
            
        for tz_key, label in self.world_clock_labels.items():
            tz = pytz.timezone(tz_key)
            world_time = current_time_utc.astimezone(tz)
            label.config(text=f"{tz_key}: {world_time.strftime('%H:%M:%S')}")
            
        self.master.after(1000, self.update_clock)
        
    def update_clock_floating(self):
        current_time_utc = datetime.datetime.now(pytz.utc)
        localized_time = current_time_utc.astimezone(self.current_timezone)
        if self.is_24_hour_format:
            time_string = localized_time.strftime("%H:%M:%S")
        else:
            time_string = localized_time.strftime("%I:%M:%S %p")
        self.floating_label.config(text=time_string)
        self.master.after(1000, self.update_clock_floating)

    def update_timer(self):
        if self.timer_running:
            time_left = self.timer_end_time - datetime.datetime.now()
            if time_left.total_seconds() <= 0:
                self.timer_running = False
                self.timer_label.config(text="時間到!", fg="red")
                self.trigger_timer()
            else:
                secs = int(time_left.total_seconds())
                mins, secs = divmod(secs, 60)
                hours, mins = divmod(mins, 60)
                time_string = f"{hours:02}:{mins:02}:{secs:02}"
                self.timer_label.config(text=time_string)
                if self.is_floating_mode and self.notebook.index(self.notebook.select()) == 1:
                    self.floating_label.config(text=time_string)
        
        self.master.after(1000, self.update_timer)

    def update_timer_floating(self):
        if self.timer_running:
            time_left = self.timer_end_time - datetime.datetime.now()
            if time_left.total_seconds() <= 0:
                self.master.destroy()
                self.trigger_timer()
            else:
                secs = int(time_left.total_seconds())
                mins, secs = divmod(secs, 60)
                hours, mins = divmod(mins, 60)
                time_string = f"{hours:02}:{mins:02}:{secs:02}"
                self.floating_label.config(text=time_string)
                self.master.after(1000, self.update_timer_floating)
        else:
            self.floating_label.config(text="00:00:00")
            self.master.after(1000, self.update_timer_floating)
        
    def update_stopwatch(self):
        if self.stopwatch_running:
            elapsed = (datetime.datetime.now() - self.stopwatch_start_time).total_seconds() + self.stopwatch_paused_time
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_string = f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}"
            self.stopwatch_label.config(text=time_string)
            if self.is_floating_mode and self.notebook.index(self.notebook.select()) == 2:
                self.floating_label.config(text=time_string)
        
        self.master.after(10, self.update_stopwatch)
        
    def update_stopwatch_floating(self):
        if self.stopwatch_running:
            elapsed = (datetime.datetime.now() - self.stopwatch_start_time).total_seconds() + self.stopwatch_paused_time
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_string = f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}"
            self.floating_label.config(text=time_string)
        else:
            self.floating_label.config(text="00:00:00.00")
            
        self.master.after(10, self.update_stopwatch_floating)

    def play_beep_sound_in_thread(self):
        thread = threading.Thread(target=self.play_beep_sound, args=(1000, 1000))
        thread.start()

    def set_timer(self):
        pass

    def start_timer(self):
        self.pause_timer()
        try:
            hours = int(self.timer_hours_spinbox.get())
            minutes = int(self.timer_mins_spinbox.get())
            seconds = int(self.timer_secs_spinbox.get())
            
            self.timer_total_seconds = hours * 3600 + minutes * 60 + seconds
            if self.timer_total_seconds > 0:
                self.timer_running = True
                self.timer_end_time = datetime.datetime.now() + datetime.timedelta(seconds=self.timer_total_seconds)
                self.timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}", fg="black")
            else:
                self.timer_label.config(text="時間必須大於0", fg="red")
        except ValueError:
            self.timer_label.config(text="格式錯誤", fg="red")

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            time_left = self.timer_end_time - datetime.datetime.now()
            self.timer_total_seconds = time_left.total_seconds()
        
    def reset_timer(self):
        self.pause_timer()
        self.timer_total_seconds = 0
        self.timer_label.config(text="00:00:00", fg="black")

    def start_stopwatch(self):
        if not self.stopwatch_running:
            self.stopwatch_running = True
            self.stopwatch_start_time = datetime.datetime.now()
            
    def pause_stopwatch(self):
        if self.stopwatch_running:
            self.stopwatch_running = False
            elapsed = (datetime.datetime.now() - self.stopwatch_start_time).total_seconds()
            self.stopwatch_paused_time += elapsed

    def reset_stopwatch(self):
        self.pause_stopwatch()
        self.stopwatch_paused_time = 0.0
        self.stopwatch_label.config(text="00:00:00.00")

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = self.master.winfo_x() + event.x - self._x
        y = self.master.winfo_y() + event.y - self._y
        self.master.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AllInOneClock(root)
    root.mainloop()