import ctypes
import json
import os
import random
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".wma", ".mid", ".midi", ".ogg")
APP_DIRECTORY = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIRECTORY, "music_player_data.json")

winmm = ctypes.WinDLL("winmm.dll")


def mci(command):
    buffer = ctypes.create_string_buffer(512)
    result = winmm.mciSendStringA(
        command.encode("utf-8"), buffer, len(buffer), 0
    )
    return result, buffer.value.decode("utf-8", errors="ignore").strip()


class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Pemutar Musik")
        self.root.geometry("980x620")
        self.root.minsize(820, 520)

        self.playlist = []
        self.lyrics = {}
        self.current_index = -1
        self.is_playing = False
        self.paused = False
        self.shuffle = False
        self.repeat_mode = "off"
        self.position_ms = 0
        self.duration_ms = 0
        self.volume = 70
        self.seek_dragging = False
        self.play_finished = False

        self.load_data()
        self.build_ui()
        self.refresh_playlist()
        self.update_controls()
        self.monitor()

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Info.TLabel", font=("Segoe UI", 11))

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Pemutar Musik", style="Title.TLabel").pack(anchor="w")

        columns = ttk.Frame(main)
        columns.pack(fill="both", expand=True, pady=(12, 8))
        columns.columnconfigure(0, weight=4, uniform="player")
        columns.columnconfigure(1, weight=3, uniform="player")
        columns.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(columns, text="Playlist", padding=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ttk.LabelFrame(columns, text="Lirik", padding=8)
        right.grid(row=0, column=1, sticky="nsew")

        self.playlist_box = tk.Listbox(left, font=("Segoe UI", 11), activestyle="dotbox")
        self.playlist_box.pack(fill="both", expand=True)
        self.playlist_box.bind("<<ListboxSelect>>", self.select_from_playlist)
        self.playlist_box.bind("<Double-Button-1>", lambda _event: self.play_selected())

        actions = ttk.Frame(left)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Tambah Lagu", command=self.add_files).pack(side="left", padx=(0, 4))
        ttk.Button(actions, text="Tambah Folder", command=self.add_folder).pack(side="left", padx=4)
        ttk.Button(actions, text="Hapus", command=self.remove_selected).pack(side="left", padx=4)

        self.lyrics_text = tk.Text(right, wrap="word", font=("Segoe UI", 11), undo=True)
        self.lyrics_text.pack(fill="both", expand=True)
        lyrics_actions = ttk.Frame(right)
        lyrics_actions.pack(fill="x", pady=(8, 0))
        ttk.Button(lyrics_actions, text="Simpan Lirik", command=self.save_lyrics).pack(side="left")
        ttk.Button(lyrics_actions, text="Hapus Lirik", command=self.delete_lyrics).pack(side="left", padx=8)

        controls = ttk.Frame(main)
        controls.pack(fill="x")

        self.now_playing = ttk.Label(controls, text="Belum ada lagu dipilih", style="Info.TLabel")
        self.now_playing.pack(anchor="w")

        timeline = ttk.Frame(controls)
        timeline.pack(fill="x", pady=(8, 0))
        self.current_time = ttk.Label(timeline, text="0:00", width=8)
        self.current_time.pack(side="left")
        self.progress = ttk.Scale(timeline, from_=0, to=1000, command=self.seek_preview)
        self.progress.pack(side="left", fill="x", expand=True, padx=6)
        self.progress.bind("<ButtonPress-1>", lambda _event: setattr(self, "seek_dragging", True))
        self.progress.bind("<ButtonRelease-1>", self.seek_release)
        self.total_time = ttk.Label(timeline, text="0:00", width=8)
        self.total_time.pack(side="left")

        buttons = ttk.Frame(controls)
        buttons.pack(fill="x", pady=(10, 0))
        self.shuffle_button = ttk.Button(buttons, text="Acak: Mati", command=self.toggle_shuffle)
        self.shuffle_button.pack(side="left")
        self.repeat_button = ttk.Button(buttons, text="Ulang: Mati", command=self.toggle_repeat)
        self.repeat_button.pack(side="left", padx=6)

        navigation = ttk.Frame(buttons)
        navigation.pack(side="left", expand=True)
        ttk.Button(navigation, text="◀◀", width=4, command=self.previous_track).pack(side="left", padx=2)
        self.play_button = ttk.Button(navigation, text="Putar", width=8, command=self.play_selected)
        self.play_button.pack(side="left", padx=2)
        ttk.Button(navigation, text="Pause", width=8, command=self.toggle_pause).pack(side="left", padx=2)
        ttk.Button(navigation, text="Berhenti", width=8, command=self.stop).pack(side="left", padx=2)
        ttk.Button(navigation, text="▶▶", width=4, command=self.next_track).pack(side="left", padx=2)

        volume = ttk.Frame(buttons)
        volume.pack(side="right")
        ttk.Label(volume, text="Volume").pack(side="left")
        self.volume_scale = ttk.Scale(volume, from_=0, to=100, value=self.volume,
                                      command=self.change_volume, length=140)
        self.volume_scale.pack(side="left", padx=(6, 0))

        self.status = ttk.Label(main, text="Siap", foreground="#555555")
        self.status.pack(anchor="w", pady=(6, 0))

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.playlist = [path for path in data.get("playlist", [])
                             if isinstance(path, str) and os.path.isfile(path)]
            self.lyrics = {path: text for path, text in data.get("lyrics", {}).items()
                           if isinstance(text, str)}
            self.volume = max(0, min(100, int(data.get("volume", 70))))
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            self.status_text = f"Gagal memuat data: {error}"

    def save_data(self):
        data = {
            "playlist": self.playlist,
            "lyrics": self.lyrics,
            "volume": self.volume,
        }
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError as error:
            messagebox.showerror("Gagal menyimpan", str(error))

    def refresh_playlist(self):
        self.playlist_box.delete(0, tk.END)
        for path in self.playlist:
            self.playlist_box.insert(tk.END, os.path.basename(path))
        if hasattr(self, "status_text"):
            self.status.configure(text=self.status_text)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Pilih lagu",
            filetypes=[("File audio", "*.mp3 *.wav *.wma *.mid *.midi *.ogg"), ("Semua file", "*.*")]
        )
        self.add_paths(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Pilih folder lagu")
        if not folder:
            return
        paths = []
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if os.path.isfile(path) and path.lower().endswith(SUPPORTED_EXTENSIONS):
                paths.append(path)
        self.add_paths(paths)

    def add_paths(self, paths):
        added = 0
        for path in paths:
            normalized = os.path.abspath(path)
            if normalized.lower().endswith(SUPPORTED_EXTENSIONS) and normalized not in self.playlist:
                self.playlist.append(normalized)
                added += 1
        self.refresh_playlist()
        self.save_data()
        self.status.configure(text=f"{added} lagu ditambahkan ke playlist")

    def remove_selected(self):
        selection = self.playlist_box.curselection()
        if not selection:
            return
        index = selection[0]
        path = self.playlist[index]
        if index == self.current_index:
            self.stop()
        self.playlist.pop(index)
        self.lyrics.pop(path, None)
        if index < self.current_index:
            self.current_index -= 1
        elif index == self.current_index:
            self.current_index = -1
        self.refresh_playlist()
        self.save_data()

    def select_from_playlist(self, _event=None):
        selection = self.playlist_box.curselection()
        if selection:
            self.current_index = selection[0]
            self.load_lyrics()

    def current_path(self):
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None

    def play_selected(self):
        selection = self.playlist_box.curselection()
        if selection:
            self.current_index = selection[0]
        if not self.playlist:
            messagebox.showinfo("Playlist kosong", "Tambahkan lagu terlebih dahulu.")
            return
        if self.current_index < 0 or self.current_index >= len(self.playlist):
            self.current_index = 0
        self.play_track(self.playlist[self.current_index])

    def play_track(self, path):
        self.stop(close_only=True)
        alias = "music"
        result, _ = mci(f'open "{path}" type mpegvideo alias {alias}')
        if result != 0:
            result, _ = mci(f'open "{path}" alias {alias}')
        error, detail = mci(f"play {alias}")
        if error != 0:
            messagebox.showerror("Tidak dapat memutar", detail or "Format audio tidak didukung.")
            return
        self.is_playing = True
        self.paused = False
        self.play_finished = False
        self.play_button.configure(text="Putar")
        self.playlist_box.selection_clear(0, tk.END)
        self.playlist_box.selection_set(self.current_index)
        self.playlist_box.activate(self.current_index)
        self.load_lyrics()
        self.apply_volume()
        self.refresh_track_info()
        self.status.configure(text=f"Memutar: {os.path.basename(path)}")

    def toggle_pause(self):
        if not self.is_playing and not self.paused:
            self.play_selected()
            return
        if self.paused:
            error, _ = mci("resume music")
            if error == 0:
                self.paused = False
                self.status.configure(text="Melanjutkan pemutaran")
        else:
            error, _ = mci("pause music")
            if error == 0:
                self.paused = True
                self.status.configure(text="Pemutaran dijeda")

    def stop(self, close_only=False):
        mci("stop music")
        mci("close music")
        self.is_playing = False
        self.paused = False
        self.position_ms = 0
        self.duration_ms = 0
        if not close_only:
            self.progress.set(0)
            self.current_time.configure(text="0:00")
            self.total_time.configure(text="0:00")
            self.status.configure(text="Berhenti")

    def previous_track(self):
        if not self.playlist:
            return
        if self.position_ms > 5000:
            self.seek_to(0)
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play_selected()

    def next_track(self):
        if not self.playlist:
            return
        if self.shuffle:
            choices = [i for i in range(len(self.playlist)) if i != self.current_index]
            self.current_index = random.choice(choices) if choices else self.current_index
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_selected()

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.shuffle_button.configure(text=f"Acak: {'Nyala' if self.shuffle else 'Mati'}")

    def toggle_repeat(self):
        modes = ("off", "all", "one")
        labels = {"off": "Mati", "all": "Playlist", "one": "Lagu"}
        self.repeat_mode = modes[(modes.index(self.repeat_mode) + 1) % len(modes)]
        self.repeat_button.configure(text=f"Ulang: {labels[self.repeat_mode]}")

    def change_volume(self, value):
        self.volume = int(float(value))
        self.apply_volume()
        self.save_data()

    def apply_volume(self):
        mci(f"setaudio music volume to {self.volume * 10}")

    def seek_preview(self, value):
        if self.seek_dragging and self.duration_ms:
            position = int(float(value) / 1000 * self.duration_ms)
            self.current_time.configure(text=self.format_time(position / 1000))

    def seek_release(self, _event=None):
        if self.duration_ms:
            self.seek_to(self.progress.get() / 1000 * self.duration_ms)
        self.seek_dragging = False

    def seek_to(self, milliseconds):
        if not self.is_playing and not self.paused:
            return
        mci(f"seek music to {int(milliseconds)}")
        if not self.paused:
            mci("play music")

    def refresh_track_info(self):
        path = self.current_path()
        if not path:
            return
        if self.duration_ms == 0:
            _, length = mci("status music length")
            try:
                self.duration_ms = int(length)
            except ValueError:
                self.duration_ms = 0
        self.now_playing.configure(text=os.path.splitext(os.path.basename(path))[0])
        self.total_time.configure(text=self.format_time(self.duration_ms / 1000))

    def monitor(self):
        if self.is_playing and not self.paused:
            _, position = mci("status music position")
            try:
                self.position_ms = int(position)
            except ValueError:
                pass
            self.refresh_track_info()
            if self.duration_ms and not self.seek_dragging:
                self.progress.set(min(1000, self.position_ms / self.duration_ms * 1000))
                self.current_time.configure(text=self.format_time(self.position_ms / 1000))

            _, mode = mci("status music mode")
            if mode == "stopped" and self.duration_ms and self.position_ms >= self.duration_ms - 1000:
                if not self.play_finished:
                    self.play_finished = True
                    self.handle_track_finished()
        self.root.after(500, self.monitor)

    def handle_track_finished(self):
        if self.repeat_mode == "one":
            self.play_track(self.current_path())
        elif self.repeat_mode == "all":
            self.next_track()
        elif self.current_index < len(self.playlist) - 1 or self.shuffle:
            self.next_track()
        else:
            self.stop()
            self.status.configure(text="Playlist selesai")

    def load_lyrics(self):
        path = self.current_path()
        self.lyrics_text.delete("1.0", tk.END)
        if path and path in self.lyrics:
            self.lyrics_text.insert("1.0", self.lyrics[path])

    def save_lyrics(self):
        path = self.current_path()
        if not path:
            messagebox.showinfo("Pilih lagu", "Pilih lagu pada playlist terlebih dahulu.")
            return
        text = self.lyrics_text.get("1.0", tk.END).strip()
        if text:
            self.lyrics[path] = text
        else:
            self.lyrics.pop(path, None)
        self.save_data()
        self.status.configure(text=f"Lirik disimpan untuk {os.path.basename(path)}")

    def delete_lyrics(self):
        path = self.current_path()
        if path and path in self.lyrics:
            del self.lyrics[path]
            self.lyrics_text.delete("1.0", tk.END)
            self.save_data()
            self.status.configure(text="Lirik dihapus")

    def update_controls(self):
        initial_status = getattr(self, "status_text", "Siap")
        self.status.configure(text=initial_status)

    @staticmethod
    def format_time(seconds):
        seconds = max(0, int(seconds))
        return f"{seconds // 60}:{seconds % 60:02d}"


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()