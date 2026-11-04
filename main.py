import math
import time
import tkinter as tk
from tkinter import ttk

W, H = 900, 600  # размер холста

# ----------------------------------------------------------------------------
# Справочники алгоритмов
# ----------------------------------------------------------------------------
ALGOS = [
    ("step",       "Пошаговый алгоритм"), #(0,0) ->(2, -1) はおもしろいです。
    ("dda",        "ЦДА (DDA)"), # (0,0) -> (14,1) はおもしろいです。
    ("bresLine",   "Брезенхем — отрезок"),
    ("bresCircle", "Брезенхем — окружность"),
]
ALGO_NAMES = dict(ALGOS)
NAME_TO_KEY = {name: key for key, name in ALGOS}

# Уникальный цвет и форма для каждого алгоритма
ALGO_STYLES = {
    "step":       {"color": "#e53935", "shape": "rect"},
    "dda":        {"color": "#43a047", "shape": "circle"},
    "bresLine":   {"color": "#1e88e5", "shape": "diamond"},
    "bresCircle": {"color": "#8e24aa", "shape": "circle"},
}


# ----------------------------------------------------------------------------
# Вспомогательные функции
# ----------------------------------------------------------------------------
def js_round(v):
    """Округление как Math.round в JS (0.5 — вверх, -0.5 — вверх)."""
    return int(math.floor(v + 0.5))


def unique_points(points):
    seen = set()
    out = []
    for p in points:
        key = (p[0], p[1])
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


# ----------------------------------------------------------------------------
# Растровые алгоритмы
# ----------------------------------------------------------------------------
def step_line(x1, y1, x2, y2):
    pts = []
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return [(x1, y1)]

    if abs(dx) >= abs(dy):
        sx = 1 if dx >= 0 else -1
        x = x1
        while True:
            y = js_round(y1 + (dy / dx) * (x - x1))
            pts.append((x, y))
            if x == x2:
                break
            x += sx
    else:
        sy = 1 if dy >= 0 else -1
        y = y1
        while True:
            x = js_round(x1 + (dx / dy) * (y - y1))
            pts.append((x, y))
            if y == y2:
                break
            y += sy
    return pts


def dda_line(x1, y1, x2, y2):
    pts = []
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return [(x1, y1)]

    x_inc = dx / steps
    y_inc = dy / steps
    x = x1
    y = y1
    for _ in range(steps + 1):
        pts.append((js_round(x), js_round(y)))
        x += x_inc
        y += y_inc
    return pts


def bresenham_line(x1, y1, x2, y2):
    pts = []
    x, y = x1, y1
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx + dy

    while True:
        pts.append((x, y))
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return pts


def bresenham_circle(cx, cy, r):
    pts = []
    if r < 0:
        return pts

    x = 0
    y = r
    d = 3 - 2 * r

    def add8(px, py):
        pts.append((cx + px, cy + py))
        pts.append((cx + py, cy + px))
        pts.append((cx + py, cy - px))
        pts.append((cx + px, cy - py))
        pts.append((cx - px, cy - py))
        pts.append((cx - py, cy - px))
        pts.append((cx - py, cy + px))
        pts.append((cx - px, cy + py))

    while x <= y:
        add8(x, y)
        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1
        x += 1
    return unique_points(pts)


def build_points(algo, p):
    if algo == "step":
        return step_line(p["x1"], p["y1"], p["x2"], p["y2"])
    if algo == "dda":
        return dda_line(p["x1"], p["y1"], p["x2"], p["y2"])
    if algo == "bresLine":
        return bresenham_line(p["x1"], p["y1"], p["x2"], p["y2"])
    if algo == "bresCircle":
        return bresenham_circle(p["x1"], p["y1"], p["r"])
    return []


