
import random
import tkinter as tk
from tkinter import messagebox, simpledialog

COLORS = {
    1: "#E0E0E0",   # Jalan biasa
    3: "#4A9DF5",   # Tanjakan
    5: "#FF9999",   # Macet
    -1: "#303943",  # Tembok
}

CELL_SIZE = 50
PADDING = 4

ALGO_STYLES = {
    "UCS (Uniform Cost Search)": {"color": "#00A94F", "offset": (-6, -6)},
    "BFS (Breadth-First Search)": {"color": "#F06A16", "offset": (-6, 6)},
    "DFS (Depth-First Search)": {"color": "#963DCE", "offset": (6, 6)},
}

MIN_WINDOW_WIDTH = 950
MIN_WINDOW_HEIGHT = 720


def draw_tile(canvas, x1, y1, x2, y2, value, outline="#737D89", width=1):
    """Menggambar satu petak dengan tekstur sesuai jenis jalannya."""
    fill = COLORS.get(value, COLORS[1])

    canvas.create_rectangle(
        x1, y1, x2, y2,
        fill=fill,
        outline=outline,
        width=width,
    )

    tile_w = x2 - x1
    tile_h = y2 - y1

    if value == 3:
        # Tanjakan
        canvas.create_polygon(
            x1 + 1, y2 - tile_h * 0.28,
            x2 - 1, y2 - tile_h * 0.48,
            x2 - 1, y2 - 1,
            x1 + 1, y2 - 1,
            fill="#347FCB",
            outline=""
        )

        center_x = (x1 + x2) / 2
        arrow_y = y1 + tile_h * 0.43
        half_w = tile_w * 0.22
        arrow_h = tile_h * 0.19

        for offset in (0, tile_h * 0.23):
            top = arrow_y - offset

            canvas.create_line(
                center_x - half_w, top + arrow_h,
                center_x, top,
                center_x + half_w, top + arrow_h,
                fill="#FFFFFF",
                width=max(2, int(tile_w * 0.075)),
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND
            )

    elif value == -1:
        # Tembok
        mortar = "#65717D"
        brick_w = tile_w / 2
        brick_h = tile_h / 4

        for row in range(1, 4):
            y = y1 + row * brick_h
            canvas.create_line(
                x1 + 1, y, x2 - 1, y,
                fill=mortar,
                width=1
            )

        for row in range(4):
            y_top = y1 + row * brick_h
            offset = 0 if row % 2 == 0 else brick_w / 2
            x = x1 + offset

            while x < x2:
                if x > x1:
                    canvas.create_line(
                        x, y_top + 1,
                        x, min(y_top + brick_h, y2 - 1),
                        fill=mortar,
                        width=1
                    )
                x += brick_w


def draw_legend(parent):
    """Panel keterangan jenis petak dan bobot konsumsi baterai."""

    frame = tk.Frame(
        parent,
        bg="#F7F9FC",
        relief=tk.GROOVE,
        borderwidth=1,
        padx=12,
        pady=10
    )

    tk.Label(
        frame,
        text="Keterangan Petak",
        bg="#F7F9FC",
        fg="#172B4D",
        font=("Arial", 12, "bold")
    ).pack(anchor="w", pady=(0, 9))

    entries = [
        (1, "Jalan Biasa", "Bobot: 1% baterai", "Kecepatan normal"),
        (3, "Tanjakan", "Bobot: 3% baterai", "Butuh tenaga lebih"),
        (5, "Macet", "Bobot: 5% baterai", "Kecepatan lebih rendah"),
        (-1, "Tembok", "Tidak dapat dilewati", "Menjadi rintangan"),
    ]

    for value, title, weight, description in entries:
        item = tk.Frame(frame, bg="#F7F9FC")
        item.pack(fill=tk.X, pady=5)

        swatch = tk.Canvas(
            item,
            width=48,
            height=48,
            bg="#F7F9FC",
            highlightthickness=0
        )
        swatch.pack(side=tk.LEFT, padx=(0, 10))

        draw_tile(swatch, 3, 3, 45, 45, value, width=1)

        labels = tk.Frame(item, bg="#F7F9FC")
        labels.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            labels,
            text=title,
            bg="#F7F9FC",
            fg="#172B4D",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            labels,
            text=weight,
            bg="#F7F9FC",
            fg="#26364D",
            font=("Arial", 9)
        ).pack(anchor="w")

        tk.Label(
            labels,
            text=description,
            bg="#F7F9FC",
            fg="#667085",
            font=("Arial", 8)
        ).pack(anchor="w")

    return frame


