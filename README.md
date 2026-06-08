# video.py

Downloader de vídeo via terminal. Cola a URL, baixa em melhor qualidade, salva como `.mp4` com tag de resolução no nome.

---

## Requisitos

```bash
pip install yt-dlp colorama
```

---

## Use com duplo click ou

```bash
python video.py
```

O script entra em loop — cola uma URL, baixa, cola outra. `Ctrl+C` para sair.

---

## Saída

Os arquivos ficam na pasta `VAR/` no mesmo diretório do script, nomeados assim:

```
Título do Vídeo [id] [HD].mp4
```

Tags de resolução: `SD` / `HD` (720p+) / `SHD` (1440p+) / `4K` (2160p+)
