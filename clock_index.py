import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import datetime
import pytz
import tzlocal

class AllInOneClock:
    def __init__(self, master):
        self.master = master
        self.master.title("多功能時鐘")
        
        self.is_floating_mode = False
        self.original_geometry = "500x350"
        self.floating_geometry = "250x100"
        
        self.master.geometry(self.original_geometry)

        # 創建選單列
        self.create_menubar()
        
        # 創建一個 Notebook 來容納不同的功能
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 創建時鐘頁面
        self.clock_frame = tk.Frame(self.notebook, bg="SystemButtonFace")
        self.notebook.add(self.clock_frame, text="時鐘")
        self.setup_clock_tab()

        # 創建計時器頁面
        self.timer_frame = tk.Frame(self.notebook, bg="SystemButtonFace")
        self.notebook.add(self.timer_frame, text="計時器")
        self.setup_timer_tab()

        # 創建碼表頁面
        self.stopwatch_frame = tk.Frame(self.notebook, bg="SystemButtonFace")
        self.notebook.add(self.stopwatch_frame, text="碼表")
        self.setup_stopwatch_tab()
        
        # 設置右鍵選單
        self.create_context_menu()
        
        # 綁定右鍵事件
        self.master.bind("<Button-3>", self.show_context_menu)
        
        # 啟動時鐘更新
        self.update_clock()
        
    def create_menubar(self):
        """創建選單列，並將其附加到主視窗"""
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)
        
        # 建立「說明」選單
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="說明", menu=help_menu, font=("Helvetica", 11))
        
        # 在「說明」選單中添加「如何使用」選項
        help_menu.add_command(label="如何使用", command=self.show_help_window, font=("Helvetica", 11))

    def create_context_menu(self):
        """創建右鍵選單"""
        self.menu = tk.Menu(self.master, tearoff=0)
        
        # 模式切換
        self.menu.add_command(label="切換到懸浮模式", command=self.toggle_mode, font=("Helvetica", 11, "bold"))
        self.menu.add_separator()
        
        # 時區子選單
        timezone_menu = tk.Menu(self.menu, tearoff=0)
        self.timezone_var = tk.StringVar()
        self.timezone_options = self.get_common_timezones()
        self.current_timezone = tzlocal.get_localzone()
        
        for tz in self.timezone_options:
            timezone_menu.add_radiobutton(label=tz, variable=self.timezone_var, value=tz, command=self.change_timezone, font=("Helvetica", 10))
        
        self.timezone_var.set(self.current_timezone.key)
        self.menu.add_cascade(label="選擇時區", menu=timezone_menu, font=("Helvetica", 11))
        
        # 時間制子選單
        format_menu = tk.Menu(self.menu, tearoff=0)
        self.format_var = tk.StringVar(value="24h")
        format_menu.add_radiobutton(label="24小時制", variable=self.format_var, value="24h", command=self.toggle_format, font=("Helvetica", 10))
        format_menu.add_radiobutton(label="12小時制", variable=self.format_var, value="12h", command=self.toggle_format, font=("Helvetica", 10))
        
        self.menu.add_cascade(label="選擇時間制", menu=format_menu, font=("Helvetica", 11))

    def show_context_menu(self, event):
        """顯示右鍵選單"""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
            
    def show_help_window(self):
        """顯示使用說明視窗"""
        messagebox.showinfo(
            "如何使用",
            "本應用程式有兩種模式：\n\n"
            "【一般模式】\n"
            "• 可自由拖動、調整視窗大小。\n"
            "• 可透過分頁切換「時鐘」、「計時器」和「碼表」。\n"
            "• 在視窗任何地方按右鍵，可切換至懸浮模式或調整設定。\n\n"
            "【懸浮模式】\n"
            "• 視窗小巧，無邊框，永遠保持在最上層。\n"
            "• 只能顯示「時鐘」功能。\n"
            "• **按住左鍵**可拖動。\n"
            "• **按右鍵**可彈出選單，調整時區、時間制或返回一般模式。"
        )

    def setup_clock_tab(self):
        self.is_24_hour_format = True
        self.clock_label = tk.Label(self.clock_frame, text="", font=("Helvetica", 60, "bold"), bg="SystemButtonFace")
        self.clock_label.pack(pady=20)
        
    def setup_timer_tab(self):
        self.timer_running = False
        self.timer_time_left = 0
        self.timer_label = tk.Label(self.timer_frame, text="00:00:00", font=("Helvetica", 60, "bold"), bg="SystemButtonFace")
        self.timer_label.pack(pady=20)

        control_frame = tk.Frame(self.timer_frame, bg="SystemButtonFace")
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="設定時間", command=self.set_timer).pack(side="left", padx=5)
        tk.Button(control_frame, text="開始", command=self.start_timer).pack(side="left", padx=5)
        tk.Button(control_frame, text="暫停", command=self.pause_timer).pack(side="left", padx=5)
        tk.Button(control_frame, text="重置", command=self.reset_timer).pack(side="left", padx=5)
        
    def setup_stopwatch_tab(self):
        self.stopwatch_running = False
        self.stopwatch_elapsed_time = 0.0
        self.stopwatch_label = tk.Label(self.stopwatch_frame, text="00:00:00.00", font=("Helvetica", 60, "bold"), bg="SystemButtonFace")
        self.stopwatch_label.pack(pady=20)
        
        control_frame = tk.Frame(self.stopwatch_frame, bg="SystemButtonFace")
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="開始", command=self.start_stopwatch).pack(side="left", padx=5)
        tk.Button(control_frame, text="暫停", command=self.pause_stopwatch).pack(side="left", padx=5)
        tk.Button(control_frame, text="重置", command=self.reset_stopwatch).pack(side="left", padx=5)

    def get_common_timezones(self):
        return sorted(['UTC', 'Asia/Taipei', 'America/New_York', 'Asia/Tokyo', 'Europe/London', 'Australia/Sydney'])

    def toggle_mode(self):
        self.is_floating_mode = not self.is_floating_mode
        
        if self.is_floating_mode:
            self.master.overrideredirect(True)
            self.master.attributes("-topmost", True)
            self.master.geometry(self.floating_geometry)
            self.master.configure(bg="white")
            self.notebook.pack_forget()
            
            self.floating_clock_label = tk.Label(self.master, text=self.clock_label['text'], font=("Helvetica", 36, "bold"), fg="black", bg="white")
            self.floating_clock_label.pack(fill=tk.BOTH, expand=True)
            
            self.master.bind("<Button-1>", self.start_move)
            self.master.bind("<B1-Motion>", self.do_move)
            
            # 隱藏選單列
            self.master.config(menu="")
            
            # 更新右鍵選單標籤
            self.menu.entryconfig(0, label="切換回一般模式")
        else:
            self.master.overrideredirect(False)
            self.master.attributes("-topmost", False)
            self.master.geometry(self.original_geometry)
            self.master.configure(bg="SystemButtonFace")
            self.notebook.pack(fill=tk.BOTH, expand=True)
            self.floating_clock_label.destroy()
            
            self.master.unbind("<Button-1>")
            self.master.unbind("<B1-Motion>")
            
            # 重新顯示選單列
            self.master.config(menu=self.menubar)
            
            # 更新右鍵選單標籤
            self.menu.entryconfig(0, label="切換到懸浮模式")

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
        
        if self.is_floating_mode:
            self.floating_clock_label.config(text=time_string)
            
        # 更新計時器
        if self.timer_running:
            self.timer_time_left -= 0.01
            if self.timer_time_left <= 0:
                self.timer_running = False
                self.timer_label.config(text="時間到!", fg="red")
            else:
                mins, secs = divmod(self.timer_time_left, 60)
                hours, mins = divmod(mins, 60)
                self.timer_label.config(text=f"{int(hours):02}:{int(mins):02}:{int(secs):02}")
        
        # 更新碼表
        if self.stopwatch_running:
            self.stopwatch_elapsed_time += 0.01
            mins, secs = divmod(self.stopwatch_elapsed_time, 60)
            hours, mins = divmod(mins, 60)
            self.stopwatch_label.config(text=f"{int(hours):02}:{int(mins):02}:{secs:05.2f}")
        
        self.master.after(10, self.update_clock)

    def set_timer(self):
        self.pause_timer()
        duration_str = simpledialog.askstring("設定計時器", "請輸入時間 (格式: M:S 或 H:M:S)", parent=self.master)
        if duration_str:
            try:
                parts = list(map(int, duration_str.split(':')))
                if len(parts) == 3:
                    hours, minutes, seconds = parts
                elif len(parts) == 2:
                    hours, minutes, seconds = 0, parts[0], parts[1]
                elif len(parts) == 1:
                    hours, minutes, seconds = 0, 0, parts[0]
                else:
                    raise ValueError
                
                self.timer_time_left = hours * 3600 + minutes * 60 + seconds
                self.timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}", fg="black")
            except (ValueError, IndexError):
                self.timer_label.config(text="格式錯誤", fg="red")

    def start_timer(self):
        if not self.timer_running and self.timer_time_left > 0:
            self.timer_running = True
    
    def pause_timer(self):
        self.timer_running = False
        
    def reset_timer(self):
        self.pause_timer()
        self.timer_time_left = 0
        self.timer_label.config(text="00:00:00", fg="black")

    def start_stopwatch(self):
        self.stopwatch_running = True

    def pause_stopwatch(self):
        self.stopwatch_running = False

    def reset_stopwatch(self):
        self.pause_stopwatch()
        self.stopwatch_elapsed_time = 0.0
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