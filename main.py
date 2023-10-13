"""
Shard - Windows terminal styled text editor
made by Abhineet Kelley, 2023
Released under MIT License
"""
import os
import sys
import time
from pathlib import Path
from random import choice

from tkinter import *
from tkinter import filedialog
from tkinter.font import Font
from tkinter.messagebox import showwarning, askyesnocancel, showerror


application_name = "Shard"


def resource_path(relative_path):
    """
    Absolute path to a resource, so that it can be
    correctly displayed/used in the compiled exe file
    made using pyinstaller
    Shard uses this function to display the title bar icon
    without the need of having the image file externally
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Shard:
    active_instances = 0

    main_directory = Path.home() / "AppData" / "Local" / "ShardEditor"
    shard_running_indicator = main_directory / "run"

    settings_file = main_directory / "EditorSettings.txt"
    save_location_file = main_directory / "LastSaveLocation.txt"
    instance_queue_file = main_directory / "files.temp"

    def __init__(self):
        self.master = Tk()
        self.master.withdraw()  # Hides the main Tk window, the parent of all subsequent instances

        Shard.main_directory.mkdir(parents=True, exist_ok=True)  # Create main directories if needed
        self.instance_queue_file = Shard.instance_queue_file
        self.instance_queue_file.touch()
        self.shard_running_indicator = Shard.shard_running_indicator

    def close_shard_if_no_instances_running(self):
        if Shard.active_instances <= 0:
            self.master.destroy()
            print("no instances detected")
            if self.shard_running_indicator.exists():
                self.shard_running_indicator.rmdir()
            sys.exit(0)

    def create_instance(self, filepath=None, main=False):
        if self.shard_running_indicator.exists() and not main:
            print("adding instance to file")
            self.add_instance_to_list(filepath)
        else:
            print("creating instance")
            ShardInstance(self.master, filepath) if filepath != "None" else ShardInstance(self.master)

    def add_instance_to_list(self, path):
        with open(self.instance_queue_file, 'a') as file:
            file.write(f"\n{path}")
            print("added", path)

    def open_instances_from_list(self):
        with open(self.instance_queue_file, 'r') as file:
            foreign_files = file.read().strip().split('\n')
        open(self.instance_queue_file, 'w').close()

        if foreign_files:
            [self.create_instance(ins, main=True) for ins in foreign_files if ins.strip() != '']

        self.close_shard_if_no_instances_running()
        self.master.after(69, self.open_instances_from_list)

    def is_foreign_file_empty(self):
        with open(self.instance_queue_file) as file:
            content = file.read().strip()

        return content == ''

    def start(self):
        if self.shard_running_indicator.exists():
            time.sleep(0.2)
            if not self.is_foreign_file_empty():
                pass
            else:
                print("app already running")
                self.master.destroy()
                return

        print("starting app")
        self.shard_running_indicator.mkdir(parents=True, exist_ok=True)
        self.open_instances_from_list()

        self.master.mainloop()


class ShardInstance:
    def __init__(self, master: Tk, filepath: Path | str | None = None):
        self.master = master
        self.root = Toplevel(master)
        self.bring_to_front(self.root)

        self.filename = StringVar()
        self.filename.set("Untitled")
        self.filepath = Path(args[0]).resolve()  # by default the location of current directory
        self.new_file = True  # whether you opened a new, empty file

        # Main folder and file paths
        self.app_directory = Shard.main_directory
        self.settings_file = Shard.settings_file
        self.save_location_file = Shard.save_location_file

        # Create main folders/files if they don't exist
        self.app_directory.mkdir(parents=True, exist_ok=True)
        self.settings_file.touch()
        self.save_location_file.touch()

        # Allowed Values of Value Editors
        self.colors = sorted(["black", "white", "red", "silver", "gray", "yellow", "sky blue", "green", "lime", "blue", "coral", "bisque", "purple", "pink"])
        self.fonts = sorted(["Consolas", "Courier New", "Lucida Console", "NSimSun", "Cascadia Mono", "MS Gothic"])
        self.sizes = sorted(list(range(8, 28, 2)) + [32, 48, 11, 72, 64, 96])
        self.tabsize_allowed = list(range(4, 17, 2))
        self.opacity = list(range(30, 101))
        self.font_styles = ["bold", "normal"]
        self.window_states = ["normal", "zoomed"]
        self.text_wrapping = ["word", "none"]

        # Default Main Variables
        self.editor_bg = StringVar()
        self.editor_fg = StringVar()
        self.editor_font = StringVar()
        self.editor_font_size = IntVar()
        self.tabsize = IntVar()
        self.editor_opacity = IntVar()
        self.bold_font = StringVar()
        self.window_state = StringVar()
        self.text_wrap = StringVar()

        self.editor_properties = [
            self.editor_bg, self.editor_fg, self.editor_font, self.editor_font_size,
            self.tabsize, self.editor_opacity, self.bold_font, self.text_wrap]

        self.get_editor_settings()
        self.draw_app_layout()
        self.apply_editor_settings()

        if filepath is not None:  # if you opened an existing file in the editor via "Open With" or OS Terminal
            self.filepath = Path(filepath).resolve()
            self.new_file = False

            try:
                with open(self.filepath, encoding="UTF-8") as file:
                    content = file.read()
            except PermissionError:
                self.close_instance()
                showerror("Error", "No permissions to view file")
                return
            except FileNotFoundError:
                content = ''
                self.new_file = True
            except UnicodeDecodeError:
                try:
                    with open(self.filepath, encoding="ANSI") as file:
                        content = file.read()
                except Exception:
                    self.close_instance()
                    showerror("Error", "An unexpected error has occurred")
                    return

            self.filename.set(self.filepath.stem + self.filepath.suffix)
            self.editor.insert(INSERT, content)

        self.update_window_title(self.filename.get())
        self.root.wm_protocol("WM_DELETE_WINDOW", lambda: [self.save_before_closing_instance()])

        Shard.active_instances += 1
        print("1 instance created, total:", Shard.active_instances)
        self.root.after(100, lambda: self.is_file_saved())

    # Start-Up Methods
    def get_last_save_location(self):
        self.app_directory.mkdir(parents=True, exist_ok=True)

        self.save_location_file.touch()
        with open(self.save_location_file) as file:
            content = file.read().strip()
        if Path(content).exists() and Path(content).is_dir():
            return Path(content)
        else:
            return False

    def set_last_save_location(self, path):
        self.app_directory.mkdir(parents=True, exist_ok=True)

        with open(self.save_location_file, 'w') as file:
            file.write(str(path))

    def get_editor_settings(self):
        self.app_directory.mkdir(parents=True, exist_ok=True)

        open(self.settings_file, 'a').close()
        with open(self.settings_file, "r") as file:
            current = file.read().split('\t')

        if len(current) >= 9 and all(current):
            self.validate_written_settings(current)
        else:
            self.validate_written_settings(current + [""]*9)

    def validate_written_settings(self, vals):
        bg, fg, ft, tb, fs, op, bd, ws, tw, *extra = vals

        self.editor_bg.set(         bg if bg in self.colors else "black")
        self.editor_fg.set(         fg if fg in self.colors else "white")
        self.editor_font.set(       ft if ft in self.fonts else "Consolas")
        self.tabsize.set(           int(tb) if tb.isdecimal() and int(tb) in self.tabsize_allowed else 4)
        self.editor_font_size.set(  int(fs) if fs.isdecimal() and int(fs) in self.sizes else 20)
        self.editor_opacity.set(    int(op) if op.isdecimal() and int(op) in self.opacity else 100)
        self.bold_font.set(         bd if bd in self.font_styles else "normal")
        self.window_state.set(      ws if ws in self.window_states else "normal")
        self.text_wrap.set(         tw if tw in self.text_wrapping else "word")

        self.save_editor_settings()

    def update_window_title(self, string):
        self.root.title(string + f" - {application_name}")

    @staticmethod
    def bring_to_front(window: Tk | Toplevel):
        window.attributes('-topmost', True)
        window.focus_set()
        window.after(100, lambda: [window.attributes('-topmost', False)])

    def toggle_pin_window_to_top(self):
        if self.pin_state.get() == "true":
            self.root.attributes('-topmost', True)
        else:
            self.root.attributes('-topmost', False)

    # GUI Related
    def save_editor_settings(self):
        with open(self.settings_file, "w") as file:
            file.write('\t'.join((
                self.editor_bg.get(), self.editor_fg.get(), self.editor_font.get(),
                str(self.tabsize.get()),
                str(self.editor_font_size.get()),
                str(self.editor_opacity.get()),
                self.bold_font.get(), self.window_state.get(), self.text_wrap.get()
            )))

    def detect_window_maximised(self):
        self.check_scrolls()
        last_state = self.window_state.get()
        current_state = self.root.state()

        if last_state == current_state:
            return
        else:
            print(f"window state changed: {last_state} -> {current_state}")
            self.window_state.set(current_state)
            self.save_editor_settings()

    def check_scrolls(self):
        if self.y_scroll_editor.get() == (0.0, 1.0):
            self.y_scroll_editor.grid_remove()
        else:
            self.y_scroll_editor.grid()

        if self.x_scroll_editor.get() == (0.0, 1.0):
            self.x_scroll_editor.grid_remove()
        else:
            self.x_scroll_editor.grid()

    def apply_editor_settings(self):
        self.root.config(bg=self.editor_bg.get())
        self.root.attributes('-alpha', self.editor_opacity.get() / 100)

        self.mainframe.config(bg=self.editor_bg.get())
        self.editor.config(
            bg=self.editor_bg.get(),
            fg=self.editor_fg.get(),
            font=(self.editor_font.get(), self.editor_font_size.get(), self.bold_font.get()),
            insertbackground="white",
            borderwidth=0, insertwidth=2,
            wrap=self.text_wrap.get()
        )

        self.custom_font = Font(font=self.editor['font'])
        self.editor.config(tabs=self.custom_font.measure(' ' * self.tabsize.get()))

        self.root.update_idletasks()

    def draw_app_layout(self):
        self.root.state(self.window_state.get())
        self.root.minsize(430, 100)
        self.root.geometry("500x300")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        try:
            self.root.iconphoto(True, PhotoImage(file=resource_path("SElogo.png")))
        except TclError:
            pass
        except Exception as e:
            pass

        self.root.bind("<Configure>", lambda _: self.detect_window_maximised())
        self.root.bind("<Motion>", lambda _: self.check_scrolls())
        self.root.bind("<Enter>", lambda _: self.check_scrolls())
        self.root.bind("<Leave>", lambda _: self.check_scrolls())

        # Top Frame
        self.topframe = Frame(self.root, bg="black", highlightthickness=1)
        self.topframe.grid(row=0, column=0, sticky=EW)
        self.topframe.rowconfigure(0, weight=1)
        self.topframe.columnconfigure(10, weight=1)

        self.draw_top_frame()

        # Editor
        self.mainframe = Frame(self.root)
        self.mainframe.grid(row=1, column=0, sticky=NSEW, padx=4, pady=4)
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        self.editor = Text(self.mainframe, width=500, wrap=NONE, undo=True)
        self.editor.grid(row=0, column=0, sticky=NSEW)
        self.editor.bind("<KeyRelease>", lambda _: self.is_file_saved())
        self.editor.focus_set()

        self.y_scroll_editor = Scrollbar(self.mainframe, command=self.editor.yview)
        self.y_scroll_editor.grid(row=0, column=1, sticky=NS)
        self.editor['yscrollcommand'] = self.y_scroll_editor.set

        self.x_scroll_editor = Scrollbar(self.mainframe, command=self.editor.xview, orient="horizontal")
        self.x_scroll_editor.grid(row=1, column=0, sticky=EW)
        self.editor['xscrollcommand'] = self.x_scroll_editor.set

        # Bottom Frame
        self.bottomframe = Frame(self.root, bg="black", highlightthickness=1)

        self.curr_line = StringVar()
        self.curr_colm = StringVar()
        self.update_cursor_location_indicators()

        Label(self.bottomframe,
              bg="black", fg="white",
              font=('Consolas', 13), text="  Ln:"
              ).pack(fill=Y, side=LEFT)
        self.curr_line_label = Label(self.bottomframe,
                                     bg="black", fg="white",
                                     font=('Consolas', 13), textvariable=self.curr_line)
        self.curr_line_label.pack(fill=Y, side=LEFT)

        Label(self.bottomframe,
              bg="black", fg="white",
              font=('Consolas', 13), text="  Col:"
              ).pack(fill=Y, side=LEFT)
        self.curr_colm_label = Label(self.bottomframe,
                                     bg="black", fg="white",
                                     font=('Consolas', 13), textvariable=self.curr_colm)
        self.curr_colm_label.pack(fill=Y, side=LEFT)

        self.pin_state = StringVar()
        self.pin_state.set("false")

        Label(
            self.bottomframe, bg="black", fg="yellow",
            font=('Consolas', 13), text="   always on top").pack(fill=Y, side=LEFT)

        self.pin_toggle = Checkbutton(
            self.bottomframe, bg="black", fg="lime", selectcolor="black",
            highlightthickness=4, highlightbackground="red",
            variable=self.pin_state, onvalue="true", offvalue="false",
            command=self.toggle_pin_window_to_top)
        self.pin_toggle.pack(fill=Y, side=LEFT)

        self.root.bind("<Control-q>", lambda _: self.pin_toggle.invoke())
        self.root.bind("<Control-Q>", lambda _: self.pin_toggle.invoke())

        self.bottomframe.grid(row=2, column=0, columnspan=2, sticky=EW)
        self.editor.bind("<ButtonRelease-1>", lambda _: self.update_cursor_location_indicators())

        self.add_hints()

    def update_cursor_location_indicators(self):
        ln, col = self.editor.index(INSERT).split(".")
        self.curr_line.set(ln)
        self.curr_colm.set(col)

    def draw_top_frame(self):
        def config_button(butt: Button):
            butt.config(bg="black", fg="white",
                        font=("Consolas", 13, 'bold'),
                        relief=FLAT, activeforeground="grey",
                        activebackground="black", borderwidth=0)

        self.open_button = Button(
            self.topframe, text="Open",
            command=self.open_file_window
        )
        config_button(self.open_button)
        self.open_button.grid(row=0, column=0, padx=10)

        self.save_button = Button(
            self.topframe, text="Save",
            command=self.save_window
        )
        config_button(self.save_button)
        self.save_button.grid(row=0, column=1, padx=10)

        self.saveas_button = Button(
            self.topframe, text="Save As",
            command=lambda saveas=True: self.save_window(saveas)
        )
        config_button(self.saveas_button)
        self.saveas_button.grid(row=0, column=2, padx=10)

        self.new_button = Button(
            self.topframe, text="New",
            command=self.start_new_file
        )
        config_button(self.new_button)
        self.new_button.grid(row=0, column=3, padx=10)

        self.settings_button = Button(
            self.topframe, text="Settings",
            command=self.settings_window
        )
        config_button(self.settings_button)
        self.settings_button.config(fg="cyan")
        self.settings_button.grid(row=0, column=4, padx=10)

        # Keyboard bindings
        self.root.bind('<Control-s>', lambda _: [self.save_window()])
        self.root.bind('<Control-S>', lambda _: [self.save_window()])
        self.root.bind('<Control-o>', lambda _: [self.open_file_window()])
        self.root.bind('<Control-O>', lambda _: [self.open_file_window()])
        self.root.bind('<Control-Shift-s>', lambda _, saveas=True: [self.save_window(saveas)])
        self.root.bind('<Control-Shift-S>', lambda _, saveas=True: [self.save_window(saveas)])
        self.root.bind('<Control-n>', lambda _: [self.start_new_file()])
        self.root.bind('<Control-N>', lambda _: [self.start_new_file()])
        self.root.bind('<Control-w>', lambda _: [self.settings_window()])
        self.root.bind('<Control-W>', lambda _: [self.settings_window()])

    def add_hints(self):
        # HINTS
        self.help_hover = Label(
            self.topframe, text="?", bg="white", fg="black",
            highlightthickness=1, highlightbackground="white",
            font=("haha", 16, 'bold')
        )
        self.help_hover.grid(row=0, column=10, ipadx=4, sticky=E)
        self.help_hover.bind("<Enter>", lambda _: show_hints())
        self.help_hover.bind("<Leave>", lambda _: hide_hints())

        def show_hints():
            self.settings_hint.grid()
            self.save_hint.grid()
            self.save_as_hint.grid()
            self.new_hint.grid()
            self.open_hint.grid()
            self.pin_hint.pack(side=LEFT, fill=Y)

        def hide_hints():
            self.settings_hint.grid_remove()
            self.save_hint.grid_remove()
            self.save_as_hint.grid_remove()
            self.new_hint.grid_remove()
            self.open_hint.grid_remove()
            self.pin_hint.pack_forget()

        def config_hint(labb: Label):
            labb.config(bg="white", fg="black", highlightbackground="black", highlightthickness=1,
                        font=("default", 11, 'bold'))

        self.open_hint = Label(
            self.topframe, text="ctrl+O"
        )
        config_hint(self.open_hint)
        self.open_hint.grid(row=0, column=0, sticky=EW, padx=4)

        self.save_hint = Label(
            self.topframe, text="ctrl+S"
        )
        config_hint(self.save_hint)
        self.save_hint.grid(row=0, column=1, sticky=EW, padx=4)

        self.save_as_hint = Label(
            self.topframe, text="ctrl+shift+S"
        )
        config_hint(self.save_as_hint)
        self.save_as_hint.grid(row=0, column=2, sticky=EW, padx=4)

        self.new_hint = Label(
            self.topframe, text="ctrl+N"
        )
        config_hint(self.new_hint)
        self.new_hint.grid(row=0, column=3, sticky=EW, padx=4)

        self.settings_hint = Label(
            self.topframe, text="ctrl+W"
        )
        config_hint(self.settings_hint)
        self.settings_hint.config(bg="cyan")
        self.settings_hint.grid(row=0, column=4, sticky=EW, padx=4)

        self.pin_hint = Label(
            self.bottomframe, text=" ctrl+Q "
        )
        config_hint(self.pin_hint)
        self.pin_hint.config(bg="lime")
        self.pin_hint.pack(side=LEFT, fill=Y)

        hide_hints()

    # Secondary Windows
    def settings_window(self):
        settings = Toplevel(self.root)
        settings.focus_force()
        settings.grab_set()

        settings.title("Shard Settings")
        settings.columnconfigure(1, weight=3)
        settings.columnconfigure(0, weight=1)
        settings.rowconfigure(0, weight=1)

        settings.resizable(False, False)
        settings.minsize(350, 300)

        curr_vars = [i.get() for i in self.editor_properties]

        sample = Label(settings, text="Shard Editor Settings",
                       bg=self.editor_bg.get(),
                       fg=self.editor_fg.get(),
                       font=(self.editor_font.get(), self.editor_font_size.get(), self.bold_font.get()),
                       anchor=W, width=2
                       )
        sample.grid(row=0, column=0, columnspan=2, sticky=NSEW, ipady=12, pady=8)

        def update_sample():
            sample.config(bg=self.editor_bg.get(), fg=self.editor_fg.get(),
                          font=(
                              self.editor_font.get(),
                              self.editor_font_size.get(),
                              self.bold_font.get()
                          ))

        # self.editor_bg = StringVar()
        Label(settings, text="Background: ").grid(row=1, column=0, sticky=E, pady=4)

        f = Frame(settings)
        f.grid(row=1, column=1)

        i = Button(f, textvariable=self.editor_bg, relief=SUNKEN, width=14)
        i.pack(side=LEFT)
        i.bind("<Right>", lambda _: [self.editor_bg.set(
            self.colors[
                (self.colors.index(self.editor_bg.get())+1) % len(self.colors)
            ]), update_sample()])
        i.bind("<Left>", lambda _: [self.editor_bg.set(
            self.colors[
                (self.colors.index(self.editor_bg.get()) - 1) % len(self.colors)
                ]), update_sample()])
        i.bind("<Button-1>", lambda _: i.focus_set())
        i.focus_set()

        o = OptionMenu(f, self.editor_bg, *self.colors, command=lambda _: [update_sample()])
        o.pack(side=LEFT)
        o.config(width=1, font=('Calibri', 1), bg="#AAAAAA", fg="white", activeforeground="white", text="")

        # self.editor_fg = StringVar()
        Label(settings, text="Foreground: ").grid(row=2, column=0, sticky=E, pady=4)

        f = Frame(settings)
        f.grid(row=2, column=1)

        i2 = Button(f, textvariable=self.editor_fg, relief=SUNKEN, width=14)
        i2.pack(side=LEFT)
        i2.bind("<Right>", lambda _: [self.editor_fg.set(
            self.colors[
                (self.colors.index(self.editor_fg.get()) + 1) % len(self.colors)
                ]), update_sample()])
        i2.bind("<Left>", lambda _: [self.editor_fg.set(
            self.colors[
                (self.colors.index(self.editor_fg.get()) - 1) % len(self.colors)
                ]), update_sample()])
        i2.bind("<Button-1>", lambda _: i2.focus_set())

        o = OptionMenu(f, self.editor_fg, *self.colors, command=lambda _: [update_sample()])
        o.pack(side=LEFT)
        o.config(width=1, font=('Calibri', 1), bg="#AAAAAA", fg="white", activeforeground="white", text="")

        # self.editor_font = StringVar()
        Label(settings, text="Font: ").grid(row=3, column=0, sticky=E, pady=4)

        f = Frame(settings)
        f.grid(row=3, column=1)

        i3 = Button(f, textvariable=self.editor_font, relief=SUNKEN, width=14)
        i3.pack(side=LEFT)
        i3.bind("<Right>", lambda _: [self.editor_font.set(
            self.fonts[
                (self.fonts.index(self.editor_font.get()) + 1) % len(self.fonts)
                ]), update_sample()])
        i3.bind("<Left>", lambda _: [self.editor_font.set(
            self.fonts[
                (self.fonts.index(self.editor_font.get()) - 1) % len(self.fonts)
                ]), update_sample()])
        i3.bind("<Button-1>", lambda _: i3.focus_set())

        o = OptionMenu(f, self.editor_font, *self.fonts, command=lambda _: [update_sample()])
        o.pack(side=LEFT)
        o.config(width=1, font=('Calibri', 1), bg="#AAAAAA", fg="white", activeforeground="white", text="")

        checkframe = Frame(settings)
        checkframe.grid(row=4, column=1)
        x = Checkbutton(checkframe, text="Bold Fonts", variable=self.bold_font, offvalue="normal", onvalue="bold",
                        command=lambda: [update_sample()])
        x.pack(side=LEFT)
        x2 = Checkbutton(checkframe, text="Wrap Text", variable=self.text_wrap, offvalue="none", onvalue="word")
        x2.pack(side=LEFT)

        x.bind("<Right>", lambda _: [x.invoke(), update_sample()])
        x.bind("<Left>", lambda _: [x.invoke(), update_sample()])
        x2.bind("<Right>", lambda _: [x2.invoke()])
        x2.bind("<Left>", lambda _: [x2.invoke()])

        # self.editor_font_size = IntVar()
        Label(settings, text="Font Size: ").grid(row=5, column=0, sticky=E, pady=4)

        f = Frame(settings)
        f.grid(row=5, column=1)

        i4 = Button(f, textvariable=self.editor_font_size, relief=SUNKEN, width=14)
        i4.pack(side=LEFT)
        i4.bind("<Right>", lambda _: [self.editor_font_size.set(
            self.sizes[
                (self.sizes.index(self.editor_font_size.get()) + 1) % len(self.sizes)
                ]), update_sample()])
        i4.bind("<Left>", lambda _: [self.editor_font_size.set(
            self.sizes[
                (self.sizes.index(self.editor_font_size.get()) - 1) % len(self.sizes)
                ]), update_sample()])
        i4.bind("<Button-1>", lambda _: i4.focus_set())

        o = OptionMenu(f, self.editor_font_size, *self.sizes, command=lambda _: [update_sample()])
        o.pack(side=LEFT)
        o.config(width=1, font=('Calibri', 1), bg="#AAAAAA", fg="white", activeforeground="white", text="")

        # self.tabsize = IntVar()
        Label(settings, text="Tab Size: ").grid(row=6, column=0, sticky=E, pady=4)

        f = Frame(settings)
        f.grid(row=6, column=1)

        i5 = Button(f, textvariable=self.tabsize, relief=SUNKEN, width=14)
        i5.pack(side=LEFT)
        i5.bind("<Right>", lambda _: [self.tabsize.set(
            self.tabsize_allowed[
                (self.tabsize_allowed.index(self.tabsize.get()) + 1) % len(self.tabsize_allowed)
                ]), update_sample()])
        i5.bind("<Left>", lambda _: [self.tabsize.set(
            self.tabsize_allowed[
                (self.tabsize_allowed.index(self.tabsize.get()) - 1) % len(self.tabsize_allowed)
                ]), update_sample()])
        i5.bind("<Button-1>", lambda _: i5.focus_set())

        o = OptionMenu(f, self.tabsize, *self.tabsize_allowed, command=lambda _: [update_sample()])
        o.pack(side=LEFT)
        o.config(width=1, font=('Calibri', 1), bg="#AAAAAA", fg="white", activeforeground="white", text="")

        # self.editor_opacity = IntVar()
        Label(settings, text="Opacity: ").grid(row=7, column=0, sticky=E)

        i6 = Scale(settings, orient="horizontal", variable=self.editor_opacity, takefocus=True,
              from_=30, to=100, repeatinterval=1, sliderlength=12,
              command=lambda _: [self.root.attributes('-alpha', self.editor_opacity.get() / 100)])
        i6.grid(row=7, column=1, sticky=EW)
        i6.bind("<Button-1>", lambda _: i6.focus_set())

        # hints
        help_frame = Frame(settings)
        help_frame.columnconfigure(1, weight=1)
        help_frame.columnconfigure(1, weight=1)
        help_frame.grid(row=8, column=0, columnspan=2, sticky=NSEW, padx=8, pady=12)

        Label(help_frame, text="ENTER\nESCAPE", justify=RIGHT, borderwidth=3, relief=GROOVE).grid(row=0, column=0, sticky=W, ipadx=4)
        Label(help_frame, text="Save\nCancel", justify=LEFT).grid(row=0, column=1, sticky=W, padx=4)
        Label(help_frame, text="RIGHT/LEFT\nTAB / Shift+TAB", justify=RIGHT, borderwidth=3, relief=GROOVE).grid(row=0, column=2, sticky=W, ipadx=4)
        Label(help_frame, text="Change value\nBrowse settings", justify=LEFT).grid(row=0, column=3, sticky=W, padx=4)

        # button frame
        button_frame = Frame(settings)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.grid(row=9, column=0, columnspan=2, sticky=NSEW)

        def save_and_apply_settings():
            self.save_editor_settings()
            self.apply_editor_settings()
            settings.destroy()

        def cancel_and_revert_settings():
            [v.set(curr_vars[i]) for i, v in enumerate(self.editor_properties)]
            self.apply_editor_settings()
            settings.destroy()

        ok_button = Button(
            button_frame, text=choice(("OK", "Save", "Apply")), width=12, relief=RIDGE, borderwidth=3,
            activebackground="#303030", activeforeground="white",
            bg="black", fg="white", font=("consolas", 12, 'bold'),
            command=save_and_apply_settings)
        ok_button.grid(row=0, column=0, sticky=E, pady=8)
        ok_button.bind("<Return>", lambda _: save_and_apply_settings())

        cancel_button = Button(
            button_frame, text=choice(("Nevermind", "Cancel")), width=12, relief=RIDGE,
            borderwidth=3, font=("consolas", 12, 'bold'),
            command=cancel_and_revert_settings)
        cancel_button.grid(row=0, column=1, sticky=W, pady=8, padx=4)
        cancel_button.bind("<Return>", lambda _: cancel_and_revert_settings())

        # Bindings
        settings.wm_protocol('WM_DELETE_WINDOW', lambda: [cancel_and_revert_settings(), settings.destroy()])
        settings.bind("<Escape>", lambda _: [cancel_and_revert_settings(), settings.destroy()])
        settings.bind("<Return>", lambda _: save_and_apply_settings())

    def save_window(self, saveAs=False, close_after_saving=False):
        if not saveAs:
            if self.is_file_saved():  # don't do anything
                return
            elif not self.new_file:  # save file directly without save dialog box
                self.save_file(close_after_saving=close_after_saving)
                return

        init_dir = self.get_last_save_location()
        if not init_dir:
            init_dir = self.filepath.parent

        file_name = filedialog.asksaveasfilename(
            parent=self.root,
            confirmoverwrite=True,
            defaultextension=".txt",
            filetypes=[("Text files", ".txt"), ("All files", "*.*")],
            initialdir=init_dir,
            initialfile=self.filename.get()
        )
        print("user chose to save as:", file_name)

        if file_name:
            self.filepath = Path(file_name)
            self.filename.set(self.filepath.stem + self.filepath.suffix)
            self.set_last_save_location(self.filepath.parent)
            self.save_file(saveAs=saveAs, close_after_saving=close_after_saving)

    def open_file_window(self):
        opened_file = filedialog.askopenfilename(
            parent=self.root,
            filetypes=[("Text files", ".txt"), ("All files", "*.*")],
            initialdir=self.filepath.parent
        )

        if opened_file:
            opened_file = Path(opened_file)
            try:
                with open(opened_file, encoding="UTF-8") as file:
                    content = file.read()
            except PermissionError:
                showerror("Error", "No permissions to view file")
                return
            except FileNotFoundError:
                return
            except UnicodeDecodeError:
                try:
                    with open(opened_file, encoding="ANSI") as file:
                        content = file.read()
                except Exception:
                    showerror("Error", "An unexpected error has occurred")
                    return

            if self.new_file and self.editor.get("1.0", END).strip() == "" and self.filename.get() == "Untitled":
                self.filepath = opened_file
                self.filename.set(self.filepath.stem + self.filepath.suffix)
                self.update_window_title(self.filename.get())
                self.editor.delete("1.0", END)
                self.editor.insert(INSERT, content)
                self.new_file = False
            else:
                self.start_new_file(Path(opened_file))

    # Save Operation Related
    def is_file_saved(self):
        self.check_scrolls()
        self.update_cursor_location_indicators()

        if self.new_file:
            if self.editor.get("1.0", END).rstrip('\n') != '':
                self.update_window_title("*" + self.filename.get())
            else:
                self.update_window_title(self.filename.get())
            return False

        try:
            with open(self.filepath.parent / self.filename.get(), encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.new_file = True
            return False
        except PermissionError:
            self.close_instance()
            showerror("Error", "No permissions to view file")
            return
        except UnicodeDecodeError:
            try:
                with open(self.filepath.parent / self.filename.get(), encoding="ANSI") as file:
                    content = file.read()
            except Exception as e:
                self.close_instance()
                showerror("Error", "An unexpected error has occurred")
                return

        cond = content.rstrip('\n') == self.editor.get("1.0", END).rstrip('\n')
        if not cond:
            self.update_window_title("*" + self.filename.get())
        else:
            self.update_window_title(self.filename.get())

        return cond

    def save_file(self, saveAs=False, close_after_saving=False):
        if not self.filename.get().strip():  # empty filename
            return
        if list(set(self.filename.get()).intersection(set('/\\:*?"<>|'))):
            showwarning("Invalid Filename", "Filename cannot contain symbols / \\ : * ? \" < > |")
            return

        target_file = self.filepath.parent / self.filename.get()

        content = self.editor.get("1.0", END)
        print(f"saving content at {target_file}")

        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(target_file, 'w', encoding="UTF-8") as file:
                file.write(content)
        except PermissionError:
            showerror("Error", "No permissions to write to file")
        except UnicodeEncodeError:
            try:
                with open(target_file, 'w', encoding="ANSI") as file:
                    file.write(content)
            except Exception as e:
                showerror("Error", "An unexpected error has occurred while saving the file")

        self.update_window_title(self.filename.get())
        self.new_file = False

        if close_after_saving:
            self.close_instance()

        return True

    # New Operation Related
    def start_new_file(self, filepath=None):
        ShardInstance(self.master, filepath)

    def close_instance(self):
        Shard.active_instances -= 1
        print("1 instance closed, total:", Shard.active_instances)
        self.root.destroy()

    def save_before_closing_instance(self):
        if not self.is_file_saved():
            if self.new_file and self.editor.get("1.0", END).rstrip('\n') == '':
                self.close_instance()
            else:
                self.root.attributes('-topmost', False)
                choice = askyesnocancel("File Unsaved", f"Do you want to save the file "
                                                        f"'{self.filename.get()}' before closing it?")
                if choice == YES:
                    self.save_window(close_after_saving=True)
                elif choice is None:
                    return
                else:
                    self.close_instance()
        else:
            self.close_instance()


if __name__ == '__main__':
    args = sys.argv
    shard = Shard()

    if len(args) > 1:
        for f in args[1:]:
            fpath = Path(f).resolve()
            shard.create_instance(fpath)
    else:
        shard.create_instance()

    shard.start()

