import glob
import json
import os
import shutil
import sqlite3
import tkinter as tk
import uuid
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
FOTOS_DIR = os.path.join(PASTA_BASE, "fotos")
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
    ("tipo", "coluna_tipo", 150),
    ("marca", "coluna_marca", 130),
    ("modelo", "coluna_modelo", 130),
    ("numero_serie", "coluna_serie", 120),
    ("data_inclusao", "coluna_data_inclusao", 120),
]

FONTE = "Aktiv Grotesk"

# ---- idiomas ----
IDIOMAS = {"pt": "Português", "en": "English"}
IDIOMA_PADRAO = "pt"
CONFIG_PATH = os.path.join(PASTA_BASE, "config.json")

TEXTOS = {
    "pt": {
        "subtitulo": "{n} instrumento(s) cadastrado(s)",
        "busca_placeholder": "Buscar por tipo, marca, modelo…",
        "botao_novo": "＋ Novo instrumento",
        "coluna_tipo": "Tipo",
        "coluna_marca": "Marca",
        "coluna_modelo": "Modelo",
        "coluna_serie": "Nº de série",
        "coluna_data_inclusao": "Data de inclusão",
        "rodape": "{x} de {y} instrumentos",
        "botao_editar": "Editar",
        "botao_excluir": "Excluir",
        "msg_selecione_titulo": "Selecione apenas um item",
        "msg_selecione_corpo": "Essa ação funciona com um item por vez. Selecione apenas um instrumento na lista.",
        "msg_nenhum_titulo": "Nenhum instrumento selecionado",
        "msg_nenhum_editar": "Selecione um instrumento na lista primeiro.",
        "msg_nenhum_excluir": "Selecione um ou mais instrumentos na lista primeiro.",
        "msg_confirmar_exclusao_titulo": "Confirmar exclusão",
        "msg_excluir_um": 'Excluir "{rotulo}" do cadastro?',
        "msg_excluir_varios": "Excluir {n} itens do cadastro?\n\n{lista}",
        "dialog_titulo_novo": "Novo instrumento",
        "dialog_titulo_editar": "Editar instrumento",
        "campo_tipo": "Tipo",
        "campo_marca": "Marca",
        "campo_modelo": "Modelo",
        "campo_serie": "Número de série",
        "botao_buscar_google": "Buscar no Google",
        "campo_foto": "Foto (arquivo)",
        "botao_escolher": "Escolher...",
        "campo_observacoes": "Observações",
        "botao_cancelar": "Cancelar",
        "botao_salvar": "Salvar",
        "msg_campo_obrigatorio_titulo": "Campo obrigatório",
        "msg_campo_obrigatorio_corpo": "Informe o tipo do item.",
        "msg_preencha_dados_titulo": "Preencha os dados primeiro",
        "msg_preencha_dados_corpo": "Informe ao menos a marca ou o modelo para buscar.",
        "dialogo_escolher_foto_titulo": "Escolher foto do instrumento",
        "filtro_imagens": "Imagens",
        "filtro_todos_arquivos": "Todos os arquivos",
    },
    "en": {
        "subtitulo": "{n} instrument(s) registered",
        "busca_placeholder": "Search by type, brand, model…",
        "botao_novo": "＋ New instrument",
        "coluna_tipo": "Type",
        "coluna_marca": "Brand",
        "coluna_modelo": "Model",
        "coluna_serie": "Serial no.",
        "coluna_data_inclusao": "Date added",
        "rodape": "{x} of {y} instruments",
        "botao_editar": "Edit",
        "botao_excluir": "Delete",
        "msg_selecione_titulo": "Select only one item",
        "msg_selecione_corpo": "This action works with one item at a time. Select only one instrument in the list.",
        "msg_nenhum_titulo": "No instrument selected",
        "msg_nenhum_editar": "Select an instrument in the list first.",
        "msg_nenhum_excluir": "Select one or more instruments in the list first.",
        "msg_confirmar_exclusao_titulo": "Confirm deletion",
        "msg_excluir_um": 'Delete "{rotulo}" from the catalog?',
        "msg_excluir_varios": "Delete {n} items from the catalog?\n\n{lista}",
        "dialog_titulo_novo": "New instrument",
        "dialog_titulo_editar": "Edit instrument",
        "campo_tipo": "Type",
        "campo_marca": "Brand",
        "campo_modelo": "Model",
        "campo_serie": "Serial number",
        "botao_buscar_google": "Search on Google",
        "campo_foto": "Photo (file)",
        "botao_escolher": "Choose...",
        "campo_observacoes": "Notes",
        "botao_cancelar": "Cancel",
        "botao_salvar": "Save",
        "msg_campo_obrigatorio_titulo": "Required field",
        "msg_campo_obrigatorio_corpo": "Enter the item's type.",
        "msg_preencha_dados_titulo": "Fill in the details first",
        "msg_preencha_dados_corpo": "Enter at least the brand or model to search.",
        "dialogo_escolher_foto_titulo": "Choose instrument photo",
        "filtro_imagens": "Images",
        "filtro_todos_arquivos": "All files",
    },
}


