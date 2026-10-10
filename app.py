import glob
import os
import shutil
import sqlite3
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
from urllib.parse import quote_plus

import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

TAMANHO_FOTO_DETALHE = (234, 150)

PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PASTA_BASE, "instrumentos.db")
BACKUP_DIR = os.path.join(PASTA_BASE, "backups")
MAX_BACKUPS = 20
ICONE_PATH = os.path.join(PASTA_BASE, "assets_icone", "icone_app_instrumentos", "icone.ico")
ICONE_PNG_PATH = os.path.join(PASTA_BASE, "assets_icone", "icone_app_instrumentos", "icone_1024.png")

TIPOS = [
    "Amplificador", "Baixo", "Banjo", "Bateria", "Cabo", "Caixa de Som",
    "Cavaquinho", "Cello", "Controlador MIDI", "Drum Machine", "Flauta",
    "Guitarra", "Mesa de Som", "Microfone", "Monitor", "Pedal", "Percussão",
    "Saxofone", "Sintetizador", "Teclado/Piano", "Trompete", "Ukulele",
    "Viola", "Violão", "Violino", "Outro",
]

COLUNAS = [
    ("tipo", "Tipo", 160),
    ("marca", "Marca", 140),
    ("modelo", "Modelo", 140),
    ("numero_serie", "Nº de série", 140),
]

FONTE = "Aktiv Grotesk"

# paleta extraída de maquete_tela_principal.html
COR_FUNDO = "#14171c"
COR_PAINEL = "#1c2027"
COR_BORDA = "#2c323c"
COR_BORDA_SUAVE = "#22272f"
COR_TEXTO = "#ece6d8"
COR_TEXTO_FRACO = "#8b919b"
COR_TEXTO_FRACO2 = "#6c727c"
COR_OURO = "#d4a24c"
COR_OURO_HOVER = "#c6953f"
COR_OURO_TEXTO = "#1a1408"
COR_GHOST = "#232831"
COR_GHOST_HOVER = "#2b313c"
COR_PERIGO_TEXTO = "#e07a6a"
COR_PERIGO_BORDA = "#4a2e2b"
COR_PERIGO_HOVER = "#2a1f1d"
COR_SELECIONADO = "#262b34"
COR_MONO = "#b8b2a5"


def fazer_backup(motivo="auto"):
    """Copia o banco atual para a pasta backups/ antes de operações sensíveis ou ao abrir o app."""
    if not os.path.isfile(DB_PATH):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(BACKUP_DIR, f"instrumentos_{carimbo}_{motivo}.db")
    shutil.copy2(DB_PATH, destino)
    _limpar_backups_antigos()


def _limpar_backups_antigos():
    arquivos = sorted(glob.glob(os.path.join(BACKUP_DIR, "instrumentos_*.db")))
    excesso = len(arquivos) - MAX_BACKUPS
    for antigo in arquivos[:max(excesso, 0)]:
        os.remove(antigo)


