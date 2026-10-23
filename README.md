# 🎵 LyricType



O **LyricType** é um jogo web interativo de digitação rítmica onde o utilizador treina a sua velocidade de escrita e pratica idiomas acompanhando a letra de músicas diretamente de vídeos do YouTube em tempo real.



## ✨ Funcionalidades



* **Busca Inteligente de Letras (Dual-Source):**

  * Procura prioritariamente letras sincronizadas (`.lrc`) através da API da **LRCLIB** com base nos metadados do vídeo.

  * Possui *fallback* automático para as legendas (manuais ou geradas automaticamente) do **YouTube** caso a música não seja encontrada na LRCLIB.

* **Suporte Multilíngue e Tradução Integrada:**

  * Deteta automaticamente o idioma original da música (**Português**, **Inglês** ou **Espanhol**).

  * Permite jogar no idioma original ou traduzir a letra em tempo real (via Google Translator / Tradução de legendas do YouTube).

* **Mecânica de Jogo Inteligente (*Gating*):**

  * Caso o jogador não termine de digitar o verso dentro do tempo da estrofe, o vídeo pausa automaticamente no final da linha e aguarda que a frase seja concluída para retomar a música.

  * Normalização de caracteres: ignora acentuação e sinais de pontuação durante a digitação, focando apenas em caracteres alfanuméricos (`a-z`, `0-9`).

* **Ajuste de Sincronia em Tempo Real:** Botões dedicados para adiantar ou atrasar o tempo da letra em incrementos de `0,5 s` para corrigir eventuais atrasos do vídeo.

* **Métricas de Desempenho ao Vivo:**

  * **Pontos:** Sistema de pontuação com multiplicador de até `4x` (aumenta a cada 15 acertos consecutivos) e bónus de linha perfeita.

  * **Combo:** Contagem de acertos seguidos (e registo do melhor combo no final).

  * **Precisão (%):** Taxa de acerto das teclas pressionadas.

  * **PPM (Palavras Por Minuto):** Cálculo dinâmico da velocidade de digitação.

* **Interface Adaptável:** Tema claro e escuro (*Light/Dark mode*) com persistência no navegador (`localStorage`) e suporte a dispositivos móveis.



## 🛠️ Tecnologias Utilizadas



### Back-end

* **[Python 3](https://www.python.org/)**

* **[Flask](https://flask.palletsprojects.com/):** Servidor web e roteamento da API REST.

* **[youtube-transcript-api](https://pypi.org/project/youtube-transcript-api/):** Extração e tradução de legendas diretamente do YouTube.

* **[deep-translator](https://pypi.org/project/deep-translator/):** Tradução em lote das letras obtidas via LRCLIB.

* **[Requests](https://pypi.org/project/requests/):** Consumo das APIs do YouTube (`oembed`) e da LRCLIB.



### Front-end

* **HTML5 & CSS3:** Estilização baseada em *Design Tokens* (`tokens.css`), animações CSS e variáveis nativas para troca de tema.

* **JavaScript (Vanilla):** Lógica do jogo, sincronização de *timecodes* a cada `80ms` e integração com a **YouTube IFrame Player API**.



## 📁 Estrutura do Projeto



> **Nota de configuração:** Como o Flask está configurado com `static_folder="static"` em `app.py`, certifica-te de que os ficheiros estáticos do front-end estão dentro da pasta `static/`:



```text

lyrictype/

├── app.py               # Servidor Flask e lógica de extração/tradução de letras

├── requirements.txt     # Dependências do Python

├── LICENSE              # Licença de uso do projeto (GNU GPLv3)

├── README.md            # Documentação do projeto

└── static/              # Ficheiros estáticos servidos pelo Flask

    ├── index.html       # Interface principal e motor do jogo em JS

    ├── tokens.css       # Variáveis de estilo, tipografia e temas (Claro/Escuro)

    └── icone.svg        # Logótipo e ícone da aplicação

```



## 🚀 Como Executar Localmente



### Pré-requisitos

* Python 3.8 ou superior instalado.

* Ligação à internet (para carregar o reprodutor do YouTube e consultar as APIs de letras).



### Passo a passo



1. **Clona o repositório:**

   ```bash

   git clone https://github.com/teu-utilizador/lyrictype.git

   cd lyrictype

   ```



2. **Cria e ativa um ambiente virtual (recomendado):**

   ```bash

   # Linux / macOS

   python3 -m venv venv

   source venv/bin/activate



   # Windows

   python -m venv venv

   venv\Scripts\activate

   ```



3. **Instala as dependências:**

   ```bash

   pip install -r requirements.txt

   ```



4. **Organiza a pasta de ficheiros estáticos (se ainda não estiver criada):**

   Garante que os ficheiros `index.html`, `tokens.css` e `icone.svg` estão dentro de um diretório chamado `static/`.



5. **Inicia o servidor:**

   ```bash

   python app.py

   ```



6. **Acede à aplicação:**

   Abre o navegador e acede a:

   ```text

   http://localhost:5000

   ```



## 🎮 Como Jogar



1. Copia o link de qualquer videoclipe ou música no **YouTube** (formatos suportados: link padrão `watch?v=`, `youtu.be/`, `shorts/` ou apenas o ID de 11 caracteres).

2. Cola o link no campo de texto e clica em **Carregar música**.

3. *(Opcional)* Escolhe a **Fonte da letra** (`Automática`, `LRCLIB` ou `Legenda do YouTube`) e o **Idioma da digitação** (`Português`, `Inglês` ou `Espanhol`).

4. Clica em **Começar jogo** e digita as letras que aparecem em destaque no palco.

   * Não precisas de digitar espaços, pontuação ou acentos — foca-te apenas nas letras e números!

   * Podes usar a tecla `Backspace` para desfazer caracteres na linha atual.

5. Ao terminar a música, confere o teu boletim final com a **Nota Geral (0 a 100)**, **Pontuação**, **Precisão**, **Melhor Combo** e **PPM**.



## 🔌 Documentação da API



### `GET /api/lyrics`



Retorna a letra sincronizada e processada para o motor do jogo.



#### Parâmetros de Query (`Query Strings`):



* **`url`** (`string`, **Obrigatório**): URL do vídeo do YouTube ou ID de 11 caracteres.

* **`src`** (`string`, *Opcional*): Fonte da letra: `auto` (padrão), `lrclib` ou `yt`.

* **`lang`** (`string`, *Opcional*): Código ISO do idioma desejado (`pt`, `en`, `es`). Vazio mantém o original.

* **`dur`** (`int`, *Opcional*): Duração do vídeo em segundos para refinar a precisão da busca na LRCLIB.



#### Exemplo de Resposta (`200 OK`):



```json

{

  "id": "dQw4w9WgXcQ",

  "lang": "en",

  "orig": "en",

  "generated": false,

  "source": "lrclib",

  "lines": [

    {

      "s": 18.5,

      "e": 22.1,

      "t": "We're no strangers to love"

    }

  ]

}

```



## 📄 Licença



Este projeto está sob a licença **GNU GPLv3**. Consulta o ficheiro [LICENSE](LICENSE) para mais detalhes.



> **Nota legal:** O LyricType não armazena músicas, vídeos ou letras protegidas por direitos de autor. Todo o conteúdo multimédia é reproduzido diretamente através da API oficial de incorporação do YouTube (YouTube IFrame Player API) e as letras são consultadas em tempo real via LRCLIB e legendas públicas do YouTube.