def traduzir(idioma, chave, **kwargs):
    texto = TEXTOS.get(idioma, TEXTOS[IDIOMA_PADRAO])[chave]
    return texto.format(**kwargs) if kwargs else texto


def carregar_idioma():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if dados.get("idioma") in TEXTOS:
                return dados["idioma"]
    except Exception:
        pass
    return IDIOMA_PADRAO


def salvar_idioma(idioma):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"idioma": idioma}, f)
    except Exception:
        pass

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


def formatar_data(data_iso):
    """Converte a data guardada no banco (AAAA-MM-DD, pra ordenar certo) para exibição em DD/MM/AAAA."""
    if not data_iso:
        return None
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return data_iso


def copiar_foto_para_pasta(caminho_original):
    """Garante que a foto do instrumento tenha uma cópia própria dentro de fotos/,
    em vez de só apontar pro arquivo original em outro lugar do computador."""
    if not caminho_original:
        return caminho_original

    if not os.path.isabs(caminho_original):
        return caminho_original  # já é um nome gerenciado (ou inválido) — mantém como está

    if not os.path.isfile(caminho_original):
        return caminho_original  # caminho absoluto que não existe — mantém como está

    os.makedirs(FOTOS_DIR, exist_ok=True)
    extensao = os.path.splitext(caminho_original)[1]
    novo_nome = f"{uuid.uuid4().hex}{extensao}"
    shutil.copy2(caminho_original, os.path.join(FOTOS_DIR, novo_nome))
    return novo_nome


def resolver_foto(nome_ou_caminho):
    """Transforma o valor salvo no banco no caminho real do arquivo no disco."""
    if not nome_ou_caminho:
        return None
    if os.path.isabs(nome_ou_caminho):
        return nome_ou_caminho  # fotos cadastradas antes dessa mudança
    return os.path.join(FOTOS_DIR, nome_ou_caminho)


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
    colunas_existentes = {linha[1] for linha in con.execute("PRAGMA table_info(instrumentos)")}
    if "data_inclusao" not in colunas_existentes:
        con.execute("ALTER TABLE instrumentos ADD COLUMN data_inclusao TEXT")
    con.commit()
    return con


