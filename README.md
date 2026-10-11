# my chaotic room

Aplicativo de janela para Windows para cadastrar e organizar seus instrumentos musicais e equipamentos
(guitarras, pedais, sintetizadores, microfones, cabos e o que mais morar na sua sala).
Os dados ficam num banco SQLite local, no seu computador.

- Interface escura feita com [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (grafite, marfim e âmbar)
- Lista em ordem alfabética, que pode ser reordenada clicando no cabeçalho de qualquer coluna
- Busca rápida por tipo, marca e modelo
- Cadastro com tipo, marca, modelo, número de série, foto e observações
- Campo **Tipo** com autocompletar: digite uma letra e aparecem os tipos que começam com ela
- Painel de detalhes com a foto do instrumento selecionado (clique na foto para abri-la)
- Seleção múltipla para excluir vários itens de uma vez
- Botão **Buscar no Google** no cadastro, que pesquisa só pela marca e modelo
- Data de inclusão no formato DD/MM/AAAA
- Interface em **Português** e **English**

## Baixar e usar (Windows)

1. Abra a página de [**Releases**](https://github.com/vonhauke/my-chaotic-room/releases/latest) e baixe o arquivo **my chaotic room.exe**.
2. Dê dois cliques nele. Não precisa instalar nada, nem o Python.

> Na primeira vez, o Windows pode mostrar um aviso azul (SmartScreen), porque o programa não é assinado.
> Clique em **Mais informações → Executar assim mesmo**.

Cada pessoa começa com o cadastro vazio. Os dados ficam no próprio computador, em `%APPDATA%\my chaotic room`.

## Rodar pelo código-fonte

Se preferir rodar sem o `.exe`, você precisa de:

- Windows
- Python 3.10+

## Como usar

```
pip install -r requirements.txt
python app.py
```

Ou dê dois cliques em `Abrir.bat`, que abre o app sem a janela do terminal.

1. Clique em **＋ Novo instrumento**, escolha o tipo e preencha o que quiser. Só o tipo é obrigatório.
2. Clique num instrumento da lista para ver a foto e os detalhes. Clique numa área vazia para limpar a seleção.
3. Use **Editar** e **Excluir** no painel de detalhes. Com `Ctrl` ou `Shift` você seleciona vários itens para excluir juntos.

> A fonte da interface é a Aktiv Grotesk. Se ela não estiver instalada no seu Windows, o app usa uma fonte padrão no lugar.

## Onde ficam os dados

Tudo é guardado no computador de quem usa e **não vai para o GitHub** (está no `.gitignore`). No `.exe`, fica em `%APPDATA%\my chaotic room`; rodando pelo código-fonte, fica ao lado do `app.py`:

| Pasta/arquivo | O que é |
|---------------|---------|
| `instrumentos.db` | Banco SQLite com o cadastro |
| `fotos/` | Cópia de cada foto escolhida, para o app não depender do arquivo original |
| `backups/` | Cópia do banco feita toda vez que o app abre e antes de qualquer exclusão (guarda as 20 mais recentes) |
| `config.json` | Idioma escolhido |

Para trocar de computador, copie essa pasta inteira (ou pelo menos `instrumentos.db` e `fotos/`).

## Estrutura

| Arquivo | Função |
|---------|--------|
| `app.py` | Aplicativo completo: interface, banco de dados e backups |
| `build_exe.py` | Gera o `.exe` em `dist/` |
| `Abrir.bat` | Atalho para abrir o app sem terminal |
| `assets_icone/` | Ícone do app (`.ico`, `.icns`, `.png` e os `.svg` de origem) |
| `maquete_tela_principal.html` / `.png` | Maquete da tela principal, usada como referência de design |
