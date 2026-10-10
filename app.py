import os
import sqlite3
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog
from urllib.parse import quote_plus

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instrumentos.db")

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


def conectar():
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
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.gif *.bmp"), ("Todos os arquivos", "*.*")],
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

        colunas = [c[0] for c in COLUNAS]
        self.tree = ttk.Treeview(meio, columns=colunas, show="headings", selectmode="browse")
        for chave, titulo, largura in COLUNAS:
            self.tree.heading(chave, text=titulo)
            self.tree.column(chave, width=largura, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._editar())

        scroll = ttk.Scrollbar(meio, orient="vertical", command=self.tree.yview)
        scroll.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        rodape = ttk.Frame(self, padding=(12, 0, 12, 12))
        rodape.pack(fill="x")
        ttk.Button(rodape, text="Editar", command=self._editar).pack(side="left")
        ttk.Button(rodape, text="Excluir", command=self._excluir).pack(side="left", padx=(8, 0))
        ttk.Button(rodape, text="Abrir foto", command=self._abrir_foto).pack(side="left", padx=(8, 0))
        self.label_total = ttk.Label(rodape, text="")
        self.label_total.pack(side="right")

    def _carregar_lista(self):
        termo = self.var_busca.get().strip().lower()
        cur = self.con.cursor()
        if termo:
            padrao = f"%{termo}%"
            cur.execute(
                """SELECT id, tipo, marca, modelo, numero_serie FROM instrumentos
                   WHERE lower(tipo) LIKE ? OR lower(marca) LIKE ? OR lower(modelo) LIKE ?
                   ORDER BY tipo""",
                (padrao, padrao, padrao),
            )
        else:
            cur.execute("SELECT id, tipo, marca, modelo, numero_serie FROM instrumentos ORDER BY tipo")

        self.tree.delete(*self.tree.get_children())
        linhas = cur.fetchall()
        for linha in linhas:
            id_, tipo, marca, modelo, numero_serie = linha
            self.tree.insert("", "end", iid=str(id_), values=(tipo or "", marca or "", modelo or "", numero_serie or ""))

        self.label_total.config(text=f"{len(linhas)} instrumento(s)")

    def _id_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

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
        id_ = self._id_selecionado()
        if id_ is None:
            messagebox.showinfo("Nenhum instrumento selecionado", "Selecione um instrumento na lista primeiro.")
            return
        dados = self._buscar_dados(id_)
        rotulo = dados["tipo"] + (f" - {dados['marca']}" if dados.get("marca") else "")
        if messagebox.askyesno("Confirmar exclusão", f"Excluir \"{rotulo}\" do cadastro?"):
            self.con.execute("DELETE FROM instrumentos WHERE id = ?", (id_,))
            self.con.commit()
            self._carregar_lista()

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