class InstrumentoDialog(ctk.CTkToplevel):
    """Janela de cadastro/edição de um instrumento."""

    def __init__(self, master, dados=None):
        super().__init__(master)
        self.idioma = getattr(master, "idioma", IDIOMA_PADRAO)
        self.resultado = None
        self.dados_originais = dados
        self.title(self.t("dialog_titulo_editar") if dados else self.t("dialog_titulo_novo"))
        self.configure(fg_color=COR_FUNDO)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.campos = {}
        self._montar_formulario()

        if dados:
            self._preencher(dados)

        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._centralizar_sobre(master)

    def _centralizar_sobre(self, master):
        self.update()
        largura = self.winfo_width()
        altura = self.winfo_height()
        x = master.winfo_rootx() + (master.winfo_width() - largura) // 2
        y = master.winfo_rooty() + (master.winfo_height() - altura) // 2
        # nunca deixa a janela nascer fora dos limites da tela
        x = max(0, min(x, self.winfo_screenwidth() - largura))
        y = max(0, min(y, self.winfo_screenheight() - altura))
        # chama o geometry "cru" do Tk (não o do CTk) para não escalar de novo um
        # tamanho que já está escalado — é isso que fazia a janela nascer fora do lugar
        tk.Toplevel.geometry(self, f"{largura}x{altura}+{x}+{y}")
        self.update()

    def t(self, chave, **kwargs):
        return traduzir(self.idioma, chave, **kwargs)

    def _montar_formulario(self):
        frame = ctk.CTkFrame(self, fg_color=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=24, pady=20)

        def rotulo(texto, obrigatorio=False, primeiro=False):
            ctk.CTkLabel(
                frame, text=texto + ("*" if obrigatorio else ""),
                text_color=COR_TEXTO_FRACO, font=(FONTE, 12), anchor="w",
            ).pack(fill="x", pady=(0 if primeiro else 14, 4))

        def add_entry(label, chave, primeiro=False):
            rotulo(label, primeiro=primeiro)
            var = tk.StringVar()
            entry = ctk.CTkEntry(
                frame, textvariable=var, width=320, height=36,
                fg_color=COR_PAINEL, border_color=COR_BORDA, border_width=1,
                corner_radius=8, text_color=COR_TEXTO, font=(FONTE, 13),
            )
            entry.pack(fill="x")
            self.campos[chave] = var
            return entry

        rotulo(self.t("campo_tipo"), obrigatorio=True, primeiro=True)
        var_tipo = tk.StringVar()
        combo_tipo = ctk.CTkComboBox(
            frame, values=TIPOS, variable=var_tipo, width=320, height=36,
            fg_color=COR_PAINEL, border_color=COR_BORDA, border_width=1,
            corner_radius=8, text_color=COR_TEXTO, font=(FONTE, 13),
            button_color=COR_GHOST, button_hover_color=COR_GHOST_HOVER,
            dropdown_fg_color=COR_PAINEL, dropdown_hover_color=COR_GHOST,
            dropdown_text_color=COR_TEXTO, dropdown_font=(FONTE, 13),
            command=lambda valor: combo_tipo.configure(values=TIPOS),
        )
        combo_tipo.set("")
        combo_tipo.pack(fill="x")
        combo_tipo.bind("<KeyRelease>", self._filtrar_tipos)
        self.campos["tipo"] = var_tipo
        self._combo_tipo = combo_tipo

        add_entry(self.t("campo_marca"), "marca")
        add_entry(self.t("campo_modelo"), "modelo")
        add_entry(self.t("campo_serie"), "numero_serie")

        ctk.CTkButton(
            frame, text=self.t("botao_buscar_google"), command=self._buscar_no_google,
            fg_color=COR_GHOST, hover_color=COR_GHOST_HOVER, text_color=COR_TEXTO,
            corner_radius=8, height=34, font=(FONTE, 13),
        ).pack(fill="x", pady=(14, 0))

        rotulo(self.t("campo_foto"))
        foto_frame = ctk.CTkFrame(frame, fg_color="transparent")
        foto_frame.pack(fill="x")
        var_foto = tk.StringVar()
        ctk.CTkEntry(
            foto_frame, textvariable=var_foto, height=36,
            fg_color=COR_PAINEL, border_color=COR_BORDA, border_width=1,
            corner_radius=8, text_color=COR_TEXTO, font=(FONTE, 13),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            foto_frame, text=self.t("botao_escolher"), command=lambda: self._escolher_foto(var_foto),
            fg_color=COR_GHOST, hover_color=COR_GHOST_HOVER, text_color=COR_TEXTO,
            corner_radius=8, height=36, width=90, font=(FONTE, 13),
        ).pack(side="left")
        self.campos["foto_path"] = var_foto

        rotulo(self.t("campo_observacoes"))
        self.campo_observacoes = ctk.CTkTextbox(
            frame, width=320, height=80,
            fg_color=COR_PAINEL, border_color=COR_BORDA, border_width=1,
            corner_radius=8, text_color=COR_TEXTO, font=(FONTE, 13),
        )
        self.campo_observacoes.pack(fill="x")

        botoes = ctk.CTkFrame(frame, fg_color="transparent")
        botoes.pack(fill="x", pady=(20, 0))
        ctk.CTkButton(
            botoes, text=self.t("botao_salvar"), command=self._salvar,
            fg_color=COR_OURO, hover_color=COR_OURO_HOVER, text_color=COR_OURO_TEXTO,
            corner_radius=8, height=38, font=(FONTE, 14, "bold"),
        ).pack(side="right")
        ctk.CTkButton(
            botoes, text=self.t("botao_cancelar"), command=self.destroy,
            fg_color=COR_GHOST, hover_color=COR_GHOST_HOVER, text_color=COR_TEXTO,
            corner_radius=8, height=38, font=(FONTE, 13),
        ).pack(side="right", padx=(0, 8))

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
        self._combo_tipo.configure(values=valores)
        try:
            if valores:
                self._combo_tipo._open_dropdown_menu()
            else:
                self._combo_tipo._dropdown_menu.close()
        except Exception:
            pass
        self._combo_tipo.focus_set()
        self._combo_tipo._entry.icursor(tk.END)

    def _buscar_no_google(self):
        partes = [
            self.campos["marca"].get().strip(),
            self.campos["modelo"].get().strip(),
        ]
        termo = " ".join(p for p in partes if p)
        if not termo:
            messagebox.showinfo(
                self.t("msg_preencha_dados_titulo"),
                self.t("msg_preencha_dados_corpo"),
                parent=self,
            )
            return
        url = f"https://www.google.com/search?q={quote_plus(termo)}"
        webbrowser.open(url)

    def _escolher_foto(self, var_foto):
        caminho = filedialog.askopenfilename(
            title=self.t("dialogo_escolher_foto_titulo"),
            filetypes=[
                (self.t("filtro_imagens"), "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tif *.tiff *.heic *.heif *.ico"),
                (self.t("filtro_todos_arquivos"), "*.*"),
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
            messagebox.showwarning(self.t("msg_campo_obrigatorio_titulo"), self.t("msg_campo_obrigatorio_corpo"), parent=self)
            self._combo_tipo.focus_set()
            return

        self.resultado = {
            "tipo": tipo,
            "marca": self.campos["marca"].get().strip(),
            "modelo": self.campos["modelo"].get().strip(),
            "numero_serie": self.campos["numero_serie"].get().strip(),
            "foto_path": copiar_foto_para_pasta(self.campos["foto_path"].get().strip()),
            "observacoes": self.campo_observacoes.get("1.0", "end").strip(),
        }
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.idioma = carregar_idioma()
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
        self.after(50, lambda: self._centralizar_na_tela(1000, 640))

    def _aplicar_icone(self):
        if os.path.isfile(ICONE_PATH):
            try:
                self.iconbitmap(ICONE_PATH)
            except tk.TclError:
                pass

    def _centralizar_na_tela(self, largura, altura):
        """Centraliza a janela considerando o tamanho real já escalado pelo Windows (DPI),
        em vez de só usar os pixels "lógicos" pedidos — evita a janela nascer fora da tela."""
        self.geometry(f"{largura}x{altura}")
        self.update_idletasks()
        largura_real = self.winfo_width()
        altura_real = self.winfo_height()
        tela_largura = self.winfo_screenwidth()
        tela_altura = self.winfo_screenheight()
        x = max((tela_largura - largura_real) // 2, 0)
        y = max((tela_altura - altura_real) // 2, 0)
        self.geometry(f"+{x}+{y}")

    def t(self, chave, **kwargs):
        return traduzir(self.idioma, chave, **kwargs)

    def _mudar_idioma(self, nome_exibido):
        novo_idioma = next((cod for cod, nome in IDIOMAS.items() if nome == nome_exibido), IDIOMA_PADRAO)
        if novo_idioma == self.idioma:
            return
        self.idioma = novo_idioma
        salvar_idioma(novo_idioma)
        self._aplicar_idioma()

    def _aplicar_idioma(self):
        self.botao_novo.configure(text=self.t("botao_novo"))
        self.entrada_busca.configure(placeholder_text=self.t("busca_placeholder"))
        self.botao_editar_detalhe.configure(text=self.t("botao_editar"))
        self.botao_excluir_detalhe.configure(text=self.t("botao_excluir"))
        for legenda, texto_key in self._legendas_detalhe.values():
            legenda.configure(text=self.t(texto_key))
        self._atualizar_cabecalhos()
        self._carregar_lista()

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

        self.botao_novo = ctk.CTkButton(
            cabecalho, text=self.t("botao_novo"), command=self._novo,
            fg_color=COR_OURO, hover_color=COR_OURO_HOVER, text_color=COR_OURO_TEXTO,
            font=(FONTE, 14, "bold"), corner_radius=10, height=38,
        )
        self.botao_novo.pack(side="right")

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
            placeholder_text=self.t("busca_placeholder"),
            fg_color="transparent", border_width=0,
            text_color=COR_TEXTO, placeholder_text_color=COR_TEXTO_FRACO2,
            font=(FONTE, 13),
        )
        self.entrada_busca.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.entrada_busca.bind("<KeyRelease>", lambda e: self._carregar_lista())

        self.var_idioma = tk.StringVar(value=IDIOMAS[self.idioma])
        ctk.CTkOptionMenu(
            cabecalho, values=list(IDIOMAS.values()), variable=self.var_idioma,
            command=self._mudar_idioma, width=120, height=38, corner_radius=10,
            fg_color=COR_PAINEL, button_color=COR_GHOST, button_hover_color=COR_GHOST_HOVER,
            text_color=COR_TEXTO, dropdown_fg_color=COR_PAINEL, dropdown_hover_color=COR_GHOST,
            dropdown_text_color=COR_TEXTO, font=(FONTE, 13),
        ).pack(side="right", padx=(0, 12))

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
        for chave, texto_key, largura in COLUNAS:
            self.tree.heading(chave, text=self.t(texto_key), command=lambda c=chave: self._ordenar_por(c))
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
        self._legendas_detalhe = {}
        campos_grade = [
            ("campo_marca", "marca"), ("campo_modelo", "modelo"),
            ("coluna_serie", "numero_serie"), ("coluna_data_inclusao", "data_inclusao"),
        ]
        for i, (texto_key, chave) in enumerate(campos_grade):
            legenda = ctk.CTkLabel(
                grade, text=self.t(texto_key), text_color=COR_TEXTO_FRACO,
                font=(FONTE, 13), anchor="w",
            )
            legenda.grid(row=i, column=0, sticky="w", pady=3)
            self._legendas_detalhe[chave] = (legenda, texto_key)
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
            acoes, text=self.t("botao_editar"), command=self._editar,
            fg_color=COR_GHOST, hover_color=COR_GHOST_HOVER, text_color=COR_TEXTO,
            corner_radius=10, height=36, font=(FONTE, 13),
        )
        self.botao_editar_detalhe.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.botao_excluir_detalhe = ctk.CTkButton(
            acoes, text=self.t("botao_excluir"), command=self._excluir,
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
        for chave, texto_key, _ in COLUNAS:
            texto = self.t(texto_key).upper()
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
                f"""SELECT id, tipo, marca, modelo, numero_serie, data_inclusao FROM instrumentos
                   WHERE lower(tipo) LIKE ? OR lower(marca) LIKE ? OR lower(modelo) LIKE ?
                   ORDER BY {coluna} {direcao}""",
                (padrao, padrao, padrao),
            )
        else:
            cur.execute(f"SELECT id, tipo, marca, modelo, numero_serie, data_inclusao FROM instrumentos ORDER BY {coluna} {direcao}")

        self.tree.delete(*self.tree.get_children())
        linhas = cur.fetchall()
        for linha in linhas:
            id_, tipo, marca, modelo, numero_serie, data_inclusao = linha
            self.tree.insert(
                "", "end", iid=str(id_),
                values=(tipo or "", marca or "", modelo or "", numero_serie or "", formatar_data(data_inclusao) or "—"),
            )

        self.label_subtitulo.configure(text=self.t("subtitulo", n=total_geral))
        self.label_total.configure(text=self.t("rodape", x=len(linhas), y=total_geral))
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
                self.t("msg_selecione_titulo"),
                self.t("msg_selecione_corpo"),
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
                   (tipo, marca, modelo, numero_serie, foto_path, observacoes, data_inclusao)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (dados["tipo"], dados["marca"], dados["modelo"], dados["numero_serie"],
                 dados["foto_path"], dados["observacoes"], datetime.now().strftime("%Y-%m-%d")),
            )
            self.con.commit()
            self._carregar_lista()

    def _editar(self):
        id_ = self._id_selecionado()
        if id_ is None:
            messagebox.showinfo(self.t("msg_nenhum_titulo"), self.t("msg_nenhum_editar"))
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
            messagebox.showinfo(self.t("msg_nenhum_titulo"), self.t("msg_nenhum_excluir"))
            return

        if len(ids) == 1:
            dados = self._buscar_dados(ids[0])
            rotulo = dados["tipo"] + (f" - {dados['marca']}" if dados.get("marca") else "")
            pergunta = self.t("msg_excluir_um", rotulo=rotulo)
        else:
            rotulos = []
            for id_ in ids:
                dados = self._buscar_dados(id_)
                rotulos.append(dados["tipo"] + (f" - {dados['marca']}" if dados.get("marca") else ""))
            pergunta = self.t("msg_excluir_varios", n=len(ids), lista="\n".join(rotulos))

        if messagebox.askyesno(self.t("msg_confirmar_exclusao_titulo"), pergunta):
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
            numero_serie=dados.get("numero_serie") or "", caminho_foto=resolver_foto(dados.get("foto_path")),
            data_inclusao=formatar_data(dados.get("data_inclusao")) or "—",
        )
        self.bloco_detalhe.pack(fill="x")
        self.botao_editar_detalhe.configure(state="normal")
        self.botao_excluir_detalhe.configure(state="normal")

    def _preencher_detalhes(self, tipo, nome, marca, modelo, numero_serie, caminho_foto, data_inclusao=""):
        self.label_tipo_detalhe.configure(text=tipo.upper() if tipo else "")
        self.label_nome_detalhe.configure(text=nome)
        self._labels_detalhe["marca"].configure(text=marca)
        self._labels_detalhe["modelo"].configure(text=modelo)
        self._labels_detalhe["numero_serie"].configure(text=numero_serie)
        self._labels_detalhe["data_inclusao"].configure(text=data_inclusao)

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