class GridConfigurator:

    def __init__(self, root, rows, cols, initial=None):

        self.root = root
        self.root.title("EV Navigation - Custom Grid Configurator")
        self.root.configure(bg="#F4F6F9")

        self.rows = rows
        self.cols = cols

        self.grid = [[1 for _ in range(cols)] for _ in range(rows)]

        self.start_pos = (rows - 1, 0)
        self.goal_pos = (0, cols - 1)

        self.mode = 1

        if initial is not None:
            prev_grid, prev_start, prev_goal, prev_battery = initial

            self.grid = [row[:] for row in prev_grid]
            self.start_pos = prev_start
            self.goal_pos = prev_goal

        else:
            prev_battery = None

        self.battery_var = tk.StringVar(
            value="" if prev_battery is None else str(prev_battery)
        )

        self.battery = 100

        self.algo_vars = {
            name: tk.BooleanVar(
                value=name in [
                    "UCS (Uniform Cost Search)",
                    "BFS (Breadth-First Search)"
                ]
            )
            for name in ALGO_STYLES
        }

        self.selected_algorithms = []


        self.zoom_factor = 1.0
        self.zoom_min = 0.5
        self.zoom_max = 2.0
        self.zoom_step = 0.1

        self.base_canvas_width = cols * CELL_SIZE
        self.base_canvas_height = rows * CELL_SIZE

        self.scroll_container = tk.Frame(root, bg="#F4F6F9")
        self.scroll_container.pack(fill=tk.BOTH, expand=True)

        self.outer_canvas = tk.Canvas(
            self.scroll_container,
            bg="#F4F6F9",
            highlightthickness=0
        )

        self.vertical_scrollbar = tk.Scrollbar(
            self.scroll_container,
            orient=tk.VERTICAL,
            command=self.outer_canvas.yview
        )

        self.horizontal_scrollbar = tk.Scrollbar(
            self.scroll_container,
            orient=tk.HORIZONTAL,
            command=self.outer_canvas.xview
        )

        self.outer_canvas.configure(
            yscrollcommand=self.vertical_scrollbar.set,
            xscrollcommand=self.horizontal_scrollbar.set
        )

        self.vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.horizontal_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.outer_canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )


        self.content_frame = tk.Frame(
            self.outer_canvas,
            bg="#F4F6F9"
        )

        self.content_window = self.outer_canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor="nw"
        )


        self.content_frame.bind(
            "<Configure>",
            lambda event: self.outer_canvas.configure(
                scrollregion=self.outer_canvas.bbox("all")
            )
        )


        self.outer_canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel
        )

    
        self.outer_canvas.bind_all(
            "<Button-4>",
            lambda event: self.outer_canvas.yview_scroll(-3, "units")
        )

        self.outer_canvas.bind_all(
            "<Button-5>",
            lambda event: self.outer_canvas.yview_scroll(3, "units")
        )


        self.root.bind_all("<Control-plus>", lambda event: self.zoom_in())
        self.root.bind_all("<Control-equal>", lambda event: self.zoom_in())
        self.root.bind_all("<Control-minus>", lambda event: self.zoom_out())
        self.root.bind_all("<Control-KP_Add>", lambda event: self.zoom_in())
        self.root.bind_all("<Control-KP_Subtract>", lambda event: self.zoom_out())

        

        self.control_frame = tk.Frame(
            self.content_frame,
            bg="#F4F6F9"
        )

        self.control_frame.pack(
            side=tk.TOP,
            fill=tk.X,
            padx=10,
            pady=(10, 5)
        )

        tk.Label(
            self.control_frame,
            text="Alat Edit:",
            bg="#F4F6F9",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)

        self._tool_button("Jalan Biasa (1)", COLORS[1], "#202B3C", 1)
        self._tool_button("▲ Tanjakan (3)", COLORS[3], "white", 3)
        self._tool_button("🚗 Macet (5)", COLORS[5], "#7D2929", 5)
        self._tool_button("▦ Tembok (-1)", COLORS[-1], "white", -1)

        tk.Label(
            self.control_frame,
            text=" | ",
            bg="#F4F6F9"
        ).pack(side=tk.LEFT, padx=3)

        self._tool_button("Set Start (S)", "#DCEBFF", "#174EA6", "S")
        self._tool_button("Set Goal (G)", "#FFE1E1", "#B42318", "G")

        tk.Label(
            self.control_frame,
            text=" | ",
            bg="#F4F6F9"
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            self.control_frame,
            text="Acak Grid",
            bg="#FDE68A",
            command=self.randomize_grid
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            self.control_frame,
            text="Reset",
            bg="white",
            command=self.reset_grid
        ).pack(side=tk.LEFT, padx=2)

        tk.Label(
            self.control_frame,
            text=" | Zoom:",
            bg="#F4F6F9",
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(8, 3))

        tk.Button(
            self.control_frame,
            text="−",
            width=3,
            bg="white",
            font=("Arial", 10, "bold"),
            command=self.zoom_out
        ).pack(side=tk.LEFT, padx=2)

        self.zoom_label = tk.Label(
            self.control_frame,
            text="100%",
            bg="#F4F6F9",
            font=("Arial", 9, "bold"),
            width=5
        )
        self.zoom_label.pack(side=tk.LEFT, padx=2)

        tk.Button(
            self.control_frame,
            text="+",
            width=3,
            bg="white",
            font=("Arial", 10, "bold"),
            command=self.zoom_in
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            self.control_frame,
            text="Reset Zoom",
            bg="#DCEBFF",
            fg="#174EA6",
            command=self.reset_zoom
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(
            self.control_frame,
            text="Tembok %",
            bg="#F4F6F9"
        ).pack(side=tk.LEFT, padx=(8, 2))

        self.wall_ratio_var = tk.IntVar(value=20)

        tk.Spinbox(
            self.control_frame,
            from_=0,
            to=60,
            width=4,
            textvariable=self.wall_ratio_var
        ).pack(side=tk.LEFT, padx=2)


        self.algo_frame = tk.Frame(
            self.content_frame,
            relief=tk.GROOVE,
            borderwidth=1,
            padx=8,
            pady=6,
            bg="#FFFFFF"
        )

        self.algo_frame.pack(
            side=tk.TOP,
            fill=tk.X,
            padx=10,
            pady=5
        )

        tk.Label(
            self.algo_frame,
            text="Pilih Algoritma (Min. 1):",
            font=("Arial", 10, "bold"),
            bg="#FFFFFF"
        ).pack(side=tk.LEFT, padx=5)

        for name, style in ALGO_STYLES.items():

            cb = tk.Checkbutton(
                self.algo_frame,
                text=name,
                variable=self.algo_vars[name],
                fg=style["color"],
                activeforeground=style["color"],
                font=("Arial", 9, "bold"),
                bg="#FFFFFF",
                activebackground="#FFFFFF"
            )

            cb.pack(side=tk.LEFT, padx=8)

        self.battery_frame = tk.Frame(
            self.content_frame,
            relief=tk.GROOVE,
            borderwidth=1,
            padx=8,
            pady=6,
            bg="#FFFFFF"
        )

        self.battery_frame.pack(
            side=tk.TOP,
            fill=tk.X,
            padx=10,
            pady=5
        )

        tk.Label(
            self.battery_frame,
            text="Baterai Awal % (penuh = 100):",
            font=("Arial", 10, "bold"),
            bg="#FFFFFF"
        ).pack(side=tk.LEFT, padx=5)

        tk.Entry(
            self.battery_frame,
            textvariable=self.battery_var,
            width=6,
            justify="center"
        ).pack(side=tk.LEFT, padx=5)

       

        self.map_frame = tk.Frame(
            self.content_frame,
            bg="#F4F6F9"
        )

        self.map_frame.pack(
            side=tk.TOP,
            padx=12,
            pady=10
        )

        canvas_width = cols * CELL_SIZE
        canvas_height = rows * CELL_SIZE

        self.canvas = tk.Canvas(
            self.map_frame,
            width=canvas_width,
            height=canvas_height,
            bg="white",
            highlightthickness=0
        )

        self.canvas.pack(
            side=tk.LEFT,
            padx=(0, 16),
            anchor="n"
        )

        self.canvas.bind(
            "<Button-1>",
            self.on_cell_click
        )

        self.legend_frame = draw_legend(self.map_frame)

        self.legend_frame.pack(
            side=tk.LEFT,
            fill=tk.Y,
            anchor="n"
        )


        self.btn_done = tk.Button(
            self.content_frame,
            text="▶  Start Simulasi",
            bg="#25A65A",
            fg="white",
            activebackground="#1D8548",
            activeforeground="white",
            font=("Arial", 11, "bold"),
            padx=18,
            pady=6,
            command=self.finish_config
        )

        self.btn_done.pack(
            side=tk.TOP,
            pady=15
        )


        self._setup_window_size()
        self.draw_grid()

    def _on_mousewheel(self, event):
        self.outer_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
    )


    def zoom_in(self):
        self.set_zoom(min(self.zoom_factor + self.zoom_step, self.zoom_max))

    def zoom_out(self):
        self.set_zoom(max(self.zoom_factor - self.zoom_step, self.zoom_min))

    def reset_zoom(self):
        self.set_zoom(1.0)

    def set_zoom(self, new_zoom):
        """Ubah ukuran grid dengan menggambar ulang pada skala baru."""
        new_zoom = max(self.zoom_min, min(self.zoom_max, round(new_zoom, 2)))
        if new_zoom == self.zoom_factor:
            return

        self.zoom_factor = new_zoom
        self.zoom_label.config(text=f"{int(round(new_zoom * 100))}%")
        self.draw_grid()
        self.content_frame.update_idletasks()
        self.outer_canvas.configure(
            scrollregion=self.outer_canvas.bbox("all")
        )

    def _tool_button(self, text, bg, fg, mode):

        tk.Button(
            self.control_frame,
            text=text,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            font=("Arial", 9, "bold"),
            relief=tk.RAISED,
            padx=5,
            pady=3,
            command=lambda m=mode: self.set_mode(m)
        ).pack(side=tk.LEFT, padx=2)

    
    def _setup_window_size(self):

        self.root.update_idletasks()

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()


        width = min(
            max(MIN_WINDOW_WIDTH, 1400),
            screen_w - 40
        )

        height = min(
            max(MIN_WINDOW_HEIGHT, 850),
            screen_h - 80
        )

        x = max((screen_w - width) // 2, 0)
        y = max((screen_h - height) // 3, 0)

        self.root.minsize(
            min(MIN_WINDOW_WIDTH, screen_w - 40),
            min(MIN_WINDOW_HEIGHT, screen_h - 80)
        )

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )


    def set_mode(self, mode):
        self.mode = mode

    def reset_grid(self):

        self.grid = [
            [1 for _ in range(self.cols)]
            for _ in range(self.rows)
        ]

        self.draw_grid()

    def randomize_grid(self, max_attempts=30):

        wall_ratio = max(
            0,
            min(self.wall_ratio_var.get(), 60)
        ) / 100.0

        protected = {
            self.start_pos,
            self.goal_pos
        }

        terrain_pool = [1, 1, 1, 3, 5]

        new_grid = self.grid

        for _ in range(max_attempts):

            new_grid = [
                [1 for _ in range(self.cols)]
                for _ in range(self.rows)
            ]

            for r in range(self.rows):
                for c in range(self.cols):

                    if (r, c) in protected:
                        continue

                    if random.random() < wall_ratio:
                        new_grid[r][c] = -1

                    else:
                        new_grid[r][c] = random.choice(terrain_pool)

            if self._is_reachable(new_grid):
                break

        self.grid = new_grid
        self.draw_grid()

    def _is_reachable(self, grid):

        from collections import deque

        seen = {self.start_pos}
        queue = deque([self.start_pos])

        while queue:

            r, c = queue.popleft()

            if (r, c) == self.goal_pos:
                return True

            for dr, dc in (
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1)
            ):

                nr = r + dr
                nc = c + dc

                if (
                    0 <= nr < self.rows
                    and 0 <= nc < self.cols
                    and (nr, nc) not in seen
                    and grid[nr][nc] != -1
                ):

                    seen.add((nr, nc))
                    queue.append((nr, nc))

        return False

    def draw_grid(self):
        """Gambar ulang grid sesuai zoom aktif."""
        self.canvas.delete("all")

        cell = max(12, int(CELL_SIZE * self.zoom_factor))
        padding = max(1, int(PADDING * self.zoom_factor))
        self.current_cell_size = cell

        canvas_width = self.cols * cell
        canvas_height = self.rows * cell
        self.canvas.configure(
            width=canvas_width,
            height=canvas_height,
            scrollregion=(0, 0, canvas_width, canvas_height)
        )

        marker_radius = max(7, int(14 * self.zoom_factor))
        marker_font = max(8, int(15 * self.zoom_factor))

        for r in range(self.rows):
            for c in range(self.cols):
                value = self.grid[r][c]
                x1 = c * cell + padding
                y1 = r * cell + padding
                x2 = (c + 1) * cell - padding
                y2 = (r + 1) * cell - padding

                draw_tile(self.canvas, x1, y1, x2, y2, value,
                          width=max(1, self.zoom_factor))

                pos = (r, c)
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2

                if pos == self.start_pos:
                    self.canvas.create_oval(
                        cx - marker_radius, cy - marker_radius,
                        cx + marker_radius, cy + marker_radius,
                        fill="#FFFFFF", outline="#1769E0",
                        width=max(1, int(2 * self.zoom_factor))
                    )
                    self.canvas.create_text(
                        cx, cy, text="S", fill="#1769E0",
                        font=("Arial", marker_font, "bold")
                    )

                elif pos == self.goal_pos:
                    self.canvas.create_oval(
                        cx - marker_radius, cy - marker_radius,
                        cx + marker_radius, cy + marker_radius,
                        fill="#FFFFFF", outline="#D92D20",
                        width=max(1, int(2 * self.zoom_factor))
                    )
                    self.canvas.create_text(
                        cx, cy, text="G", fill="#D92D20",
                        font=("Arial", marker_font, "bold")
                    )

        self.content_frame.update_idletasks()
        self.outer_canvas.configure(
            scrollregion=self.outer_canvas.bbox("all")
        )

    def on_cell_click(self, event):

        cell = getattr(self, "current_cell_size", CELL_SIZE)
        c = int(event.x // cell)
        r = int(event.y // cell)

        if 0 <= r < self.rows and 0 <= c < self.cols:

            if self.mode == "S":

                if self.grid[r][c] == -1:
                    messagebox.showerror(
                        "Error",
                        "Titik Start tidak boleh berada di atas Tembok!"
                    )
                    return

                self.start_pos = (r, c)

            elif self.mode == "G":

                if self.grid[r][c] == -1:
                    messagebox.showerror(
                        "Error",
                        "Titik Goal tidak boleh berada di atas Tembok!"
                    )
                    return

                self.goal_pos = (r, c)

            else:

                if (
                    (r, c) in (self.start_pos, self.goal_pos)
                    and self.mode == -1
                ):

                    messagebox.showerror(
                        "Error",
                        "Petak Start atau Goal tidak bisa diubah menjadi Tembok!"
                    )
                    return

                self.grid[r][c] = self.mode

            self.draw_grid()

    def finish_config(self):

        if self.start_pos == self.goal_pos:

            messagebox.showerror(
                "Error",
                "Titik Start dan Goal tidak boleh di koordinat yang sama!"
            )
            return

        chosen = [
            name
            for name, var in self.algo_vars.items()
            if var.get()
        ]

        if not chosen:

            messagebox.showwarning(
                "Peringatan",
                "Pilih minimal satu algoritma sebelum memulai simulasi!"
            )
            return

        raw = self.battery_var.get().strip()

        if raw == "":
            battery = 100

        else:

            try:
                battery = int(raw)

            except ValueError:

                messagebox.showerror(
                    "Error",
                    "Baterai awal harus berupa angka bulat!"
                )
                return

            if not 1 <= battery <= 100:

                messagebox.showerror(
                    "Error",
                    "Baterai awal harus antara 1 sampai 100!"
                )
                return

        self.battery = battery
        self.selected_algorithms = chosen

        self.root.destroy()


def get_env(initial=None):

    """Membuka konfigurator grid."""

    if initial is None:

        root = tk.Tk()
        root.withdraw()

        cols = simpledialog.askinteger(
            "Input Grid",
            "Masukkan jumlah Kolom (lebar, misal: 6-12):",
            initialvalue=8,
            minvalue=3,
            maxvalue=20
        )

        rows = simpledialog.askinteger(
            "Input Grid",
            "Masukkan jumlah Baris (tinggi, misal: 6-12):",
            initialvalue=8,
            minvalue=3,
            maxvalue=20
        )

        if not cols or not rows:
            cols, rows = 8, 8

        root.destroy()

    else:

        rows = len(initial[0])
        cols = len(initial[0][0])

    config_root = tk.Tk()

    app = GridConfigurator(
        config_root,
        rows,
        cols,
        initial
    )

    config_root.mainloop()

    return (
        app.grid,
        app.start_pos,
        app.goal_pos,
        app.selected_algorithms,
        app.battery
    )


def draw_multi_results(grid, start, goal, results):
    """Menampilkan hasil algoritma dan animasi mobil dengan zoom + scroll."""
    action = {"value": None}
    root = tk.Tk()
    root.title("EV Navigation - Simulasi Pergerakan Kendaraan")
    root.configure(bg="#F4F6F9")

    rows, cols = len(grid), len(grid[0])
    zoom = {"value": 1.0}
    zoom_min, zoom_max, zoom_step = 0.5, 2.0, 0.1
    animation_delay = 450
    animation_job = {"id": None}

    def choose(value):
        action["value"] = value
        if animation_job["id"] is not None:
            try:
                root.after_cancel(animation_job["id"])
            except tk.TclError:
                pass
        root.destroy()

    scroll_container = tk.Frame(root, bg="#F4F6F9")
    scroll_container.pack(fill=tk.BOTH, expand=True)

    view = tk.Canvas(scroll_container, bg="#F4F6F9", highlightthickness=0)
    ybar = tk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=view.yview)
    xbar = tk.Scrollbar(scroll_container, orient=tk.HORIZONTAL, command=view.xview)
    view.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
    ybar.pack(side=tk.RIGHT, fill=tk.Y)
    xbar.pack(side=tk.BOTTOM, fill=tk.X)
    view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    content = tk.Frame(view, bg="#F4F6F9")
    content_window = view.create_window((0, 0), window=content, anchor="nw")

    def update_scroll_region(_event=None):
        view.configure(scrollregion=view.bbox("all"))

    content.bind("<Configure>", update_scroll_region)


    zoom_bar = tk.Frame(content, bg="#F4F6F9")
    zoom_bar.pack(fill=tk.X, padx=15, pady=(12, 5))

    tk.Label(
        zoom_bar, text="Zoom Grid Simulasi:", bg="#F4F6F9",
        font=("Arial", 9, "bold")
    ).pack(side=tk.LEFT, padx=(0, 6))

    zoom_label = tk.Label(
        zoom_bar, text="100%", width=6, bg="#F4F6F9",
        font=("Arial", 9, "bold")
    )
    zoom_label.pack(side=tk.LEFT, padx=3)

    main_frame = tk.Frame(content, bg="#F4F6F9")
    main_frame.pack(padx=15, pady=(5, 15), anchor="nw")

    canvas = tk.Canvas(
        main_frame,
        width=cols * CELL_SIZE,
        height=rows * CELL_SIZE,
        bg="white",
        highlightthickness=0
    )
    canvas.pack(side=tk.LEFT, padx=(0, 15), anchor="n")

    panel = tk.Frame(
        main_frame, relief=tk.GROOVE, borderwidth=1,
        padx=12, pady=12, bg="#FFFFFF"
    )
    panel.pack(side=tk.RIGHT, fill=tk.Y, anchor="n")

    tk.Label(
        panel, text="Hasil & Perbandingan Algoritma",
        font=("Arial", 12, "bold"), bg="#FFFFFF"
    ).pack(anchor="w", pady=(0, 8))

    tk.Label(
        panel, text="Mobil bergerak bersamaan • 1 langkah = 450 ms",
        font=("Arial", 8), fg="#667085", bg="#FFFFFF"
    ).pack(anchor="w", pady=(0, 8))

    car_states = []
    car_offsets = [(-10, -9), (10, -9), (0, 10)]

    for index, res in enumerate(results):
        name = res["name"]
        color = ALGO_STYLES[name]["color"]
        path = res.get("path", [])
        initial_battery = int(res.get("battery", 100))

        card = tk.Frame(panel, bg="#FFFFFF", pady=5)
        card.pack(fill=tk.X, anchor="w")

        header = tk.Frame(card, bg="#FFFFFF")
        header.pack(anchor="w")
        tk.Label(
            header, text="●", fg=color, bg="#FFFFFF",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT)
        tk.Label(
            header, text=f" {name}", bg="#FFFFFF",
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT)

        if path:
            planned_cost = sum(grid[r][c] for r, c in path[1:])
            detail = (
                f"Rute: {len(path)} petak | Estimasi konsumsi: {planned_cost}%\n"
                f"Node dieksplorasi: {res.get('visited', 0)} | "
                f"Waktu pencarian: {res.get('time_ms', 0):.2f} ms"
            )
            current_position = path[0]
            active = len(path) > 1
            initial_status = "Menunggu pergerakan" if active else "Sudah di tujuan"
        else:
            detail = "Rute tidak ditemukan oleh algoritma ini."
            current_position = start
            active = False
            initial_status = "Rute tidak ditemukan"

        tk.Label(
            card, text=detail, justify=tk.LEFT,
            font=("Consolas", 8), bg="#FFFFFF", fg="#475467"
        ).pack(anchor="w", pady=(3, 2))

        live_label = tk.Label(
            card, text=f"Baterai: {initial_battery}% | {initial_status}",
            justify=tk.LEFT, font=("Arial", 9, "bold"),
            fg=color, bg="#FFFFFF"
        )
        live_label.pack(anchor="w")

        warning_frame = tk.Frame(
            card,
            bg="#FEE4E2",
            highlightbackground="#D92D20",
            highlightthickness=1,
            padx=8,
            pady=6
        )

        tk.Label(
            warning_frame,
            text="⚠",
            font=("Arial", 13, "bold"),
            fg="#D92D20",
            bg="#FEE4E2"
        ).pack(side=tk.LEFT, padx=(0, 7))

        tk.Label(
            warning_frame,
            text="BATERAI TIDAK CUKUP\nSisa baterai: 0%",
            font=("Arial", 9, "bold"),
            fg="#B42318",
            bg="#FEE4E2",
            justify=tk.LEFT
        ).pack(side=tk.LEFT)

        car_states.append({
            "name": name,
            "warning_frame": warning_frame,
            "color": color,
            "path": path,
            "step": 0,
            "battery": initial_battery,
            "position": current_position,
            "active": active,
            "status": initial_status,
            "offset": car_offsets[index % len(car_offsets)],
            "label": live_label,
        })

        tk.Frame(card, height=1, bg="#D9DEE7").pack(fill=tk.X, pady=4)

    if not any(state["path"] for state in car_states):
        tk.Label(
            panel, text="Tidak ada algoritma yang menemukan rute.",
            fg="white", bg="#D32F2F", font=("Arial", 9, "bold"),
            padx=8, pady=6
        ).pack(fill=tk.X, pady=5)

    def draw_car(state, scale):
        r, c = state["position"]
        ox, oy = state["offset"]
        cx = (c * CELL_SIZE + CELL_SIZE / 2 + ox) * scale
        cy = (r * CELL_SIZE + CELL_SIZE / 2 + oy) * scale
        color = state["color"]
        unit = scale

        badge_y = cy - 17 * unit
        canvas.create_rectangle(
            cx - 15 * unit, badge_y - 6 * unit,
            cx + 15 * unit, badge_y + 6 * unit,
            fill="white", outline=color, width=max(1, unit)
        )
        canvas.create_text(
            cx, badge_y, text=f"{state['battery']}%", fill=color,
            font=("Arial", max(5, int(7 * unit)), "bold")
        )
        canvas.create_polygon(
            cx - 9 * unit, cy - 3 * unit,
            cx - 6 * unit, cy - 8 * unit,
            cx + 6 * unit, cy - 8 * unit,
            cx + 9 * unit, cy - 3 * unit,
            cx + 9 * unit, cy + 5 * unit,
            cx - 9 * unit, cy + 5 * unit,
            fill=color, outline="white", width=max(1, unit)
        )
        canvas.create_rectangle(
            cx - 5 * unit, cy - 6 * unit,
            cx + 5 * unit, cy - 3 * unit,
            fill="#DCEBFF", outline="white", width=max(1, unit)
        )
        for wheel_x in (cx - 6 * unit, cx + 6 * unit):
            canvas.create_oval(
                wheel_x - 2 * unit, cy + 3 * unit,
                wheel_x + 2 * unit, cy + 7 * unit,
                fill="#202B3C", outline="white", width=max(1, unit)
            )

    def render_scene():
        """Redraw all map elements at the current zoom, avoiding cumulative scaling."""
        scale = zoom["value"]
        cell = CELL_SIZE * scale
        pad = max(1, PADDING * scale)
        canvas.delete("all")
        canvas.configure(
            width=max(1, int(cols * cell)),
            height=max(1, int(rows * cell)),
            scrollregion=(0, 0, cols * cell, rows * cell)
        )

        # Base terrain.
        for r in range(rows):
            for c in range(cols):
                x1 = c * cell + pad
                y1 = r * cell + pad
                x2 = (c + 1) * cell - pad
                y2 = (r + 1) * cell - pad
                draw_tile(canvas, x1, y1, x2, y2, grid[r][c],
                          width=max(1, scale))

        # Planned routes.
        for res in results:
            path = res.get("path", [])
            if not path:
                continue
            style = ALGO_STYLES[res["name"]]
            ox, oy = style["offset"]
            coords = []
            for r, c in path:
                cx = (c * CELL_SIZE + CELL_SIZE / 2 + ox) * scale
                cy = (r * CELL_SIZE + CELL_SIZE / 2 + oy) * scale
                coords.extend([cx, cy])
            if len(coords) >= 4:
                canvas.create_line(
                    *coords, fill=style["color"],
                    width=max(1, 2 * scale), dash=(5, 3)
                )

        # Start and goal markers.
        for pos, label, color in (
            (start, "S", "#1769E0"),
            (goal, "G", "#D92D20")
        ):
            r, c = pos
            cx = (c * CELL_SIZE + CELL_SIZE / 2) * scale
            cy = (r * CELL_SIZE + CELL_SIZE / 2) * scale
            radius = 13 * scale
            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill="white", outline=color, width=max(1, 2 * scale)
            )
            canvas.create_text(
                cx, cy, text=label, fill=color,
                font=("Arial", max(6, int(12 * scale)), "bold")
            )

        # Current car positions and live battery badges.
        for state in car_states:
            if state["path"]:
                draw_car(state, scale)

        zoom_label.config(text=f"{int(round(scale * 100))}%")
        content.update_idletasks()
        view.configure(scrollregion=view.bbox("all"))

    def set_zoom(value):
        zoom["value"] = max(zoom_min, min(zoom_max, round(value, 2)))
        render_scene()

    tk.Button(
        zoom_bar, text="−", width=3, bg="white",
        font=("Arial", 10, "bold"),
        command=lambda: set_zoom(zoom["value"] - zoom_step)
    ).pack(side=tk.LEFT, padx=2)
    tk.Button(
        zoom_bar, text="+", width=3, bg="white",
        font=("Arial", 10, "bold"),
        command=lambda: set_zoom(zoom["value"] + zoom_step)
    ).pack(side=tk.LEFT, padx=2)
    tk.Button(
        zoom_bar, text="Reset Zoom", bg="#DCEBFF", fg="#174EA6",
        command=lambda: set_zoom(1.0)
    ).pack(side=tk.LEFT, padx=4)
    tk.Label(
        zoom_bar, text="Ctrl + + / Ctrl - - untuk zoom",
        bg="#F4F6F9", fg="#667085", font=("Arial", 8)
    ).pack(side=tk.LEFT, padx=8)

    def animate_step():
        """Majukan seluruh mobil satu petak pada tick yang sama."""
        any_active = False

        # Proses pergerakan setiap algoritma
        for state in car_states:
            if not state["active"]:
                continue

            path = state["path"]
            next_step = state["step"] + 1

            if next_step >= len(path):
                state["active"] = False
                state["status"] = "Tiba di Goal"
                continue

            next_position = path[next_step]
            nr, nc = next_position
            tile_cost = grid[nr][nc]

            if tile_cost == -1:
                state["active"] = False
                state["status"] = "Berhenti: menemukan tembok"
                continue

            # Periksa kecukupan baterai
            if state["battery"] < tile_cost:
                state["battery"] = 0
                state["active"] = False
                state["status"] = "Baterai tidak cukup"
                continue

            # Pindahkan mobil dan kurangi baterai
            state["step"] = next_step
            state["position"] = next_position
            state["battery"] -= tile_cost

            if next_position == goal:
                state["active"] = False
                state["status"] = "Tiba di Goal"
            elif state["battery"] == 0:
                state["active"] = False
                state["status"] = "Baterai habis"
            else:
                state["status"] = "Sedang berjalan"

        # Update tampilan setiap algoritma secara terpisah
        for state in car_states:
            state["label"].config(
                text=f"Baterai: {state['battery']}% | {state['status']}"
            )

            # Warning box milik masing-masing algoritma
            warning = state["warning_frame"]

            if state["status"] == "Baterai tidak cukup":
                if not warning.winfo_manager():
                    warning.pack(
                        anchor="w",
                        fill=tk.X,
                        pady=(5, 2)
                    )
            else:
                warning.pack_forget()

            if state["active"]:
                any_active = True

        # Render posisi mobil terbaru
        render_scene()

        # Lanjutkan animasi atau tampilkan simulasi selesai
        if any_active:
            animation_job["id"] = root.after(
                animation_delay,
                animate_step
            )
        else:
            tk.Label(
                panel,
                text="Simulasi selesai.",
                fg="#167A3E",
                bg="#FFFFFF",
                font=("Arial", 9, "bold")
            ).pack(anchor="w", pady=(5, 2))

            content.update_idletasks()
            view.configure(scrollregion=view.bbox("all"))

    
    btn_frame = tk.Frame(panel, bg="#FFFFFF")
    btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

    tk.Button(
        btn_frame, text="🔁 Percobaan Baru (Peta Sama)",
        bg="#25A65A", fg="white", font=("Arial", 9, "bold"),
        command=lambda: choose("same")
    ).pack(fill=tk.X, pady=2)
    tk.Button(
        btn_frame, text="🗺 Percobaan Baru (Peta Baru)",
        bg="#2478D4", fg="white", font=("Arial", 9, "bold"),
        command=lambda: choose("new")
    ).pack(fill=tk.X, pady=2)
    tk.Button(
        btn_frame, text="Keluar", bg="#D92D20", fg="white",
        font=("Arial", 9, "bold"), command=lambda: choose(None)
    ).pack(fill=tk.X, pady=2)

    
    def on_mousewheel(event):
        if event.state & 0x0001:
            view.xview_scroll(int(-event.delta / 120), "units")
        else:
            view.yview_scroll(int(-event.delta / 120), "units")

    root.bind_all("<MouseWheel>", on_mousewheel)
    root.bind_all("<Button-4>", lambda event: view.yview_scroll(-3, "units"))
    root.bind_all("<Button-5>", lambda event: view.yview_scroll(3, "units"))
    root.bind_all("<Control-plus>", lambda event: set_zoom(zoom["value"] + zoom_step))
    root.bind_all("<Control-equal>", lambda event: set_zoom(zoom["value"] + zoom_step))
    root.bind_all("<Control-minus>", lambda event: set_zoom(zoom["value"] - zoom_step))
    root.bind_all("<Control-KP_Add>", lambda event: set_zoom(zoom["value"] + zoom_step))
    root.bind_all("<Control-KP_Subtract>", lambda event: set_zoom(zoom["value"] - zoom_step))

    
    render_scene()
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    width = min(max(1000, root.winfo_reqwidth() + 30), screen_w - 40)
    height = min(max(700, root.winfo_reqheight() + 30), screen_h - 80)
    x = max((screen_w - width) // 2, 0)
    y = max((screen_h - height) // 3, 0)
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.minsize(min(750, screen_w - 40), min(500, screen_h - 80))

    root.after(700, animate_step)
    root.mainloop()
    return action["value"]