# ----------------------------------------------------------------------------
# Приложение
# ----------------------------------------------------------------------------
class RasterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("ЛР3 — Базовые растровые алгоритмы")
        root.minsize(1180, 780)

        self.points = []
        self.scale = 40
        self.timer = None
        self.anim_i = -1
        self.last_params = None
        self.step_iids = []
        self.mode = None  # None | "draw" | "compare"

        self._build_ui()
        self.read_params()
        self.draw_grid()

    # ---------------- построение интерфейса ----------------
    def _build_ui(self):
        header = ttk.Label(
            self.root,
            text="Лабораторная работа 3. Базовые растровые алгоритмы",
            font=("TkDefaultFont", 12, "bold"),
        )
        header.pack(anchor="w", padx=16, pady=(12, 6))

        main = ttk.Frame(self.root, padding=(16, 0, 16, 16))
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(main, text="Управление", padding=10)
        left.grid(row=0, column=0, sticky="nw")
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Алгоритм").grid(row=0, column=0, sticky="w")
        self.v_algo = tk.StringVar(value=ALGO_NAMES["bresLine"])
        ttk.Combobox(
            left, textvariable=self.v_algo, state="readonly",
            values=[name for _, name in ALGOS], width=30,
        ).grid(row=1, column=0, sticky="ew", pady=(2, 8))

        self.v_x1 = tk.StringVar(value="2")
        self.v_y1 = tk.StringVar(value="3")
        self.v_x2 = tk.StringVar(value="11")
        self.v_y2 = tk.StringVar(value="7")
        self.v_r = tk.StringVar(value="5")

        io = ttk.Frame(left)
        io.grid(row=2, column=0, sticky="ew")
        io.columnconfigure(0, weight=1)
        io.columnconfigure(1, weight=1)

        ttk.Label(io, text="x1 / центр x").grid(row=0, column=0, sticky="w")
        ttk.Label(io, text="y1 / центр y").grid(row=0, column=1, sticky="w", padx=(6, 0))
        ttk.Entry(io, textvariable=self.v_x1, width=10).grid(row=1, column=0, sticky="ew", pady=(2, 6))
        ttk.Entry(io, textvariable=self.v_y1, width=10).grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(2, 6))

        ttk.Label(io, text="x2").grid(row=2, column=0, sticky="w")
        ttk.Label(io, text="y2").grid(row=2, column=1, sticky="w", padx=(6, 0))
        ttk.Entry(io, textvariable=self.v_x2, width=10).grid(row=3, column=0, sticky="ew", pady=(2, 6))
        ttk.Entry(io, textvariable=self.v_y2, width=10).grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=(2, 6))

        ttk.Label(io, text="Радиус (для окружности)").grid(row=4, column=0, columnspan=2, sticky="w")
        ttk.Entry(io, textvariable=self.v_r, width=10).grid(row=5, column=0, sticky="ew", pady=(2, 8))

        ttk.Label(left, text="Масштаб, px / ед.").grid(row=3, column=0, sticky="w")
        self.scale_var = tk.IntVar(value=40)
        tk.Scale(
            left, from_=10, to=80, orient="horizontal", resolution=1,
            variable=self.scale_var, command=self._on_scale,
            showvalue=True, length=260,
        ).grid(row=4, column=0, sticky="ew")

        self.v_grid = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left, text="показывать сетку",
            variable=self.v_grid, command=self._on_grid_toggle,
        ).grid(row=5, column=0, sticky="w", pady=(6, 8))

        btns = ttk.Frame(left)
        btns.grid(row=6, column=0, sticky="ew", pady=(6, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        ttk.Button(btns, text="Построить", command=self.draw).grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        ttk.Button(btns, text="Анимация", command=self.animate).grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(btns, text="Замер времени", command=self.timing).grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        ttk.Button(btns, text="Очистить", command=self.clear_all).grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(btns, text="Сравнить все (наложение)", command=self.compare).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=2)

        ttk.Label(
            left,
            text="Для окружности используются x1, y1 как центр и поле «Радиус». "
                 "Для отрезков — x1, y1 и x2, y2.",
            wraplength=260, foreground="#555",
        ).grid(row=7, column=0, sticky="w", pady=(10, 0))

        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        canvas_frame = tk.Frame(right, bd=1, relief="solid", bg="#d0d7de")
        canvas_frame.grid(row=0, column=0, sticky="nw")
        self.canvas = tk.Canvas(
            canvas_frame, width=W, height=H, bg="white", highlightthickness=0)
        self.canvas.pack()

        info_panel = ttk.LabelFrame(right, text="Результаты", padding=10)
        info_panel.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        info_panel.columnconfigure(0, weight=1)
        info_panel.rowconfigure(1, weight=1)

        self.info = ttk.Label(
            info_panel,
            text="Выберите алгоритм и нажмите «Построить».",
            justify="left", anchor="nw", font="TkFixedFont", wraplength=880,
        )
        self.info.grid(row=0, column=0, sticky="ew")

        tree_frame = ttk.Frame(info_panel)
        tree_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame, columns=("n", "x", "y"), show="headings", height=9)
        self.tree.heading("n", text="№")
        self.tree.heading("x", text="x")
        self.tree.heading("y", text="y")
        self.tree.column("n", width=60, anchor="e", stretch=False)
        self.tree.column("x", width=80, anchor="e", stretch=False)
        self.tree.column("y", width=80, anchor="e", stretch=False)
        self.tree.tag_configure("cur", background="#ffcdd2", font=("TkDefaultFont", 9, "bold"))
        self.tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

    # ---------------- параметры ----------------
    @staticmethod
    def _to_int(var, default=0):
        try:
            return int(float(str(var.get()).strip().replace(",", ".")))
        except (ValueError, TypeError):
            return default

    def read_params(self):
        x1 = self._to_int(self.v_x1)
        y1 = self._to_int(self.v_y1)
        x2 = self._to_int(self.v_x2)
        y2 = self._to_int(self.v_y2)
        r = max(0, self._to_int(self.v_r))
        algo = NAME_TO_KEY.get(self.v_algo.get(), "bresLine")
        try:
            self.scale = max(1, int(self.scale_var.get()))
        except (ValueError, TypeError):
            self.scale = 40
        return {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "r": r, "algo": algo}

    # ---------------- отрисовка ----------------
    def draw_grid(self):
        c = self.canvas
        c.delete("all")
        c.create_rectangle(0, 0, W, H, fill="white", outline="")

        s = self.scale
        ox, oy = W / 2, H / 2

        if self.v_grid.get():
            min_x = math.ceil(-ox / s)
            max_x = math.floor((W - ox) / s)
            min_y = math.ceil((oy - H) / s)
            max_y = math.floor(oy / s)

            for x in range(min_x, max_x + 1):
                sx = ox + x * s
                c.create_line(sx, 0, sx, H, fill="#e6e6e6")
            for y in range(min_y, max_y + 1):
                sy = oy - y * s
                c.create_line(0, sy, W, sy, fill="#e6e6e6")

            label_step = 1 if s >= 35 else (2 if s >= 20 else 5)
            for x in range(min_x, max_x + 1):
                if x != 0 and x % label_step == 0:
                    c.create_text(ox + x * s, oy + 3, text=str(x),
                                  anchor="n", fill="#666", font=("TkDefaultFont", 8))
            for y in range(min_y, max_y + 1):
                if y != 0 and y % label_step == 0:
                    c.create_text(ox - 4, oy - y * s, text=str(y),
                                  anchor="e", fill="#666", font=("TkDefaultFont", 8))

        c.create_line(0, oy, W, oy, fill="black", width=2)
        c.create_line(ox, 0, ox, H, fill="black", width=2)
        c.create_text(ox + 4, oy + 4, text="0", anchor="nw", fill="black")

    def draw_pixel(self, x, y, color, factor=1.0, shape="rect", highlight=False):
        """Пиксель (x, y) целиком заполняет ячейку сетки [x, x+1] x [y, y+1]."""
        ox, oy = W / 2, H / 2
        s = self.scale

        left   = ox + x * s
        right  = left + s
        bottom = oy - y * s
        top    = bottom - s

        if factor != 1.0:
            cx, cy = (left + right) / 2, (top + bottom) / 2
            h = s * factor / 2
            left, right, top, bottom = cx - h, cx + h, cy - h, cy + h

        if highlight:
            fill_color, outline_color, outline_width = "#ffeb3b", "black", 2
        else:
            fill_color, outline_color, outline_width = color, "", 0

        if shape == "circle":
            self.canvas.create_oval(left, top, right, bottom,
                                    fill=fill_color, outline=outline_color,
                                    width=outline_width)
        elif shape == "diamond":
            cx, cy = (left + right) / 2, (top + bottom) / 2
            self.canvas.create_polygon(cx, top, right, cy, cx, bottom, left, cy,
                                       fill=fill_color, outline=outline_color,
                                       width=outline_width)
        else:  # rect — сплошь залитая ячейка
            self.canvas.create_rectangle(left, top, right, bottom,
                                         fill=fill_color, outline=outline_color,
                                         width=outline_width)

    def render(self, points, algo_key, upto=None, highlight=None):
        self.draw_grid()
        if not points:
            return

        style = ALGO_STYLES.get(algo_key, {"color": "#1e88e5", "shape": "rect"})
        color = style["color"]
        shape = style["shape"]

        last = len(points) - 1 if upto is None else upto
        for i in range(min(last + 1, len(points))):
            is_highlight = (highlight is not None and i == highlight)
            self.draw_pixel(points[i][0], points[i][1], color,
                            factor=1.0, shape=shape, highlight=is_highlight)

    # ---------------- вывод информации ----------------
    def show_info(self, p, points):
        lines = [ALGO_NAMES[p["algo"]], ""]
        if p["algo"] == "bresCircle":
            lines.append(f'Центр: ({p["x1"]}; {p["y1"]}), радиус: {p["r"]}')
        else:
            lines.append(f'Отрезок: ({p["x1"]}; {p["y1"]}) → ({p["x2"]}; {p["y2"]})')
        lines.append(f"Количество растровых точек: {len(points)}")
        lines.append(f"Масштаб: {self.scale} px/ед.; начало координат — в центре холста; ось Y направлена вверх.")
        self.info.config(text="\n".join(lines))

    def render_steps(self, points):
        self.tree.delete(*self.tree.get_children())
        self.step_iids = []
        max_rows = 60
        n = min(len(points), max_rows)
        for i in range(n):
            iid = self.tree.insert("", "end", values=(i + 1, points[i][0], points[i][1]))
            self.step_iids.append(iid)
        if len(points) > max_rows:
            self.info.config(text=self.info.cget("text") + f"\n(в таблице показаны первые {max_rows} точек из {len(points)})")

    def highlight_step(self, index):
        for i, iid in enumerate(self.step_iids):
            if i == index:
                self.tree.item(iid, tags=("cur",))
                self.tree.see(iid)
            else:
                self.tree.item(iid, tags=())

    # ---------------- действия ----------------
    def stop_animation(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        self.anim_i = -1

    def draw(self):
        self.stop_animation()
        p = self.read_params()
        self.last_params = p
        self.mode = "draw"
        points = build_points(p["algo"], p)
        self.points = points
        self.render(points, p["algo"])
        self.show_info(p, points)
        self.render_steps(points)

    def animate(self):
        self.stop_animation()
        p = self.read_params()
        self.last_params = p
        self.mode = "draw"
        points = build_points(p["algo"], p)
        self.points = points
        self.show_info(p, points)
        self.render_steps(points)
        if not points:
            return
        self.anim_i = 0
        self._tick(points, p["algo"])

    def _tick(self, points, algo_key):
        i = self.anim_i
        self.render(points, algo_key, i, i)
        self.highlight_step(i)
        i += 1
        self.anim_i = i
        if i < len(points):
            self.timer = self.root.after(80, lambda: self._tick(points, algo_key))
        else:
            self.timer = None
            self.anim_i = -1
            self.render(points, algo_key)
            self.highlight_step(-1)

    def timing(self):
        self.stop_animation()
        p = self.read_params()

        rows = []
        for key, name in ALGOS:
            repeats = 500 if key == "bresCircle" else 2000
            t0 = time.perf_counter()
            sink = 0
            for _ in range(repeats):
                sink += len(build_points(key, p))
            t1 = time.perf_counter()
            total = (t1 - t0) * 1000.0
            rows.append((name, repeats, total / repeats, total))

        lines = ["Замер времени", ""]
        lines.append(f'{"Алгоритм":<24}{"Повторов":>10}{"Среднее, мс":>14}{"Всего, мс":>12}')
        lines.append("-" * 60)
        for name, repeats, avg, total in rows:
            lines.append(f"{name:<24}{repeats:>10}{avg:>14.6f}{total:>12.3f}")
        lines.append("")
        lines.append("Для отрезков используются x1,y1–x2,y2; для окружности — центр x1,y1 и радиус.")
        lines.append("Время зависит от CPU и загрузки системы.")
        self.info.config(text="\n".join(lines))

    # ---------------- сравнение алгоритмов (МЕТОДЫ КЛАССА) ----------------
    def _outline_cell(self, x, y, color, inset):
        ox, oy = W / 2, H / 2
        s = self.scale
        inset = min(inset, max(1, s // 2 - 2))  # защита на малом масштабе
        self.canvas.create_rectangle(
            ox + x * s + inset, oy - (y + 1) * s + inset,
            ox + (x + 1) * s - inset, oy - y * s - inset,
            outline=color, width=2,
        )

    def compare(self):
        self.stop_animation()
        p = self.read_params()
        self.last_params = p
        self.mode = "compare"
        self.points = []
        self.draw_grid()

        keys = ["step", "dda", "bresLine"]
        sets = {k: build_points(k, p) for k in keys}

        # серая подложка — объединение всех пикселей
        for (x, y) in unique_points([pt for k in keys for pt in sets[k]]):
            self.draw_pixel(x, y, "#e0e0e0")

        # концентрические рамки: красная=step, зелёная=dda, синяя=bres
        for i, k in enumerate(keys):
            for (x, y) in sets[k]:
                self._outline_cell(x, y, ALGO_STYLES[k]["color"], 3 + i * 4)

        base = set(sets["bresLine"])
        lines = ["Наложение: пошаговый / DDA / Брезенхем", ""]
        for k in ("step", "dda"):
            s_set = set(sets[k])
            lines.append(
                f'{ALGO_NAMES[k]}: общих с Брезенхемом {len(s_set & base)}, '
                f'только у него {len(s_set - base)}, '
                f'отсутствует у него {len(base - s_set)}')
        lines.append("")
        lines.append("Рамки: красная — пошаговый, зелёная — DDA, синяя — Брезенхем.")
        lines.append("Общий пиксель = вложенные рамки; отличающийся = рамка")
        lines.append("одного цвета на ячейке, где у других рамок нет.")
        self.info.config(text="\n".join(lines))
        self.render_steps(sets["bresLine"])

    def clear_all(self):
        self.stop_animation()
        self.points = []
        self.last_params = None
        self.mode = None
        self.draw_grid()
        self.info.config(text="Очищено. Выберите алгоритм и нажмите «Построить».")
        self.tree.delete(*self.tree.get_children())
        self.step_iids = []

    # ---------------- обработчики ----------------
    def _on_scale(self, _value=None):
        self.read_params()
        if self.mode == "compare" and self.last_params:
            self.compare()
        elif self.points and self.last_params:
            self.render(self.points, self.last_params["algo"])
        else:
            self.draw_grid()

    def _on_grid_toggle(self):
        self.read_params()
        if self.mode == "compare" and self.last_params:
            self.compare()
        elif self.points and self.last_params:
            self.render(self.points, self.last_params["algo"])
        else:
            self.draw_grid()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    RasterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()