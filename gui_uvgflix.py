import queue
import random
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import operacionesGrafo as og
import recomendador as rec
from database import closeDriver, comprobarConexion, session


BG = "#f4f5f2"
SURFACE = "#ffffff"
BORDER = "#d7dbd2"
TEXT = "#1f2933"
MUTED = "#64706a"
ACCENT = "#c83333"
ACCENT_DARK = "#a72828"
DANGER = "#9f3a38"

ESTADOS_ANIMO = ["", "alegre", "relajado", "emocionado", "triste", "nostalgico", "curioso"]
ESTADO_DB = {"nostalgico": "nost\u00e1lgico"}
GENEROS_BASE = [
    "Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Horror", "Mystery", "Romance",
    "Sci-Fi", "Thriller"
]
PLATAFORMAS_BASE = ["Netflix", "Disney+", "Prime Video", "HBO Max", "Apple TV+", "Paramount+"]


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text,
        command,
        *,
        variant="default",
        width=170,
        height=38,
        radius=10,
        background=None,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=background or self._parent_bg(parent),
            cursor="hand2",
        )
        self.text = text
        self.command = command
        self.variant = variant
        self.radius = radius
        self.height_value = height
        self._pressed = False
        self._alive = True
        self._configure_colors()
        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._draw()

    @staticmethod
    def _parent_bg(parent):
        try:
            return parent.cget("background")
        except tk.TclError:
            return BG

    def _configure_colors(self):
        if self.variant == "accent":
            self.fill = ACCENT
            self.hover = ACCENT_DARK
            self.outline = ACCENT
            self.fg = "#ffffff"
        elif self.variant == "danger":
            self.fill = SURFACE
            self.hover = "#fbefef"
            self.outline = "#d8a2a0"
            self.fg = DANGER
        else:
            self.fill = SURFACE
            self.hover = "#f7f8f5"
            self.outline = BORDER
            self.fg = TEXT

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, splinesteps=16, **kwargs)

    def _exists(self):
        try:
            return self._alive and bool(self.winfo_exists())
        except tk.TclError:
            return False

    def destroy(self):
        self._alive = False
        try:
            self.unbind("<Configure>")
            self.unbind("<Enter>")
            self.unbind("<Leave>")
            self.unbind("<ButtonPress-1>")
            self.unbind("<ButtonRelease-1>")
        except tk.TclError:
            pass
        super().destroy()

    def _on_configure(self, _event):
        self._draw()

    def _draw(self, fill=None):
        if not self._exists():
            return
        try:
            self.delete("all")
            w = max(self.winfo_width(), 1)
            h = self.height_value
            self.configure(height=h)
            self._round_rect(1, 1, w - 2, h - 2, self.radius, fill=fill or self.fill, outline=self.outline, width=1)
            self.create_text(w / 2, h / 2, text=self.text, fill=self.fg, font=("Segoe UI Semibold", 10))
        except tk.TclError:
            self._alive = False

    def _on_enter(self, _event):
        self._draw(self.hover)

    def _on_leave(self, _event):
        self._pressed = False
        self._draw(self.fill)

    def _on_press(self, _event):
        self._pressed = True
        self._draw(self.hover)

    def _on_release(self, event):
        if not self._exists():
            return
        try:
            inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        except tk.TclError:
            return
        should_run = self._pressed and inside
        self._pressed = False
        if should_run:
            self.command()
        if self._exists():
            self._draw(self.hover if inside else self.fill)


class UvgflixApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UVGflix - Sistema de Recomendaciones")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg=BG)
        self._tasks = queue.Queue()
        self.current_user_id = None
        self.status_var = tk.StringVar(value="Verificando Neo4j...")
        self.auth_frame = None
        self.main_frame = None

        self._configure_style()
        self._build_auth_layout()
        self._check_connection()
        self.after(100, self._process_tasks)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background=BG, foreground=TEXT)
        style.configure("TFrame", background=BG)
        style.configure("Surface.TFrame", background=SURFACE, relief="solid", borderwidth=1)
        style.configure("Header.TFrame", background="#e9ece7")
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Surface.TLabel", background=SURFACE, foreground=TEXT)
        style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED)
        style.configure("BrandUV.TLabel", background="#e9ece7", foreground=ACCENT, font=("Segoe UI Semibold", 20))
        style.configure("BrandFlix.TLabel", background="#e9ece7", foreground="#111111", font=("Segoe UI Semibold", 20))
        style.configure("BrandUV.Surface.TLabel", background=SURFACE, foreground=ACCENT, font=("Segoe UI Semibold", 20))
        style.configure("BrandFlix.Surface.TLabel", background=SURFACE, foreground="#111111", font=("Segoe UI Semibold", 20))
        style.configure("Title.TLabel", background="#e9ece7", foreground=TEXT, font=("Segoe UI Semibold", 17))
        style.configure("Status.TLabel", background="#e9ece7", foreground=MUTED)
        style.configure("TButton", padding=(12, 7), borderwidth=1)
        style.map("TButton", background=[("active", "#eef1ec")])
        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", borderwidth=0)
        style.map("Accent.TButton", background=[("active", ACCENT_DARK), ("disabled", "#9aa8a4")])
        style.configure("Danger.TButton", foreground=DANGER)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 9), background="#e1e5df", foreground=TEXT)
        style.map("TNotebook.Tab", background=[("selected", SURFACE)])
        style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT, rowheight=28)
        style.configure("Treeview.Heading", background="#e9ece7", foreground=TEXT, font=("Segoe UI Semibold", 10))
        style.map("Treeview", background=[("selected", "#dce8e7")], foreground=[("selected", TEXT)])
        style.configure("TEntry", fieldbackground=SURFACE, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        style.configure("TCombobox", fieldbackground=SURFACE, bordercolor=BORDER)

    def _brand(self, parent, bg_style="Header.TFrame"):
        brand = ttk.Frame(parent, style=bg_style)
        uv_style = "BrandUV.Surface.TLabel" if bg_style == "Surface.TFrame" else "BrandUV.TLabel"
        flix_style = "BrandFlix.Surface.TLabel" if bg_style == "Surface.TFrame" else "BrandFlix.TLabel"
        ttk.Label(brand, text="UV", style=uv_style).pack(side="left")
        ttk.Label(brand, text="flix", style=flix_style).pack(side="left")
        return brand

    def _button(self, parent, text, command, *, variant="default", width=170, background=SURFACE):
        return RoundedButton(
            parent,
            text,
            self._safe_command(command),
            variant=variant,
            width=width,
            background=background,
        )

    def _safe_command(self, command):
        def wrapped():
            try:
                command()
            except Exception as exc:
                messagebox.showerror("UVGflix", str(exc))
                self.status_var.set("Error")
        return wrapped

    def report_callback_exception(self, _exc, value, _tb):
        message = str(value)
        if "invalid command name" in message and "roundedbutton" in message.lower():
            return
        messagebox.showerror("UVGflix", str(value))
        self.status_var.set("Error")

    def _build_auth_layout(self):
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None
        if self.auth_frame:
            self.auth_frame.destroy()

        self.auth_frame = ttk.Frame(self, padding=30)
        self.auth_frame.pack(fill="both", expand=True)
        self.auth_frame.columnconfigure(0, weight=1)
        self.auth_frame.rowconfigure(0, weight=1)

        card = ttk.Frame(self.auth_frame, style="Surface.TFrame", padding=28)
        card.grid(row=0, column=0, sticky="", ipadx=28, ipady=16)

        self._brand(card, "Surface.TFrame").pack(anchor="w", pady=(0, 18))

        ttk.Label(
            card,
            text="Inicio de sesion",
            style="Surface.TLabel",
            font=("Segoe UI Semibold", 22),
        ).pack(anchor="w")
        ttk.Label(
            card,
            text="Ingresa con tu usuario o crea uno nuevo para recibir recomendaciones.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 22))

        self.login_user_id = self._stacked_field(card, "ID de usuario")
        self.login_user_id.bind("<Return>", lambda _event: self.login_user())

        self._button(card, "Log in", self.login_user, variant="accent").pack(fill="x", pady=(8, 8))
        self._button(card, "Ingresar como guest", self.login_guest).pack(fill="x", pady=(0, 8))
        self._button(card, "Registrarse", self._build_register_layout).pack(fill="x")

        ttk.Label(card, textvariable=self.status_var, style="Muted.TLabel").pack(anchor="w", pady=(18, 0))

    def _build_register_layout(self):
        if self.auth_frame:
            self.auth_frame.destroy()

        self.auth_frame = ttk.Frame(self, padding=24)
        self.auth_frame.pack(fill="both", expand=True)
        self.auth_frame.columnconfigure(0, weight=1)
        self.auth_frame.rowconfigure(0, weight=1)

        card = ttk.Frame(self.auth_frame, style="Surface.TFrame", padding=24)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        heading = ttk.Frame(card, style="Surface.TFrame")
        heading.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        self._brand(heading, "Surface.TFrame").pack(side="left")
        self._button(heading, "Volver", self._build_auth_layout, width=112).pack(side="right")

        ttk.Label(
            card,
            text="Cuentanos que te gusta",
            style="Surface.TLabel",
            font=("Segoe UI Semibold", 21),
        ).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Label(
            card,
            text="Estas preferencias crean tu perfil inicial dentro del grafo.",
            style="Muted.TLabel",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 18))

        left = ttk.Frame(card, style="Surface.TFrame", padding=(0, 0, 16, 0))
        right = ttk.Frame(card, style="Surface.TFrame", padding=(16, 0, 0, 0))
        left.grid(row=3, column=0, sticky="nsew")
        right.grid(row=3, column=1, sticky="nsew")

        self.reg_name = self._stacked_field(left, "Nombre")
        self.reg_age = self._stacked_field(left, "Edad")
        self.reg_location = self._stacked_field(left, "Ubicacion")

        ttk.Label(left, text="Plataformas", style="Surface.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(10, 6))
        self.platform_vars = {}
        platform_grid = ttk.Frame(left, style="Surface.TFrame")
        platform_grid.pack(fill="x")
        for i, plataforma in enumerate(PLATAFORMAS_BASE):
            var = tk.BooleanVar(value=i < 2)
            self.platform_vars[plataforma] = var
            ttk.Checkbutton(platform_grid, text=plataforma, variable=var).grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 12), pady=3)

        ttk.Label(right, text="Generos favoritos", style="Surface.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(0, 6))
        self.genre_vars = {}
        genre_grid = ttk.Frame(right, style="Surface.TFrame")
        genre_grid.pack(fill="x")
        for i, genero in enumerate(GENEROS_BASE):
            var = tk.BooleanVar(value=genero in {"Action", "Comedy", "Drama", "Sci-Fi"})
            self.genre_vars[genero] = var
            ttk.Checkbutton(genre_grid, text=genero, variable=var).grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 12), pady=3)

        prefs = ttk.Frame(right, style="Surface.TFrame")
        prefs.pack(fill="x", pady=(12, 0))
        self.reg_mood = self._combo(prefs, "Estado de animo", ESTADOS_ANIMO[1:], 16)
        self.reg_time = self._combo(prefs, "Tiempo usual", ["sin filtro", "menos de 90 min", "90 a 130 min", "mas de 130 min"], 18)

        actions = ttk.Frame(card, style="Surface.TFrame")
        actions.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        self._button(actions, "Crear usuario", self.register_user, variant="accent", width=150).pack(side="right")
        ttk.Label(actions, textvariable=self.status_var, style="Muted.TLabel").pack(side="left")

    def login_user(self):
        user_id = self._int_value(self.login_user_id, "ID de usuario")

        def task():
            perfil = rec.perfilUsuario(user_id)
            if not perfil:
                raise ValueError(f"El usuario {user_id} no existe.")
            return user_id

        self._run_async("Iniciando sesion...", task, self._enter_app)

    def login_guest(self):
        def task():
            usuarios = og.listarUsuarios(limite=1)
            if not usuarios:
                raise ValueError("No hay usuarios cargados. Ejecuta loadMovieLens.py primero.")
            return usuarios[0]["userId"]

        self._run_async("Ingresando como guest...", task, self._enter_app)

    def register_user(self):
        nombre = self.reg_name.get().strip()
        edad = self._int_value(self.reg_age, "Edad", None)
        ubicacion = self.reg_location.get().strip() or None
        plataformas = [name for name, var in self.platform_vars.items() if var.get()]
        generos = [name for name, var in self.genre_vars.items() if var.get()]
        tiempo = self.reg_time.get()
        animo = ESTADO_DB.get(self.reg_mood.get(), self.reg_mood.get())

        if not nombre:
            messagebox.showwarning("UVGflix", "Ingrese su nombre.")
            return
        if not generos:
            messagebox.showwarning("UVGflix", "Seleccione al menos un genero.")
            return

        def task():
            user_id = self._next_user_id()
            og.agregarUsuario(user_id, nombre, edad, ubicacion)
            for plataforma in plataformas:
                og.vincularPlataforma(user_id, plataforma)

            peliculas = self._movies_for_preferences(generos, tiempo, animo, limite=18)
            for movie_id in peliculas:
                og.agregarCalificacion(user_id, movie_id, 5.0)
            return user_id, len(peliculas)

        def done(result):
            user_id, seeded = result
            messagebox.showinfo(
                "UVGflix",
                f"Usuario creado con ID {user_id}. Se guardaron {seeded} gustos iniciales.",
            )
            self._enter_app(user_id)

        self._run_async("Creando usuario...", task, done)

    def _next_user_id(self):
        with session() as s:
            record = s.run("MATCH (u:Usuario) RETURN coalesce(max(u.userId), 0) + 1 AS nextId").single()
            return int(record["nextId"])

    def _movies_for_preferences(self, generos, tiempo, animo=None, limite=18):
        max_minutes = None
        min_minutes = None
        if tiempo == "menos de 90 min":
            max_minutes = 90
        elif tiempo == "90 a 130 min":
            min_minutes = 90
            max_minutes = 130
        elif tiempo == "mas de 130 min":
            min_minutes = 130

        query = """
            MATCH (c:Contenido)-[:ES_DE_GENERO]->(g:Genero)
            WHERE g.nombre IN $generos
              AND ($minMinutes IS NULL OR c.duracion >= $minMinutes)
              AND ($maxMinutes IS NULL OR c.duracion <= $maxMinutes)
            OPTIONAL MATCH (g)-[:COMPATIBLE_CON]->(e:EstadoAnimo {nombre: $animo})
            WITH c, count(DISTINCT g) AS matches, count(DISTINCT e) AS moodMatches
            ORDER BY moodMatches DESC, matches DESC, rand()
            RETURN c.movieId AS movieId
            LIMIT $limite
        """
        with session() as s:
            return [
                int(r["movieId"])
                for r in s.run(
                    query,
                    generos=generos,
                    animo=animo,
                    minMinutes=min_minutes,
                    maxMinutes=max_minutes,
                    limite=limite,
                )
            ]

    def _enter_app(self, user_id):
        self.current_user_id = user_id
        self._build_layout()
        self._set_entry(self.rec_user, user_id)
        self._set_entry(self.rate_user, user_id)
        self._set_entry(self.friend_a, user_id)
        self._set_entry(self.platform_user, user_id)
        self.load_users()
        self.load_stats()

    def _back_to_start(self):
        self.current_user_id = None
        self.status_var.set("Neo4j conectado")
        self._build_auth_layout()

    def _build_layout(self):
        if self.auth_frame:
            self.auth_frame.destroy()
            self.auth_frame = None

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        header = ttk.Frame(self.main_frame, style="Header.TFrame", padding=(18, 14))
        header.pack(fill="x")
        self._brand(header).pack(side="left")
        ttk.Label(
            header,
            text="Sistema de recomendaciones",
            style="Status.TLabel",
            padding=(14, 4),
        ).pack(side="left")
        self._button(header, "Volver", self._back_to_start, width=104, background="#e9ece7").pack(side="right", padx=(12, 0))
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").pack(side="right")

        main = ttk.Frame(self.main_frame, padding=16)
        main.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)

        self._build_recommendations_tab()
        self._build_users_tab()
        self._build_content_tab()
        self._build_graph_tab()
        self._build_stats_tab()

    def _surface(self, parent, padding=14):
        frame = ttk.Frame(parent, style="Surface.TFrame", padding=padding)
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        return frame

    def _field(self, parent, label, width=18):
        frame = ttk.Frame(parent, style="Surface.TFrame")
        frame.pack(side="left", padx=(0, 10), pady=(0, 8))
        ttk.Label(frame, text=label, style="Surface.TLabel").pack(anchor="w")
        entry = ttk.Entry(frame, width=width)
        entry.pack(anchor="w")
        return entry

    def _combo(self, parent, label, values, width=18):
        frame = ttk.Frame(parent, style="Surface.TFrame")
        frame.pack(side="left", padx=(0, 10), pady=(0, 8))
        ttk.Label(frame, text=label, style="Surface.TLabel").pack(anchor="w")
        combo = ttk.Combobox(frame, values=values, width=width, state="readonly")
        combo.current(0)
        combo.pack(anchor="w")
        return combo

    def _build_recommendations_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Recomendaciones")
        surface = self._surface(tab)

        controls = ttk.Frame(surface, style="Surface.TFrame")
        controls.pack(fill="x")
        self.rec_user = self._field(controls, "ID usuario", 12)
        self.rec_n = self._field(controls, "Cantidad", 10)
        self.rec_n.insert(0, "5")
        self.rec_time = self._field(controls, "Minutos max.", 12)
        self.rec_mood = self._combo(controls, "Estado de animo", ESTADOS_ANIMO, 16)
        self._button(controls, "Recomendar", self.load_recommendations, variant="accent", width=138).pack(
            side="left", padx=(4, 0), pady=(17, 8)
        )

        self.profile_var = tk.StringVar(value="Seleccione un usuario para ver su perfil.")
        ttk.Label(surface, textvariable=self.profile_var, style="Muted.TLabel").pack(anchor="w", pady=(6, 12))

        panes = ttk.PanedWindow(surface, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes, style="Surface.TFrame", padding=(0, 0, 8, 0))
        right = ttk.Frame(panes, style="Surface.TFrame", padding=(8, 0, 0, 0))
        panes.add(left, weight=3)
        panes.add(right, weight=2)

        self.rec_tree = self._tree(left, ("movieId", "titulo", "puntaje", "razones"), {
            "movieId": (80, "ID"),
            "titulo": (320, "Titulo"),
            "puntaje": (90, "Puntaje"),
            "razones": (360, "Razones"),
        })
        self.friends_tree = self._tree(right, ("movieId", "titulo", "puntaje", "razones"), {
            "movieId": (75, "ID"),
            "titulo": (260, "Social"),
            "puntaje": (80, "Puntaje"),
            "razones": (260, "Razones"),
        })

    def _build_users_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Usuarios")
        surface = self._surface(tab)

        top = ttk.Frame(surface, style="Surface.TFrame")
        top.pack(fill="x")
        self._button(top, "Actualizar usuarios", self.load_users, variant="accent", width=164).pack(
            side="left", pady=(0, 10)
        )
        self._button(top, "Agregar usuario", self.new_user_form, width=146).pack(side="left", padx=8, pady=(0, 10))
        self._button(top, "Ver historial", self.load_selected_history, width=126).pack(side="left", padx=0, pady=(0, 10))

        split = ttk.PanedWindow(surface, orient="horizontal")
        split.pack(fill="both", expand=True)

        users_panel = ttk.Frame(split, style="Surface.TFrame", padding=(0, 0, 8, 0))
        edit_panel = ttk.Frame(split, style="Surface.TFrame", padding=(8, 0, 0, 0))
        split.add(users_panel, weight=3)
        split.add(edit_panel, weight=2)

        self.users_tree = self._tree(users_panel, ("userId", "nombre", "edad", "contenidos"), {
            "userId": (80, "ID"),
            "nombre": (260, "Nombre"),
            "edad": (70, "Edad"),
            "contenidos": (130, "Vistos"),
        })
        self.users_tree.bind("<<TreeviewSelect>>", self._fill_user_from_selection)

        ttk.Label(edit_panel, text="Gestion de usuario", style="Surface.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        form = ttk.Frame(edit_panel, style="Surface.TFrame")
        form.pack(fill="x", pady=(10, 4))
        self.user_id = self._stacked_field(form, "ID")
        self.user_name = self._stacked_field(form, "Nombre")
        self.user_age = self._stacked_field(form, "Edad")
        self.user_location = self._stacked_field(form, "Ubicacion")
        self._button(edit_panel, "Guardar usuario", self.save_user, variant="accent").pack(fill="x", pady=(8, 4))
        self._button(edit_panel, "Eliminar usuario", self.delete_user, variant="danger").pack(fill="x", pady=4)

        ttk.Separator(edit_panel).pack(fill="x", pady=14)
        ttk.Label(edit_panel, text="Historial", style="Surface.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.history_tree = self._tree(edit_panel, ("movieId", "titulo", "calificacion"), {
            "movieId": (80, "ID"),
            "titulo": (280, "Titulo"),
            "calificacion": (90, "Rating"),
        }, height=9)

    def _build_content_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Contenido")
        surface = self._surface(tab)

        search = ttk.Frame(surface, style="Surface.TFrame")
        search.pack(fill="x")
        self.search_text = self._field(search, "Buscar titulo", 38)
        self._button(search, "Buscar", self.search_content, variant="accent", width=110).pack(
            side="left", pady=(17, 8)
        )

        split = ttk.PanedWindow(surface, orient="horizontal")
        split.pack(fill="both", expand=True, pady=(8, 0))
        results_panel = ttk.Frame(split, style="Surface.TFrame", padding=(0, 0, 8, 0))
        rate_panel = ttk.Frame(split, style="Surface.TFrame", padding=(8, 0, 0, 0))
        split.add(results_panel, weight=4)
        split.add(rate_panel, weight=2)

        self.content_tree = self._tree(results_panel, ("movieId", "titulo", "year", "duracion", "generos"), {
            "movieId": (80, "ID"),
            "titulo": (330, "Titulo"),
            "year": (70, "Anio"),
            "duracion": (90, "Min."),
            "generos": (260, "Generos"),
        })
        self.content_tree.bind("<<TreeviewSelect>>", self._fill_movie_from_selection)

        ttk.Label(rate_panel, text="Calificar contenido", style="Surface.TLabel", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        form = ttk.Frame(rate_panel, style="Surface.TFrame")
        form.pack(fill="x", pady=(10, 4))
        self.rate_user = self._stacked_field(form, "ID usuario")
        self.rate_movie = self._stacked_field(form, "ID contenido")
        self.rate_value = self._stacked_field(form, "Calificacion 0-5")
        self._button(rate_panel, "Guardar calificacion", self.save_rating, variant="accent").pack(fill="x", pady=(8, 4))

    def _build_graph_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Relaciones")
        surface = self._surface(tab)

        left = ttk.Frame(surface, style="Surface.TFrame", padding=(0, 0, 12, 0))
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(surface, style="Surface.TFrame", padding=(12, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(left, text="Crear amistad", style="Surface.TLabel", font=("Segoe UI Semibold", 12)).pack(anchor="w")
        self.friend_a = self._stacked_field(left, "ID usuario 1")
        self.friend_b = self._stacked_field(left, "ID usuario 2")
        self._button(left, "Guardar amistad", self.save_friendship, variant="accent").pack(fill="x", pady=(8, 18))

        ttk.Label(right, text="Vincular plataforma", style="Surface.TLabel", font=("Segoe UI Semibold", 12)).pack(anchor="w")
        self.platform_user = self._stacked_field(right, "ID usuario")
        self.platform_name = self._stacked_field(right, "Plataforma")
        self._button(right, "Vincular", self.save_platform, variant="accent").pack(fill="x", pady=(8, 18))

    def _build_stats_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Estadisticas")
        surface = self._surface(tab)

        self._button(surface, "Actualizar estadisticas", self.load_stats, variant="accent", width=190).pack(anchor="w", pady=(0, 12))
        self.stats_tree = self._tree(surface, ("metrica", "valor"), {
            "metrica": (260, "Metrica"),
            "valor": (160, "Valor"),
        }, height=14)

    def _stacked_field(self, parent, label):
        frame = ttk.Frame(parent, style="Surface.TFrame")
        frame.pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text=label, style="Surface.TLabel").pack(anchor="w")
        entry = ttk.Entry(frame)
        entry.pack(fill="x")
        return entry

    def _tree(self, parent, columns, specs, height=16):
        frame = ttk.Frame(parent, style="Surface.TFrame")
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        for col in columns:
            width, heading = specs[col]
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="w", stretch=True)

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        return tree

    def _run_async(self, label, func, on_success=None):
        self.status_var.set(label)

        def worker():
            try:
                result = func()
                self._tasks.put(("success", label, result, on_success))
            except Exception as exc:
                self._tasks.put(("error", label, exc, None))

        threading.Thread(target=worker, daemon=True).start()

    def _process_tasks(self):
        try:
            while True:
                kind, label, payload, callback = self._tasks.get_nowait()
                if kind == "success":
                    self.status_var.set("Listo")
                    if callback:
                        try:
                            callback(payload)
                        except Exception as exc:
                            self.status_var.set("Error")
                            messagebox.showerror("UVGflix", str(exc))
                else:
                    self.status_var.set("Error")
                    messagebox.showerror("UVGflix", str(payload))
        except queue.Empty:
            pass
        self.after(100, self._process_tasks)

    def _check_connection(self):
        self._run_async(
            "Verificando Neo4j...",
            comprobarConexion,
            lambda ok: self.status_var.set("Neo4j conectado" if ok else "Neo4j no disponible"),
        )

    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def _insert_rows(self, tree, rows):
        self._clear_tree(tree)
        for row in rows:
            tree.insert("", "end", values=row)

    def _int_value(self, entry, name, default=None):
        raw = entry.get().strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(f"{name} debe ser un numero entero.") from exc

    def _float_value(self, entry, name, default=None):
        raw = entry.get().strip()
        if not raw:
            return default
        try:
            return float(raw)
        except ValueError as exc:
            raise ValueError(f"{name} debe ser un numero.") from exc

    def load_recommendations(self):
        user_id = self._int_value(self.rec_user, "ID usuario")
        n = self._int_value(self.rec_n, "Cantidad", 5)
        tiempo = self._int_value(self.rec_time, "Minutos maximos", None)
        animo = self.rec_mood.get() or None
        animo = ESTADO_DB.get(animo, animo)

        def task():
            perfil = rec.perfilUsuario(user_id)
            if not perfil:
                raise ValueError(f"El usuario {user_id} no existe.")
            recomendaciones = rec.recomendar(user_id, n=n, tiempoDisponible=tiempo, estadoAnimo=animo)
            sociales = rec.recomendarAmigos(user_id, n=n)
            return perfil, recomendaciones, sociales

        self._run_async("Calculando recomendaciones...", task, self._show_recommendations)

    def _show_recommendations(self, data):
        perfil, recomendaciones, sociales = data
        plataformas = ", ".join(perfil.get("plataformas") or []) or "sin plataformas"
        generos = ", ".join(perfil.get("generosFavoritos") or []) or "sin generos"
        self.profile_var.set(
            f"{perfil.get('nombre') or 'Usuario'} | edad {perfil.get('edad') or '?'} | "
            f"{perfil.get('ubicacion') or 'sin ubicacion'} | {plataformas} | favoritos: {generos}"
        )
        self._insert_rows(self.rec_tree, [
            (r["movieId"], r["titulo"], f"{r['puntaje']:.2f}", "; ".join(r["razones"]))
            for r in recomendaciones
        ])
        self._insert_rows(self.friends_tree, [
            (r["movieId"], r["titulo"], f"{r['puntaje']:.2f}", "; ".join(r["razones"]))
            for r in sociales
        ])

    def load_users(self):
        self._run_async("Cargando usuarios...", lambda: og.listarUsuarios(limite=100), self._show_users)

    def _show_users(self, users):
        self._insert_rows(self.users_tree, [
            (u["userId"], u.get("nombre") or "", u.get("edad") or "", u["contenidosVistos"])
            for u in users
        ])

    def new_user_form(self):
        def done(next_id):
            self._set_entry(self.user_id, next_id)
            self._set_entry(self.user_name, "")
            self._set_entry(self.user_age, "")
            self._set_entry(self.user_location, "")
            self.status_var.set("Nuevo usuario listo para guardar")

        self._run_async("Preparando usuario nuevo...", self._next_user_id, done)

    def _fill_user_from_selection(self, _event=None):
        selected = self.users_tree.selection()
        if not selected:
            return
        values = self.users_tree.item(selected[0], "values")
        self._set_entry(self.user_id, values[0])
        self._set_entry(self.user_name, values[1])
        self._set_entry(self.user_age, values[2])
        self._set_entry(self.rec_user, values[0])
        self._set_entry(self.rate_user, values[0])
        self._set_entry(self.friend_a, values[0])
        self._set_entry(self.platform_user, values[0])

    def save_user(self):
        user_id = self._int_value(self.user_id, "ID")
        nombre = self.user_name.get().strip()
        edad = self._int_value(self.user_age, "Edad", None)
        ubicacion = self.user_location.get().strip() or None
        if not nombre:
            messagebox.showwarning("UVGflix", "Ingrese el nombre del usuario.")
            return
        self._run_async(
            "Guardando usuario...",
            lambda: og.agregarUsuario(user_id, nombre, edad, ubicacion),
            lambda _ok: (messagebox.showinfo("UVGflix", "Usuario guardado."), self.load_users()),
        )

    def delete_user(self):
        user_id = self._int_value(self.user_id, "ID")
        if not messagebox.askyesno("UVGflix", f"Eliminar usuario {user_id}?"):
            return
        self._run_async(
            "Eliminando usuario...",
            lambda: og.eliminarUsuario(user_id),
            lambda nombre: (messagebox.showinfo("UVGflix", f"Usuario eliminado: {nombre or 'no existia'}"), self.load_users()),
        )

    def load_selected_history(self):
        raw = self.user_id.get().strip() or self.rec_user.get().strip()
        if not raw:
            messagebox.showwarning("UVGflix", "Seleccione o ingrese un usuario.")
            return
        user_id = int(raw)
        self._run_async("Cargando historial...", lambda: og.historialUsuario(user_id, limite=50), self._show_history)

    def _show_history(self, items):
        self._insert_rows(self.history_tree, [
            (h["movieId"], h["titulo"], f"{h['calificacion']:.1f}")
            for h in items
        ])

    def search_content(self):
        text = self.search_text.get().strip()
        if not text:
            messagebox.showwarning("UVGflix", "Ingrese texto para buscar.")
            return
        self._run_async("Buscando contenido...", lambda: og.buscarContenido(text, limite=100), self._show_content)

    def _show_content(self, rows):
        self._insert_rows(self.content_tree, [
            (
                r["movieId"],
                r["titulo"],
                r.get("year") or "",
                r.get("duracion") or "",
                ", ".join(r.get("generos") or []),
            )
            for r in rows
        ])

    def _fill_movie_from_selection(self, _event=None):
        selected = self.content_tree.selection()
        if selected:
            values = self.content_tree.item(selected[0], "values")
            self._set_entry(self.rate_movie, values[0])

    def save_rating(self):
        user_id = self._int_value(self.rate_user, "ID usuario")
        movie_id = self._int_value(self.rate_movie, "ID contenido")
        rating = self._float_value(self.rate_value, "Calificacion")
        if rating is None:
            messagebox.showwarning("UVGflix", "Ingrese una calificacion.")
            return

        def task():
            title = og.agregarCalificacion(user_id, movie_id, rating)
            if not title:
                raise ValueError("No se encontro el usuario o el contenido.")
            return title

        self._run_async(
            "Guardando calificacion...",
            task,
            lambda title: messagebox.showinfo("UVGflix", f"Calificacion guardada para {title}."),
        )

    def save_friendship(self):
        u1 = self._int_value(self.friend_a, "ID usuario 1")
        u2 = self._int_value(self.friend_b, "ID usuario 2")
        self._run_async(
            "Creando amistad...",
            lambda: og.agregarAmistad(u1, u2),
            lambda _ok: messagebox.showinfo("UVGflix", "Amistad guardada."),
        )

    def save_platform(self):
        user_id = self._int_value(self.platform_user, "ID usuario")
        plataforma = self.platform_name.get().strip()
        if not plataforma:
            messagebox.showwarning("UVGflix", "Ingrese una plataforma.")
            return
        self._run_async(
            "Vinculando plataforma...",
            lambda: og.vincularPlataforma(user_id, plataforma),
            lambda _ok: messagebox.showinfo("UVGflix", "Plataforma vinculada."),
        )

    def load_stats(self):
        self._run_async("Cargando estadisticas...", og.estadisticas, self._show_stats)

    def _show_stats(self, stats):
        self._insert_rows(self.stats_tree, [(key, value) for key, value in stats.items()])

    def _set_entry(self, entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def _on_close(self):
        closeDriver()
        self.destroy()


if __name__ == "__main__":
    app = UvgflixApp()
    app.mainloop()
