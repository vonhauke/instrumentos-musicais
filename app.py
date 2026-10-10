import glob
import os
import shutil
import sqlite3
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
from urllib.parse import quote_plus

from PIL import Image, ImageTk

TAMANHO_PREVIEW = (220, 220)

PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PASTA_BASE, "instrumentos.db")
BACKUP_DIR = os.path.join(PASTA_BASE, "backups")
MAX_BACKUPS = 20

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
    ("numero_serie", "Nº Série", 140),
]


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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meus Instrumentos Musicais")
        self.geometry("780x480")
        self.minsize(640, 400)

        self.con = conectar()
        self.coluna_ordenacao = "tipo"
        self.ordem_crescente = True
        self._preview_img = None

        self._montar_interface()
        self._carregar_lista()

    def _montar_interface(self):
        topo = ttk.Frame(self, padding=(12, 12, 12, 0))
        topo.pack(fill="x")

        ttk.Label(topo, text="Buscar:").pack(side="left")
        self.var_busca = tk.StringVar()
        self.var_busca.trace_add("write", lambda *a: self._carregar_lista())
        ttk.Entry(topo, textvariable=self.var_busca, width=30).pack(side="left", padx=(5, 0))

        ttk.Button(topo, text="Novo instrumento", command=self._novo).pack(side="right")

        meio = ttk.Frame(self, padding=12)
        meio.pack(fill="both", expand=True)

        lista_frame = ttk.Frame(meio)
        lista_frame.pack(side="left", fill="both", expand=True)

        colunas = [c[0] for c in COLUNAS]
        self.tree = ttk.Treeview(lista_frame, columns=colunas, show="headings", selectmode="extended")
        for chave, titulo, largura in COLUNAS:
            self.tree.heading(chave, text=titulo, command=lambda c=chave: self._ordenar_por(c))
            self.tree.column(chave, width=largura, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._editar())
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._atualizar_preview())

        scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        preview_frame = ttk.Frame(meio, padding=(12, 0, 0, 0))
        preview_frame.pack(side="left", fill="y")
        self.label_preview = ttk.Label(
            preview_frame, text="Selecione um item\npara ver a foto",
            width=28, anchor="center", justify="center",
            relief="groove", padding=10,
        )
        self.label_preview.pack()

        self._atualizar_cabecalhos()

        rodape = ttk.Frame(self, padding=(12, 0, 12, 12))
        rodape.pack(fill="x")
        ttk.Button(rodape, text="Editar", command=self._editar).pack(side="left")
        ttk.Button(rodape, text="Excluir", command=self._excluir).pack(side="left", padx=(8, 0))
        ttk.Button(rodape, text="Abrir foto", command=self._abrir_foto).pack(side="left", padx=(8, 0))
        self.label_total = ttk.Label(rodape, text="")
        self.label_total.pack(side="right")

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
            texto = titulo
            if chave == self.coluna_ordenacao:
                texto += " ▲" if self.ordem_crescente else " ▼"
            self.tree.heading(chave, text=texto)

    def _carregar_lista(self):
        termo = self.var_busca.get().strip().lower()
        colunas_validas = {c[0] for c in COLUNAS}
        coluna = self.coluna_ordenacao if self.coluna_ordenacao in colunas_validas else "tipo"
        direcao = "ASC" if self.ordem_crescente else "DESC"

        cur = self.con.cursor()
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

        self.label_total.config(text=f"{len(linhas)} instrumento(s)")
        self._atualizar_preview()

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

    def _atualizar_preview(self):
        ids = self._ids_selecionados()

        if not ids:
            self._mostrar_mensagem_preview("Selecione um item\npara ver a foto")
            return
        if len(ids) > 1:
            self._mostrar_mensagem_preview(f"{len(ids)} itens selecionados")
            return

        dados = self._buscar_dados(ids[0])
        caminho = dados.get("foto_path") if dados else None

        if not caminho:
            self._mostrar_mensagem_preview("Este item não tem\nfoto cadastrada")
            return
        if not os.path.isfile(caminho):
            self._mostrar_mensagem_preview("Arquivo da foto\nnão encontrado")
            return

        try:
            imagem = Image.open(caminho)
            imagem.thumbnail(TAMANHO_PREVIEW)
            self._preview_img = ImageTk.PhotoImage(imagem)
            self.label_preview.configure(image=self._preview_img, text="")
        except Exception:
            self._mostrar_mensagem_preview("Não foi possível\nabrir essa imagem\n(formato não suportado)")

    def _mostrar_mensagem_preview(self, texto):
        self._preview_img = None
        self.label_preview.configure(image="", text=texto)

    def _abrir_foto(self):
        id_ = self._id_selecionado()
        if id_ is None:
            messagebox.showinfo("Nenhum instrumento selecionado", "Selecione um instrumento na lista primeiro.")
            return
        dados = self._buscar_dados(id_)
        caminho = dados.get("foto_path")
        if not caminho:
            messagebox.showinfo("Sem foto", "Este instrumento não tem foto cadastrada.")
            return
        if not os.path.isfile(caminho):
            messagebox.showwarning("Arquivo não encontrado", f"Não foi possível encontrar o arquivo:\n{caminho}")
            return
        os.startfile(caminho)


if __name__ == "__main__":
    App().mainloop()
