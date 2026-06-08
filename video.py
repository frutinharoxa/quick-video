#!/usr/bin/env python3
import os
import sys
import re
import shutil
from pathlib import Path
from colorama import init, Fore, Style
from yt_dlp import YoutubeDL

init(autoreset=True)

BASE_DIR = Path(__file__).resolve().parent
VAR_DIR = BASE_DIR / "VAR"
VAR_DIR.mkdir(exist_ok=True)

# Map approximate vertical resolution to tag
def resolution_tag(height):
    if height is None:
        return "SD"
    try:
        h = int(height)
    except Exception:
        return "SD"
    if h >= 2160:
        return "4K"
    if h >= 1440:
        return "SHD"
    if h >= 720:
        return "HD"
    return "SD"

def choose_ext(info):
    # queremos MP4 final; yt-dlp pode muxar no postprocessor para mp4
    return "mp4"

def sanitize_filename(name):
    # basic safe filename
    return re.sub(r'[<>:"/\\|?*\n\r]+', '_', name).strip()

ydl_opts_base = {
    # salvar temporário em VAR e finalizar com mp4
    "outtmpl": str(VAR_DIR / "%(title)s [%(id)s] %(format_id)s.%(ext)s"),
    "format": "bestvideo+bestaudio/best",
    "merge_output_format": "mp4",
    "noplaylist": True,
    "quiet": True,  # controlamos a saída
    "no_warnings": True,
    "ignoreerrors": False,
    "continuedl": True,
    "logger": None,
    # progress_hooks será definido por download function
}

def download_and_report(url):
    print(Fore.CYAN + "Iniciando download..." + Style.RESET_ALL)
    info = {}
    def progress_hook(d):
        nonlocal info
        if d.get('status') == 'downloading':
            percent = d.get('downloaded_bytes', 0) / (d.get('total_bytes') or 1) * 100 if d.get('total_bytes') else 0
            speed = d.get('speed')
            eta = d.get('eta')
            line = f"\r{Fore.YELLOW}Baixando:{Style.RESET_ALL} {percent:5.1f}%"
            if speed:
                line += f" • {speed/1024/1024:.2f} MB/s"
            if eta is not None:
                line += f" • ETA {int(eta)}s"
            print(line, end='', flush=True)
        elif d.get('status') == 'finished':
            print("\r" + " " * 80, end='\r')
            info = d.copy()
            print(Fore.GREEN + "Stream merge." + Style.RESET_ALL)
        elif d.get('status') == 'error':
            print(Fore.RED + "\nErro no download." + Style.RESET_ALL)

    opts = dict(ydl_opts_base)
    opts['progress_hooks'] = [progress_hook]
    # Forçar metadados e thumbnails embedding e escrita de infojson se quiser
    opts['writethumbnail'] = False
    opts['writesubtitles'] = False

    try:
        with YoutubeDL(opts) as ydl:
            meta = ydl.extract_info(url, download=True)
    except Exception as e:
        print(Fore.RED + f"Falha ao baixar: {e}" + Style.RESET_ALL)
        return

    # meta pode ser dict com info do vídeo
    if not meta:
        print(Fore.RED + "Nenhuma informação retornada pelo yt-dlp." + Style.RESET_ALL)
        return

    # Determinar melhor vídeo e áudio usados no arquivo final
    # yt-dlp já mesclou em mp4; tentamos detectar a resolução a partir do formats selecionado.
    # Procurar por height no meta (if available)
    height = None
    # meta pode conter 'height' or 'requested_formats' list
    if isinstance(meta, dict):
        if meta.get('height'):
            height = meta.get('height')
        elif meta.get('requested_formats'):
            # take highest height among requested_formats
            for f in meta.get('requested_formats', []):
                if f.get('vcodec', 'none') != 'none' and f.get('height'):
                    height = max(height or 0, f.get('height'))
        elif meta.get('formats'):
            # try best format entry
            best = None
            for f in meta.get('formats'):
                if f.get('height') and (best is None or f.get('height') > best):
                    best = f.get('height')
            height = best

    tag = resolution_tag(height)
    # localizar arquivo resultante mais recente para renomear adicionando tag
    # Procurar arquivos mp4 com id em VAR_DIR
    id_ = meta.get('id') or ''
    title = meta.get('title') or 'video'
    safe_title = sanitize_filename(title)
    # find file with id
    candidates = list(VAR_DIR.glob(f"*{id_}*.mp4"))
    if not candidates:
        # fallback: try any mp4 with title
        candidates = list(VAR_DIR.glob(f"{safe_title}*.mp4"))
    if candidates:
        # pick most recent
        file = max(candidates, key=lambda p: p.stat().st_mtime)
        new_name = f"{safe_title} [{id_}] [{tag}].mp4"
        target = VAR_DIR / new_name
        try:
            file.replace(target)
            print(Fore.MAGENTA + f"Arquivo salvo: {target.name}" + Style.RESET_ALL)
        except Exception:
            # fallback to copy
            shutil.copy2(file, target)
            print(Fore.MAGENTA + f"Arquivo salvo (cópia): {target.name}" + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "Aviso: não foi possível localizar o arquivo .mp4 gerado para renomear." + Style.RESET_ALL)

def is_valid_url(text):
    # aceita URLs simples (http/https)
    return bool(re.match(r'^https?://\S+$', text.strip()))

def main_loop():
    print(Fore.GREEN + "Modo CLI - yt-dlp rápido. Cole a URL e pressione Enter. (Ctrl+C para sair)" + Style.RESET_ALL)
    try:
        while True:
            url = input(Fore.CYAN + "\nURL: " + Style.RESET_ALL).strip()
            if not url:
                continue
            if not is_valid_url(url):
                print(Fore.RED + "URL inválida. Insira uma URL iniciando com http:// ou https://." + Style.RESET_ALL)
                continue
            download_and_report(url)
            print(Fore.BLUE + "\nPróximo URL" + Style.RESET_ALL)
    except KeyboardInterrupt:
        print("\n" + Fore.YELLOW + "Encerrando." + Style.RESET_ALL)
        sys.exit(0)

if __name__ == "__main__":
    main_loop()