def conectar():
    fazer_backup(motivo="abertura")
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS instrumentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            marca TEXT,
            modelo TEXT,
            numero_serie TEXT,
            foto_path TEXT,
            observacoes TEXT
        )
    """)
    con.commit()
    return con


class InstrumentoDialog(tk.Toplevel):
    """Janela de cadastro/edição de um instrumento."""

    def __init__(self, master, dados=None):
        super().__init__(master)
        self.resultado = None
        self.dados_originais = dados
        self.title("Editar instrumento" if dados else "Novo instrumento")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.campos = {}
        self._montar_formulario()

        if dados:
            self._preencher(dados)

        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _montar_formulario(self):
        frame = ttk.Frame(self, padding=15)
        frame.grid(row=0, column=0, sticky="nsew")

        linha = 0

        def add_entry(label, chave, largura=35):
            nonlocal linha
            ttk.Label(frame, text=label).grid(row=linha, column=0, sticky="w", pady=4)
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=largura)
            entry.grid(row=linha, column=1, sticky="w", pady=4, padx=(10, 0))
            self.campos[chave] = var
            linha += 1
            return entry

        ttk.Label(frame, text="Tipo*").grid(row=linha, column=0, sticky="w", pady=4)
        var_tipo = tk.StringVar()
        combo_tipo = ttk.Combobox(frame, textvariable=var_tipo, values=TIPOS, width=32)
        combo_tipo.grid(row=linha, column=1, sticky="w", pady=4, padx=(10, 0))
        combo_tipo.bind("<KeyRelease>", self._filtrar_tipos)
        combo_tipo.bind("<<ComboboxSelected>>", lambda e: combo_tipo.configure(values=TIPOS))
        self.campos["tipo"] = var_tipo
        self._combo_tipo = combo_tipo
        linha += 1

        add_entry("Marca", "marca")
        add_entry("Modelo", "modelo")
        add_entry("Número de série", "numero_serie")

        ttk.Button(frame, text="Buscar no Google", command=self._buscar_no_google).grid(
            row=linha, column=1, sticky="w", pady=(0, 8), padx=(10, 0)
        )
        linha += 1

        ttk.Label(frame, text="Foto (arquivo)").grid(row=linha, column=0, sticky="w", pady=4)
        foto_frame = ttk.Frame(frame)
        foto_frame.grid(row=linha, column=1, sticky="w", pady=4, padx=(10, 0))
        var_foto = tk.StringVar()
        ttk.Entry(foto_frame, textvariable=var_foto, width=26).pack(side="left")
        ttk.Button(foto_frame, text="Escolher...", command=lambda: self._escolher_foto(var_foto)).pack(side="left", padx=(5, 0))
        self.campos["foto_path"] = var_foto
        linha += 1

        ttk.Label(frame, text="Observações").grid(row=linha, column=0, sticky="nw", pady=4)
        texto_obs = tk.Text(frame, width=35, height=4)
        texto_obs.grid(row=linha, column=1, sticky="w", pady=4, padx=(10, 0))
        self.campo_observacoes = texto_obs
        linha += 1

        botoes = ttk.Frame(frame)
        botoes.grid(row=linha, column=0, columnspan=2, pady=(15, 0), sticky="e")
        ttk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="right", padx=(5, 0))
        ttk.Button(botoes, text="Salvar", command=self._salvar).pack(side="right")

        self._combo_tipo.focus_set()

    def _filtrar_tipos(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "ISO_Left_Tab"):
            return
        texto = self.campos["tipo"].get().strip().lower()
        if not texto:
            valores = TIPOS
        else:
            valores = [t for t in TIPOS if t.lower().startswith(texto)]
            if not valores:
                valores = [t for t in TIPOS if texto in t.lower()]
        self._combo_tipo["values"] = valores
        try:
            if valores:
                self._combo_tipo.tk.call("ttk::combobox::Post", self._combo_tipo)
            else:
                self._combo_tipo.tk.call("ttk::combobox::Unpost", self._combo_tipo)
        except tk.TclError:
            pass
        self._combo_tipo.focus_set()
        self._combo_tipo.icursor(tk.END)

    def _buscar_no_google(self):
        partes = [
            self.campos["marca"].get().strip(),
            self.campos["modelo"].get().strip(),
            self.campos["tipo"].get().strip(),
        ]
        termo = " ".join(p for p in partes if p)
        if not termo:
            messagebox.showinfo(
                "Preencha os dados primeiro",
                "Informe ao menos a marca ou o modelo para buscar.",
                parent=self,
            )
            return
        url = f"https://www.google.com/search?q={quote_plus(termo + ' especificações')}"
        webbrowser.open(url)

    def _escolher_foto(self, var_foto):
        caminho = filedialog.askopenfilename(
            title="Escolher foto do instrumento",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.heic *.heif *.ico"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if caminho:
            var_foto.set(caminho)

    def _preencher(self, dados):
        for chave, var in self.campos.items():
            var.set(dados.get(chave) or "")
        self.campo_observacoes.insert("1.0", dados.get("observacoes") or "")

    def _salvar(self):
        tipo = self.campos["tipo"].get().strip()
        if not tipo:
            messagebox.showwarning("Campo obrigatório", "Informe o tipo do item.", parent=self)
            self._combo_tipo.focus_set()
            return

        self.resultado = {
            "tipo": tipo,
            "marca": self.campos["marca"].get().strip(),
            "modelo": self.campos["modelo"].get().strip(),
            "numero_serie": self.campos["numero_serie"].get().strip(),
            "foto_path": self.campos["foto_path"].get().strip(),
            "observacoes": self.campo_observacoes.get("1.0", "end").strip(),
        }
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("my chaotic room")
        self.configure(fg_color=COR_FUNDO)
        self.geometry("1000x640")
        self.minsize(860, 480)
        self._aplicar_icone()

        self.con = conectar()
        self.coluna_ordenacao = "tipo"
        self.ordem_crescente = True
        imagem_vazia = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        self._imagem_vazia = ctk.CTkImage(light_image=imagem_vazia, dark_image=imagem_vazia, size=(1, 1))
        self._foto_detalhe_img = self._imagem_vazia
        self._foto_detalhe_caminho = None

        self._montar_interface()
        self._carregar_lista()

    def _aplicar_icone(self):
        if os.path.isfile(ICONE_PATH):
            try:
                self.iconbitmap(ICONE_PATH)
            except tk.TclError:
                pass

    def _montar_interface(self):
        self._configurar_estilo_treeview()

        # ---- cabeçalho ----
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=28, pady=(22, 18))

        if os.path.isfile(ICONE_PNG_PATH):
            img = Image.open(ICONE_PNG_PATH)
            icone_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(30, 30))
            ctk.CTkLabel(cabecalho, text="", image=icone_ctk).pack(side="left", padx=(0, 14))

        textos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        textos.pack(side="left")
        ctk.CTkLabel(
            textos, text="my chaotic room", text_color=COR_TEXTO,
            font=(FONTE, 20, "bold"), anchor="w",
        ).pack(anchor="w")
        self.label_subtitulo = ctk.CTkLabel(
            textos, text="", text_color=COR_TEXTO_FRACO,
            font=(FONTE, 13), anchor="w",
        )
        self.label_subtitulo.pack(anchor="w")

        ctk.CTkButton(
            cabecalho, text="＋ Novo instrumento", command=self._novo,
            fg_color=COR_OURO, hover_color=COR_OURO_HOVER, text_color=COR_OURO_TEXTO,
            font=(FONTE, 14, "bold"), corner_radius=10, height=38,
        ).pack(side="right")

        busca_caixa = ctk.CTkFrame(
            cabecalho, fg_color=COR_PAINEL, border_color=COR_BORDA, border_width=1,
            corner_radius=10, height=38, width=280,
        )
        busca_caixa.pack(side="right", padx=(0, 12))
        busca_caixa.pack_propagate(False)
        ctk.CTkLabel(
            busca_caixa, text="🔍", text_color=COR_TEXTO_FRACO2, font=(FONTE, 13),
        ).pack(side="left", padx=(12, 4))
        self.entrada_busca = ctk.CTkEntry(
            busca_caixa,
            placeholder_text="Buscar por tipo, marca, modelo…",
            fg_color="transparent", border_width=0,
            text_color=COR_TEXTO, placeholder_text_color=COR_TEXTO_FRACO2,
            font=(FONTE, 13),
        )
        self.entrada_busca.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.entrada_busca.bind("<KeyRelease>", lambda e: self._carregar_lista())

        # ---- corpo: tabela + painel de detalhes ----
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=28, pady=(0, 22))

        painel_tabela = ctk.CTkFrame(corpo, fg_color=COR_PAINEL, corner_radius=14)
        painel_tabela.pack(side="left", fill="both", expand=True, padx=(0, 18))

        lista_frame = ctk.CTkFrame(painel_tabela, fg_color=COR_PAINEL)
        lista_frame.pack(fill="both", expand=True, padx=1, pady=(1, 0))

        colunas = [c[0] for c in COLUNAS]
        self.tree = ttk.Treeview(
            lista_frame, columns=colunas, show="headings",
            selectmode="extended", style="Instrumentos.Treeview",
        )
        for chave, titulo, largura in COLUNAS:
            self.tree.heading(chave, text=titulo, command=lambda c=chave: self._ordenar_por(c))
            self.tree.column(chave, width=largura, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._editar())
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._atualizar_detalhes())
        self.tree.bind("<Button-1>", self._clique_na_lista)

        self.scroll = ttk.Scrollbar(
            lista_frame, orient="vertical", command=self.tree.yview,
            style="Instrumentos.Vertical.TScrollbar",
        )
        # a barra só é exibida (pack) quando o conteúdo realmente não cabe na área visível
        self.tree.configure(yscrollcommand=self._atualizar_barra_rolagem)
        lista_frame.bind("<Configure>", lambda e: self._reavaliar_barra_rolagem())

        self._atualizar_cabecalhos()

        linha_rodape = ctk.CTkFrame(painel_tabela, fg_color=COR_BORDA_SUAVE, height=1)
        linha_rodape.pack(fill="x", side="top")
        self.label_total = ctk.CTkLabel(
            painel_tabela, text="", text_color=COR_TEXTO_FRACO2,
            font=(FONTE, 12), anchor="w",
        )
        self.label_total.pack(fill="x", padx=18, pady=12, anchor="w")

        # ---- painel de detalhes ----
        painel_detalhe = ctk.CTkFrame(corpo, fg_color=COR_PAINEL, corner_radius=14, width=270)
        painel_detalhe.pack(side="left", fill="y")
        painel_detalhe.pack_propagate(False)

        conteudo_detalhe = ctk.CTkFrame(painel_detalhe, fg_color="transparent")
        conteudo_detalhe.pack(fill="both", expand=True, padx=18, pady=18)

        # bloco inteiro (foto + textos) só aparece com exatamente 1 item selecionado
        self.bloco_detalhe = ctk.CTkFrame(conteudo_detalhe, fg_color="transparent")

        self.foto_detalhe_frame = ctk.CTkFrame(
            self.bloco_detalhe, fg_color=COR_GHOST, corner_radius=10, height=150,
        )
        self.foto_detalhe_frame.pack(fill="x")
        self.foto_detalhe_frame.pack_propagate(False)
        self.label_foto_detalhe = ctk.CTkLabel(self.foto_detalhe_frame, text="", image=self._imagem_vazia)
        self.label_foto_detalhe.pack(expand=True)
        self.label_foto_detalhe.bind("<Button-1>", self._abrir_foto_detalhe)

        self.label_tipo_detalhe = ctk.CTkLabel(
            self.bloco_detalhe, text="", text_color=COR_OURO,
            font=(FONTE, 12, "bold"), anchor="w",
        )
        self.label_tipo_detalhe.pack(fill="x", pady=(14, 0))
        self.label_nome_detalhe = ctk.CTkLabel(
            self.bloco_detalhe, text="", text_color=COR_TEXTO,
            font=(FONTE, 18, "bold"), anchor="w", justify="left", wraplength=230,
        )
        self.label_nome_detalhe.pack(fill="x")

        grade = ctk.CTkFrame(self.bloco_detalhe, fg_color="transparent")
        grade.pack(fill="x", pady=(14, 0))
        grade.columnconfigure(1, weight=1)
        self._labels_detalhe = {}
        for i, (rotulo, chave) in enumerate([("Marca", "marca"), ("Modelo", "modelo"), ("Nº de série", "numero_serie")]):
            ctk.CTkLabel(
                grade, text=rotulo, text_color=COR_TEXTO_FRACO,
                font=(FONTE, 13), anchor="w",
            ).grid(row=i, column=0, sticky="w", pady=3)
            fonte_valor = ("Consolas", 13) if chave == "numero_serie" else (FONTE, 13)
            cor_valor = COR_MONO if chave == "numero_serie" else COR_TEXTO
            valor = ctk.CTkLabel(
                grade, text="", text_color=cor_valor,
                font=fonte_valor, anchor="e", justify="right",
            )
            valor.grid(row=i, column=1, sticky="e", pady=3)
            self._labels_detalhe[chave] = valor

        acoes = ctk.CTkFrame(conteudo_detalhe, fg_color="transparent")
        acoes.pack(fill="x", side="bottom", pady=(14, 0))
        self.botao_editar_detalhe = ctk.CTkButton(
            acoes, text="Editar", command=self._editar,
            fg_color=COR_GHOST, hover_color=COR_GHOST_HOVER, text_color=COR_TEXTO,
            corner_radius=10, height=36, font=(FONTE, 13),
        )
        self.botao_editar_detalhe.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.botao_excluir_detalhe = ctk.CTkButton(
            acoes, text="Excluir", command=self._excluir,
            fg_color="transparent", hover_color=COR_PERIGO_HOVER, text_color=COR_PERIGO_TEXTO,
            border_color=COR_PERIGO_BORDA, border_width=1,
            corner_radius=10, height=36, font=(FONTE, 13),
        )
        self.botao_excluir_detalhe.pack(side="left", fill="x", expand=True)

        self._atualizar_detalhes()

    def _configurar_estilo_treeview(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")

        estilo.configure(
            "Instrumentos.Treeview",
            background=COR_PAINEL, fieldbackground=COR_PAINEL, foreground=COR_TEXTO,
            rowheight=52, borderwidth=0, relief="flat", font=(FONTE, 12),
            bordercolor=COR_PAINEL, lightcolor=COR_PAINEL, darkcolor=COR_PAINEL,
        )
        estilo.configure(
            "Instrumentos.Treeview.Heading",
            background=COR_PAINEL, foreground=COR_TEXTO_FRACO,
            font=(FONTE, 11, "bold"), borderwidth=0, relief="flat",
            bordercolor=COR_PAINEL, lightcolor=COR_PAINEL, darkcolor=COR_PAINEL,
        )
        estilo.map(
            "Instrumentos.Treeview.Heading",
            background=[("active", COR_PAINEL), ("pressed", COR_PAINEL)],
            foreground=[("active", COR_TEXTO_FRACO)],
        )
        estilo.map(
            "Instrumentos.Treeview",
            background=[("selected", COR_SELECIONADO)],
            foreground=[("selected", COR_TEXTO)],
        )

        estilo.configure(
            "Instrumentos.Vertical.TScrollbar",
            background=COR_PAINEL, troughcolor=COR_PAINEL, bordercolor=COR_PAINEL,
            arrowcolor=COR_TEXTO_FRACO2, relief="flat", width=12,
        )

    def _ordenar_por(self, coluna):
        if coluna == self.coluna_ordenacao:
            self.ordem_crescente = not self.ordem_crescente
        else:
            self.coluna_ordenacao = coluna
            self.ordem_crescente = True
        self._atualizar_cabecalhos()
        self._carregar_lista()

    def _atualizar_cabecalhos(self):
        for chave, titulo, _ in COLUNAS:
            texto = titulo.upper()
            if chave == self.coluna_ordenacao:
                texto += " ▲" if self.ordem_crescente else " ▼"
            self.tree.heading(chave, text=texto, anchor="w")

    def _carregar_lista(self):
        termo = self.entrada_busca.get().strip().lower()
        colunas_validas = {c[0] for c in COLUNAS}
        coluna = self.coluna_ordenacao if self.coluna_ordenacao in colunas_validas else "tipo"
        direcao = "ASC" if self.ordem_crescente else "DESC"

        cur = self.con.cursor()
        total_geral = cur.execute("SELECT COUNT(*) FROM instrumentos").fetchone()[0]

        if termo:
            padrao = f"%{termo}%"
            cur.execute(
                f"""SELECT id, tipo, marca, modelo, numero_serie FROM instrumentos
                   WHERE lower(tipo) LIKE ? OR lower(marca) LIKE ? OR lower(modelo) LIKE ?
                   ORDER BY {coluna} {direcao}""",
                (padrao, padrao, padrao),
            )
        else:
            cur.execute(f"SELECT id, tipo, marca, modelo, numero_serie FROM instrumentos ORDER BY {coluna} {direcao}")

        self.tree.delete(*self.tree.get_children())
        linhas = cur.fetchall()
        for linha in linhas:
            id_, tipo, marca, modelo, numero_serie = linha
            self.tree.insert("", "end", iid=str(id_), values=(tipo or "", marca or "", modelo or "", numero_serie or ""))

        self.label_subtitulo.configure(text=f"{total_geral} instrumento(s) cadastrado(s)")
        self.label_total.configure(text=f"{len(linhas)} de {total_geral} instrumentos")
        self._atualizar_detalhes()

    def _atualizar_barra_rolagem(self, primeiro, ultimo):
        self.scroll.set(primeiro, ultimo)
        if float(primeiro) <= 0.0 and float(ultimo) >= 1.0:
            self.scroll.pack_forget()
        elif not self.scroll.winfo_ismapped():
            self.scroll.pack(side="left", fill="y")

    def _reavaliar_barra_rolagem(self):
        self._atualizar_barra_rolagem(*self.tree.yview())

    def _clique_na_lista(self, event):
        if not self.tree.identify_row(event.y):
            self.tree.selection_set([])

    def _id_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            return None
        if len(sel) > 1:
            messagebox.showinfo(
                "Selecione apenas um item",
                "Essa ação funciona com um item por vez. Selecione apenas um instrumento na lista.",
            )
            return None
        return int(sel[0])

    def _ids_selecionados(self):
        return [int(i) for i in self.tree.selection()]

    def _buscar_dados(self, id_):
        cur = self.con.cursor()
        cur.execute("SELECT * FROM instrumentos WHERE id = ?", (id_,))
        colunas = [d[0] for d in cur.description]
        linha = cur.fetchone()
        if not linha:
            return None
        return dict(zip(colunas, linha))

    def _novo(self):
        dialog = InstrumentoDialog(self)
        self.wait_window(dialog)
        if dialog.resultado:
            dados = dialog.resultado
            self.con.execute(
                """INSERT INTO instrumentos
                   (tipo, marca, modelo, numero_serie, foto_path, observacoes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (dados["tipo"], dados["marca"], dados["modelo"], dados["numero_serie"],
                 dados["foto_path"], dados["observacoes"]),
            )
            self.con.commit()
            self._carregar_lista()

    def _editar(self):
        id_ = self._id_selecionado()
        if id_ is None:
            messagebox.showinfo("Nenhum instrumento selecionado", "Selecione um instrumento na lista primeiro.")
            return
        dados = self._buscar_dados(id_)
        dialog = InstrumentoDialog(self, dados=dados)
        self.wait_window(dialog)
        if dialog.resultado:
            novos = dialog.resultado
            self.con.execute(
                """UPDATE instrumentos SET tipo=?, marca=?, modelo=?, numero_serie=?,
                   foto_path=?, observacoes=?
                   WHERE id=?""",
                (novos["tipo"], novos["marca"], novos["modelo"], novos["numero_serie"],
                 novos["foto_path"], novos["observacoes"], id_),
            )
            self.con.commit()
            self._carregar_lista()

    def _excluir(self):
        ids = self._ids_selecionados()
        if not ids:
            messagebox.showinfo("Nenhum instrumento selecionado", "Selecione um ou mais instrumentos na lista primeiro.")
            return

        if len(ids) == 1:
            dados = self._buscar_dados(ids[0])
            rotulo = dados["tipo"] + (f" - {dados['marca']}" if dados.get("marca") else "")
            pergunta = f"Excluir \"{rotulo}\" do cadastro?"
        else:
            rotulos = []
            for id_ in ids:
                dados = self._buscar_dados(id_)
                rotulos.append(dados["tipo"] + (f" - {dados['marca']}" if dados.get("marca") else ""))
            pergunta = f"Excluir {len(ids)} itens do cadastro?\n\n" + "\n".join(rotulos)

        if messagebox.askyesno("Confirmar exclusão", pergunta):
            fazer_backup(motivo="antes_exclusao")
            self.con.executemany("DELETE FROM instrumentos WHERE id = ?", [(i,) for i in ids])
            self.con.commit()
            self._carregar_lista()

    def _atualizar_detalhes(self):
        ids = self._ids_selecionados()

        if len(ids) != 1:
            self.bloco_detalhe.pack_forget()
            self.botao_editar_detalhe.configure(state="disabled")
            self.botao_excluir_detalhe.configure(state="normal" if ids else "disabled")
            return

        dados = self._buscar_dados(ids[0]) or {}
        nome = " ".join(p for p in [dados.get("marca"), dados.get("modelo")] if p) or dados.get("tipo", "")
        self._preencher_detalhes(
            tipo=dados.get("tipo", ""), nome=nome,
            marca=dados.get("marca") or "", modelo=dados.get("modelo") or "",
            numero_serie=dados.get("numero_serie") or "", caminho_foto=dados.get("foto_path"),
        )
        self.bloco_detalhe.pack(fill="x")
        self.botao_editar_detalhe.configure(state="normal")
        self.botao_excluir_detalhe.configure(state="normal")

    def _preencher_detalhes(self, tipo, nome, marca, modelo, numero_serie, caminho_foto):
        self.label_tipo_detalhe.configure(text=tipo.upper() if tipo else "")
        self.label_nome_detalhe.configure(text=nome)
        self._labels_detalhe["marca"].configure(text=marca)
        self._labels_detalhe["modelo"].configure(text=modelo)
        self._labels_detalhe["numero_serie"].configure(text=numero_serie)

        self._foto_detalhe_caminho = caminho_foto
        if caminho_foto and os.path.isfile(caminho_foto):
            try:
                imagem = Image.open(caminho_foto)
                imagem.thumbnail(TAMANHO_FOTO_DETALHE)
                self._foto_detalhe_img = ctk.CTkImage(
                    light_image=imagem, dark_image=imagem, size=imagem.size,
                )
                self.label_foto_detalhe.configure(image=self._foto_detalhe_img, text="")
                return
            except Exception:
                pass

        self._foto_detalhe_img = self._imagem_vazia
        self.label_foto_detalhe.configure(image=self._imagem_vazia, text="")

    def _abrir_foto_detalhe(self, event=None):
        caminho = self._foto_detalhe_caminho
        if caminho and os.path.isfile(caminho):
            os.startfile(caminho)


def _identificar_processo_windows():
    """No Windows, dissocia o app do ícone genérico do pythonw.exe na barra de tarefas."""
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("instrumentosmusicais.app")
    except Exception:
        pass


if __name__ == "__main__":
    _identificar_processo_windows()
    App().mainloop()
