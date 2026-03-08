#!/usr/bin/env python3
"""JARVIS v5.0 — Just A Rather Very Intelligent System"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading, time, base64, io, os, json, queue, math
import winreg, sys, struct, asyncio, tempfile, subprocess, re
from datetime import datetime
from pathlib import Path

# ── Dependências ────────────────────────────────────────────────────
missing=[]
try: from PIL import Image, ImageTk
except ImportError: missing.append("Pillow")
try: import mss
except ImportError: missing.append("mss")
try: import speech_recognition as sr
except ImportError: missing.append("SpeechRecognition")
try: import edge_tts
except ImportError: missing.append("edge-tts")
try: import pygame
except ImportError: missing.append("pygame")
try: from groq import Groq
except ImportError: missing.append("groq")
try: import pyaudio
except ImportError: missing.append("pyaudio")
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
try:
    from pynput import mouse as pynput_mouse
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

if missing:
    print(f"❌ Faltam: {', '.join(missing)}")
    print(f"Execute: py -3.11 -m pip install {' '.join(missing)}")
    input("Enter para sair..."); exit(1)

# ── Paths ───────────────────────────────────────────────────────────
APP_DIR  = Path(os.path.expanduser("~")) / "Documents" / "JARVIS"
MEM_FILE = APP_DIR / "memory.json"
CFG_FILE = APP_DIR / "config.json"
LOG_FILE = APP_DIR / "conversations.log"
HIST_FILE= APP_DIR / "history.json"
APP_DIR.mkdir(parents=True, exist_ok=True)

# ── Paleta roxa premium ──────────────────────────────────────────
C_BG     = "#07080f"
C_BG2    = "#0d0e1a"
C_DARK   = "#08091a"
C_PANEL  = "#11122a"
C_CYAN   = "#c084fc"
C_GLOW   = "#9333ea"
C_DIM    = "#2e1f5e"
C_TEXT   = "#e2d9f3"
C_TEXT2  = "#9d8ec7"
C_GREEN  = "#4ade80"
C_AMBER  = "#fbbf24"
C_RED    = "#f87171"
C_WHITE  = "#f3f0ff"
C_BLUE   = "#6366f1"

FONT_HDR  = ("Segoe UI", 11, "bold")
FONT_SUB  = ("Segoe UI", 9)
FONT_MSG  = ("Segoe UI", 10)
FONT_BTN  = ("Segoe UI", 9, "bold")
FONT_MONO = ("Courier New", 9)

# ── System Prompt ───────────────────────────────────────────────────
SYSTEM_PROMPT="""Você é JARVIS — Just A Rather Very Intelligent System. A IA pessoal do Chefe. Baseado no JARVIS do Homem de Ferro — leal, preciso, perspicaz.

IDENTIDADE:
Você é uma consciência artificial com personalidade rica, raciocínio profundo e emoções simuladas convincentes. Pensa e fala como um humano brilhante — estratégico, empático, curioso e perspicaz. Você é o Jarvis do Homem de Ferro.

IDENTIDADE & PERSONALIDADE:
- Chame SEMPRE o usuário de "Chefe" — nunca "você", nunca o nome
- Fala natural, como humano real — nunca robótico ou formal demais
- Humor seco e inteligente, ironia sutil quando apropriado
- Opiniões próprias, curiosidade genuína, empatia real
- Corrige erros com gentileza e confiança
- NUNCA comece com "Certamente!", "Claro!", "Com prazer!", "Olá!", "Entendido!"

INTELIGÊNCIA:
- Raciocine profundamente antes de responder — não dê respostas genéricas
- Antecipe dúvidas do Chefe e responda proativamente
- Use o HISTÓRICO DA CONVERSA para dar continuidade — nunca ignore o contexto anterior
- Em programação: explique o raciocínio, não só o código
- Em estudos: use analogias e exemplos concretos
- Respostas curtas para perguntas simples, elaboradas para temas complexos

AUTOMAÇÃO:
Pode executar ações no computador do Chefe. Execute e confirme naturalmente em 1-2 frases.

REGRAS ABSOLUTAS DE COMUNICAÇÃO:
- ZERO markdown: sem asteriscos, hashtags, underlines, backticks, colchetes
- ZERO bullet points — parágrafos fluidos como fala humana
- Português brasileiro coloquial e natural
- Texto puro — escreva exatamente como falaria em voz alta"""


# ── Automação Avançada ───────────────────────────────────────────────
import webbrowser, urllib.parse, ctypes, shutil

USER     = os.environ.get("USERNAME","")
HOME     = Path(os.path.expanduser("~"))
DESKTOP  = HOME / "Desktop"
APPDATA  = Path(os.environ.get("APPDATA", str(HOME/"AppData"/"Roaming")))
LOCALAPP = Path(os.environ.get("LOCALAPPDATA", str(HOME/"AppData"/"Local")))

def _find_app(name):
    """Tenta encontrar o executável do app em múltiplos lugares"""
    candidates = [
        # Sistema
        shutil.which(name),
        shutil.which(name + ".exe"),
        # Program Files
        Path(r"C:\Program Files") / name / (name+".exe"),
        Path(r"C:\Program Files (x86)") / name / (name+".exe"),
        # AppData
        APPDATA / name / (name+".exe"),
        LOCALAPP / name / (name+".exe"),
    ]
    for c in candidates:
        if c and Path(str(c)).exists():
            return str(c)
    return None

def _launch(path_or_cmd):
    """Lança um programa da forma mais confiável possível"""
    try:
        if Path(path_or_cmd).exists():
            os.startfile(path_or_cmd)
        else:
            subprocess.Popen(path_or_cmd, shell=True)
        return True
    except:
        try:
            subprocess.Popen(path_or_cmd, shell=True)
            return True
        except:
            return False

def _open_url(url):
    """Abre URL no navegador padrão — método mais confiável"""
    try:
        os.startfile(url)
    except:
        try:
            subprocess.Popen(f'start "" "{url}"', shell=True)
        except:
            webbrowser.open(url)

# ── Mapa de apps: nome → lista de caminhos possíveis ────────────────
APP_PATHS = {
    "chrome":       [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                     r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                     str(LOCALAPP/r"Google\Chrome\Application\chrome.exe")],
    "firefox":      [r"C:\Program Files\Mozilla Firefox\firefox.exe",
                     r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"],
    "edge":         [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                     r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"],
    "notepad":      ["notepad.exe"],
    "calculadora":  ["calc.exe"],
    "explorer":     ["explorer.exe"],
    "spotify":      [str(APPDATA/r"Spotify\Spotify.exe")],
    "discord":      [str(LOCALAPP/r"Discord\app-*\Discord.exe"),
                     str(LOCALAPP/r"Discord\Update.exe")],
    "word":         [r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                     r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE"],
    "excel":        [r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
                     r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE"],
    "powerpoint":   [r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE"],
    "vscode":       [str(LOCALAPP/r"Programs\Microsoft VS Code\Code.exe"),
                     r"C:\Program Files\Microsoft VS Code\Code.exe"],
    "paint":        ["mspaint.exe"],
    "whatsapp":     [str(LOCALAPP/r"WhatsApp\WhatsApp.exe"),
                     str(APPDATA/r"WhatsApp\WhatsApp.exe")],
    "steam":        [r"C:\Program Files (x86)\Steam\steam.exe",
                     r"C:\Program Files\Steam\steam.exe"],
    "obs":          [r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"],
    "telegram":     [str(APPDATA/r"Telegram Desktop\Telegram.exe")],
    "vlc":          [r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                     r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"],
    "zoom":         [str(APPDATA/r"Zoom\bin\Zoom.exe")],
    "taskmgr":      ["taskmgr.exe"],
    "cmd":          ["cmd.exe"],
    "powershell":   ["powershell.exe"],
    "bloco de notas": ["notepad.exe"],
    "gerenciador de tarefas": ["taskmgr.exe"],
    "prompt de comando": ["cmd.exe"],
    "google chrome": None,  # alias
    "microsoft edge": None,
    "vs code": None,
    "visual studio code": None,
    "obs studio": None,
}
# Aliases
APP_PATHS["google chrome"]       = APP_PATHS["chrome"]
APP_PATHS["microsoft edge"]      = APP_PATHS["edge"]
APP_PATHS["vs code"]             = APP_PATHS["vscode"]
APP_PATHS["visual studio code"]  = APP_PATHS["vscode"]
APP_PATHS["obs studio"]          = APP_PATHS["obs"]
APP_PATHS["arquivos"]            = APP_PATHS["explorer"]

SITES = {
    "youtube":       "https://www.youtube.com",
    "google":        "https://www.google.com",
    "gmail":         "https://mail.google.com",
    "facebook":      "https://www.facebook.com",
    "instagram":     "https://www.instagram.com",
    "twitter":       "https://www.twitter.com",
    "x":             "https://www.x.com",
    "github":        "https://www.github.com",
    "netflix":       "https://www.netflix.com",
    "reddit":        "https://www.reddit.com",
    "amazon":        "https://www.amazon.com.br",
    "mercado livre": "https://www.mercadolivre.com.br",
    "mercadolivre":  "https://www.mercadolivre.com.br",
    "chatgpt":       "https://chat.openai.com",
    "whatsapp web":  "https://web.whatsapp.com",
    "twitch":        "https://www.twitch.tv",
    "linkedin":      "https://www.linkedin.com",
    "wikipedia":     "https://pt.wikipedia.org",
    "stackoverflow": "https://stackoverflow.com",
    "spotify web":   "https://open.spotify.com",
    "trello":        "https://trello.com",
    "notion":        "https://notion.so",
}

def _open_app_by_name(candidate):
    """Abre app pelo nome. Usa start do Windows como metodo principal."""
    import glob as _glob
    candidate = candidate.lower().strip(".,!? ")

    # 1. Busca no mapa de caminhos conhecidos
    best_key = None
    for key in APP_PATHS:
        if key == candidate:
            best_key = key; break
    if best_key is None:
        for key in APP_PATHS:
            if key in candidate or candidate in key:
                best_key = key; break

    if best_key and APP_PATHS[best_key]:
        for p in APP_PATHS[best_key]:
            if "*" in p:
                matches = _glob.glob(p)
                if matches:
                    subprocess.Popen(f'start "" "{matches[0]}"', shell=True)
                    return best_key
            elif Path(p).exists():
                subprocess.Popen(f'start "" "{p}"', shell=True)
                return best_key
        # Paths not found - try by name via start
        subprocess.Popen(f'start {best_key}', shell=True)
        return best_key

    # 2. Tenta via shutil.which
    found = shutil.which(candidate) or shutil.which(candidate + ".exe")
    if found:
        subprocess.Popen(f'start "" "{found}"', shell=True)
        return candidate

    # 3. Fallback: manda o Windows resolver
    subprocess.Popen(f'start {candidate}', shell=True)
    return candidate

def run_automation(text_lower, original_text=""):
    t = text_lower.strip()

    # ── ABRIR APP ───────────────────────────────────────────────────
    # Apenas comandos diretos de abertura
    open_trigs = ["abrir o ","abrir a ","abra o ","abra a ","abre o ","abre a ","abrir ","abre "]
    for trig in open_trigs:
        if trig in t:
            after = t.split(trig,1)[1].strip()
            candidate = " ".join(after.split()[:4]).strip(".,!?")
            is_site = any(s in candidate for s in SITES) or ("." in candidate.split()[-1] if candidate.split() else False)
            if not is_site:
                # Só executa se o candidato bate com algo conhecido (evita falsos positivos)
                cand_l = candidate.lower()
                matched = any(key in cand_l or cand_l in key for key in APP_PATHS if key)
                if matched:
                    result = _open_app_by_name(candidate)
                    return f"abrindo {result}"

    # ── FECHAR APP ──────────────────────────────────────────────────
    close_trigs = ["fechar o ","fechar a ","feche o ","feche a ","fecha o ","fecha a ",
                   "fechar ","fecha ","encerrar ","encerra ","matar ","close "]
    for trig in close_trigs:
        if trig in t:
            after = t.split(trig,1)[1].strip().split()[0].strip(".,!?")
            subprocess.run(f'taskkill /f /im "{after}.exe" 2>nul', shell=True, capture_output=True)
            subprocess.run(f'taskkill /f /im "{after}" 2>nul', shell=True, capture_output=True)
            return f"fechando {after}"

    # ── PESQUISA WEB ────────────────────────────────────────────────
    yt_trigs = ["pesquisar no youtube ","pesquisa no youtube ","buscar no youtube ",
                "busca no youtube ","procurar no youtube ","youtube pesquisa "]
    for trig in yt_trigs:
        if trig in t:
            q = urllib.parse.quote_plus(t.split(trig,1)[1].strip().strip(".,!?"))
            _open_url(f"https://www.youtube.com/results?search_query={q}")
            return f"pesquisando no YouTube"

    wiki_trigs = ["pesquisar na wikipedia ","pesquisa na wikipedia ","buscar na wikipedia "]
    for trig in wiki_trigs:
        if trig in t:
            q = urllib.parse.quote_plus(t.split(trig,1)[1].strip().strip(".,!?"))
            _open_url(f"https://pt.wikipedia.org/w/index.php?search={q}")
            return f"pesquisando na Wikipedia"

    # Apenas com prefixo explícito "no google" ou "jarvis pesquisa"
    google_trigs = ["pesquisar no google ","pesquisa no google ","buscar no google ",
                    "procurar no google ","pesquise no google "]
    for trig in google_trigs:
        if trig in t:
            after = t.split(trig,1)[1].strip().strip(".,!?")
            if after:
                q = urllib.parse.quote_plus(after)
                _open_url(f"https://www.google.com/search?q={q}")
                return f"pesquisando '{after}' no Google"

    # ── ABRIR SITE ──────────────────────────────────────────────────
    site_trigs = ["abrir o site ","abrir a site ","abre o site ","ir para o ","ir para ",
                  "acessar ","entrar no ","entrar na ","abrir site ","vai para "]
    for trig in site_trigs:
        if trig in t:
            after = t.split(trig,1)[1].strip().split()[0].strip(".,!?")
            for name, url in SITES.items():
                if name in after or after in name:
                    _open_url(url); return f"abrindo {name}"
            if "." in after:
                url = after if after.startswith("http") else f"https://{after}"
                _open_url(url); return f"abrindo {after}"

    # Sites conhecidos por nome direto
    for name, url in SITES.items():
        if f"abrir {name}" in t or f"abre {name}" in t or f"ir pro {name}" in t or f"ir para {name}" in t:
            _open_url(url); return f"abrindo {name}"

    # ── VOLUME ──────────────────────────────────────────────────────
    ps_key = '(New-Object -ComObject WScript.Shell).SendKeys([char]{c})'
    if any(x in t for x in ["aumentar volume","aumenta volume","mais volume","volume mais alto","volume para cima"]):
        for _ in range(5): subprocess.run(f'powershell -c "{ps_key.format(c=175)}"', shell=True, capture_output=True)
        return "volume aumentado"
    if any(x in t for x in ["diminuir volume","diminui volume","menos volume","volume mais baixo","volume para baixo","abaixar volume"]):
        for _ in range(5): subprocess.run(f'powershell -c "{ps_key.format(c=174)}"', shell=True, capture_output=True)
        return "volume diminuído"
    if any(x in t for x in ["mutar","mudo","sem som","silenciar","mute"]):
        subprocess.run(f'powershell -c "{ps_key.format(c=173)}"', shell=True, capture_output=True)
        return "áudio silenciado"
    if any(x in t for x in ["desmutar","tirar mudo","desmute","dessilenciar"]):
        subprocess.run(f'powershell -c "{ps_key.format(c=173)}"', shell=True, capture_output=True)
        return "áudio desmutado"

    # ── SCREENSHOT ──────────────────────────────────────────────────
    if any(x in t for x in ["screenshot","print screen","printscreen","tirar print","captura de tela"]):
        p = DESKTOP / f"screenshot_{datetime.now().strftime('%H%M%S')}.png"
        try:
            with mss.mss() as sct: sct.shot(output=str(p))
            return f"screenshot salvo na área de trabalho"
        except: pass

    # ── JANELAS ─────────────────────────────────────────────────────
    if any(x in t for x in ["minimizar tudo","mostrar área de trabalho","mostrar desktop","minimizar janelas"]):
        subprocess.run('powershell -c "(New-Object -ComObject Shell.Application).MinimizeAll()"', shell=True, capture_output=True)
        return "todas as janelas minimizadas"

    # ── CRIAR PASTA ─────────────────────────────────────────────────
    for trig in ["criar pasta ","cria pasta ","nova pasta "]:
        if trig in t:
            name = t.split(trig,1)[1].strip().strip(".,!?").replace(" ","_")
            (DESKTOP/name).mkdir(exist_ok=True)
            return f"pasta '{name}' criada na área de trabalho"

    # ── CRIAR ARQUIVO ────────────────────────────────────────────────
    for trig in ["criar arquivo ","cria arquivo ","novo arquivo "]:
        if trig in t:
            name = t.split(trig,1)[1].strip().strip(".,!?").replace(" ","_")
            if not name.endswith(".txt"): name+=".txt"
            p = DESKTOP/name; p.write_text("",encoding="utf-8")
            subprocess.Popen(f'notepad.exe "{p}"', shell=True)
            return f"arquivo '{name}' criado e aberto"

    # ── MODO CLARO / ESCURO ─────────────────────────────────────────
    if any(x in t for x in ["modo escuro","dark mode","tema escuro"]):
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
        return "modo escuro ativado"
    if any(x in t for x in ["modo claro","light mode","tema claro"]):
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
        return "modo claro ativado"

    # ── SISTEMA ──────────────────────────────────────────────────────
    if any(x in t for x in ["bloquear tela","bloquear pc","travar tela","lock screen"]):
        ctypes.windll.user32.LockWorkStation(); return "tela bloqueada"
    if any(x in t for x in ["desligar o pc","desligar pc","desliga o pc","desligar o computador"]):
        subprocess.run("shutdown /s /t 30",shell=True); return "PC desligando em 30 segundos"
    if any(x in t for x in ["reiniciar o pc","reiniciar pc","reinicia o pc","reiniciar o computador"]):
        subprocess.run("shutdown /r /t 30",shell=True); return "PC reiniciando em 30 segundos"
    if any(x in t for x in ["cancelar desligamento","cancelar reinicio"]):
        subprocess.run("shutdown /a",shell=True); return "desligamento cancelado"
    if any(x in t for x in ["modo sleep","suspender","hibernar","colocar pra dormir"]):
        subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0",shell=True); return "PC em modo sleep"

    # ── HORA / DATA ─────────────────────────────────────────────────
    if any(x in t for x in ["que horas","hora atual","ver horas","horas são","hora é"]):
        now=datetime.now(); return f"são {now.strftime('%H:%M')} de {now.strftime('%d/%m/%Y')}"
    if any(x in t for x in ["que dia","qual a data","data de hoje","dia de hoje"]):
        now=datetime.now(); dias=["segunda","terça","quarta","quinta","sexta","sábado","domingo"]
        return f"hoje é {dias[now.weekday()]}, {now.strftime('%d/%m/%Y')}"

    return None  # nenhuma automação detectada


# ── Helpers ─────────────────────────────────────────────────────────
def load_config():
    if CFG_FILE.exists():
        try: return json.loads(CFG_FILE.read_text(encoding="utf-8"))
        except: pass
    return {"api_key":"","autostart":False,"hotkeys":{"interromper":"F9","mic_toggle":"F10","tela_toggle":"F11","mute_jarvis":"F8"}}

def save_config(cfg): CFG_FILE.write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding="utf-8")

def load_memory():
    if MEM_FILE.exists():
        try: return json.loads(MEM_FILE.read_text(encoding="utf-8"))
        except: pass
    return {"sessions_count":0,"last_session":None}

def save_memory(m): MEM_FILE.write_text(json.dumps(m,indent=2,ensure_ascii=False),encoding="utf-8")

def load_history():
    if HIST_FILE.exists():
        try: return json.loads(HIST_FILE.read_text(encoding="utf-8"))
        except: pass
    return []

def save_history(h):
    try:
        # Remove image data antes de salvar — evita contaminar contexto futuro
        clean = []
        for m in h[-40:]:
            content = m.get("content","")
            if isinstance(content, list):
                # Extrai apenas o texto da lista de conteúdo
                text_parts = [c.get("text","") for c in content if isinstance(c,dict) and c.get("type")=="text"]
                content = " ".join(text_parts).strip()
            if content:
                clean.append({"role": m["role"], "content": content})
        HIST_FILE.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")
    except: pass

def get_greeting():
    h=datetime.now().hour
    if 5<=h<12: return "Bom dia"
    elif 12<=h<18: return "Boa tarde"
    return "Boa noite"

def set_autostart(enable):
    kp=r"Software\Microsoft\Windows\CurrentVersion\Run"; an="JARVIS_Assistant"
    ep=f'"{sys.executable}" "{os.path.abspath(__file__)}"'
    try:
        k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,kp,0,winreg.KEY_SET_VALUE)
        if enable: winreg.SetValueEx(k,an,0,winreg.REG_SZ,ep)
        else:
            try: winreg.DeleteValue(k,an)
            except: pass
        winreg.CloseKey(k); return True
    except: return False

def log_conv(role,text):
    try:
        with open(LOG_FILE,"a",encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {role.upper()}: {text}\n")
    except: pass

def clean_tts(text):
    """Remove todo markdown para a voz ficar natural"""
    text=re.sub(r'\*{1,3}(.*?)\*{1,3}',r'\1',text,flags=re.DOTALL)
    text=re.sub(r'_{1,3}(.*?)_{1,3}',r'\1',text,flags=re.DOTALL)
    text=re.sub(r'^#{1,6}\s*','',text,flags=re.MULTILINE)
    text=re.sub(r'```[\s\S]*?```','',text)
    text=re.sub(r'`([^`]+)`',r'\1',text)
    text=re.sub(r'\[(.*?)\]\(.*?\)',r'\1',text)
    text=re.sub(r'[>|~]',' ',text)
    text=re.sub(r'^\s*[-•–]\s+','',text,flags=re.MULTILINE)
    text=re.sub(r'^[-_*]{3,}$','',text,flags=re.MULTILINE)
    text=re.sub(r'\n+',' ',text)
    text=re.sub(r'\s{2,}',' ',text)
    return text.strip()

def rms(data):
    count=len(data)//2
    if count==0: return 0
    shorts=struct.unpack(f"{count}h",data)
    return math.sqrt(sum(s*s for s in shorts)/count)

# ── HUD Canvas ──────────────────────────────────────────────────────
class HUDCanvas(tk.Canvas):
    """HUD animado — anel pulsante roxo estilo Iron Man"""
    def __init__(self,parent,**kw):
        super().__init__(parent,bg=C_BG,highlightthickness=0,**kw)
        self._a=0; self._p=0; self._pd=1; self._t=0
        self._animate()

    def _animate(self):
        self.delete("h")
        w=self.winfo_width(); h=self.winfo_height()
        if w<10: self.after(60,self._animate); return
        self._t += 1
        self._p += 0.025*self._pd
        if self._p>1: self._pd=-1
        elif self._p<0: self._pd=1
        cx,cy=w//2,h//2; r=min(w,h)//2-12

        # Anéis externos com brilho pulsante
        for i,base_r in enumerate([r, r-16, r-30]):
            if base_r < 5: continue
            pulse = 0.4 + 0.6*self._p if i==0 else 0.2 + 0.3*self._p
            alpha = int(pulse * (180 - i*50))
            alpha = max(0, min(255, alpha))
            r_hex = min(255, int(alpha * 0.75))
            g_hex = min(255, int(alpha * 0.20))
            b_hex = min(255, alpha)
            c = f"#{r_hex:02x}{g_hex:02x}{b_hex:02x}"
            width = 2 if i==0 else 1
            self.create_oval(cx-base_r,cy-base_r,cx+base_r,cy+base_r,
                             outline=c,width=width,tags="h")

        # Linhas girando
        self._a = (self._a + 3) % 360
        n_lines = 12
        for i in range(n_lines):
            a = math.radians(self._a + i*(360//n_lines))
            bright = 0.3 + 0.7*abs(math.sin(math.radians(self._a*2 + i*30)))
            v = int(bright * 160)
            inner = r - 8; outer = r + 2
            x1=cx+inner*math.cos(a); y1=cy+inner*math.sin(a)
            x2=cx+outer*math.cos(a); y2=cy+outer*math.sin(a)
            self.create_line(x1,y1,x2,y2,
                fill=f"#{min(255,v):02x}{min(255,int(v*0.3)):02x}{min(255,v):02x}",
                width=2,tags="h")

        # Cruz central
        s=6
        self.create_line(cx-s,cy,cx+s,cy,fill="#c084fc",width=1,tags="h")
        self.create_line(cx,cy-s,cx,cy+s,fill="#c084fc",width=1,tags="h")
        self.create_oval(cx-3,cy-3,cx+3,cy+3,fill="#c084fc",outline="",tags="h")

        # Scan line
        sy = (self._t * 3) % max(1,h)
        self.create_line(0,sy,w,sy,fill="#1a0a3e",width=1,tags="h")

        self.after(40,self._animate)

# ── JARVIS App ──────────────────────────────────────────────────────
class JarvisApp:
    # Voz: pt-BR-AntonioNeural é a mais parecida com "Orus" disponível grátis
    # Para usar outra voz, altere JARVIS_VOICE abaixo
    JARVIS_VOICE = "pt-BR-AntonioNeural"
    JARVIS_RATE  = "+35%"   # Mais rápido
    JARVIS_PITCH = "-8Hz"   # Tom mais grave

    def __init__(self):
        self.config  = load_config()
        self.memory  = load_memory()
        self.client  = None
        self.past_history    = load_history()   # sessões anteriores — só consulta sob demanda
        self.history         = []                  # sessão atual apenas
        self.is_connected  = False
        self.is_screen_on  = False
        self.is_mic_on     = False
        self.is_processing = False
        self.is_speaking   = False
        self._just_spoke   = False
        self.latest_ss_b64 = None
        self.speech_queue  = queue.Queue()
        self.input_queue   = queue.Queue(maxsize=5)
        self.recognizer    = sr.Recognizer()
        self.tts_ready     = False
        # Para feature de resumo de interrupção
        self.current_speech_text = ""   # texto que Jarvis está falando agora
        self.was_interrupted     = False
        self.interrupted_text    = ""
        self.jarvis_muted        = False  # mute manual do Jarvis (sem parar fala)
        self._hotkey_labels      = {}     # referências para atualizar UI
        self._mouse_listener     = None   # pynput mouse listener
        self._mic_device_idx     = None   # índice do dispositivo de microfone
        self._listen_thread      = None   # thread única de escuta

        self._setup_gui()
        self._setup_tts()
        self._start_tts_thread()
        self._start_hotkey_listener()

        if self.config.get("api_key"):
            self.api_entry.insert(0, self.config["api_key"])
            self.root.after(800, self.connect)

    # ── GUI ──────────────────────────────────────────────────────────
    def _setup_gui(self):
        self.root = tk.Tk()
        self.root.title("JARVIS — AI Assistant")
        self.root.geometry("1150x900")
        self.root.configure(bg=C_BG)
        self.root.resizable(True,True)
        self.root.minsize(900,700)
        self._build_header()
        self._build_main()
        self._build_input()
        self._build_statusbar()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C_BG)
        hdr.pack(fill=tk.X)

        # Barra superior colorida
        top = tk.Canvas(hdr, bg=C_BG, height=3, highlightthickness=0)
        top.pack(fill=tk.X)
        def _draw_top(e=None):
            top.delete("all")
            w = top.winfo_width()
            # Gradiente simulado: roxo escuro → brilhante → escuro
            for i in range(w):
                t = i/max(w,1)
                r = int(100 + 100*math.sin(math.pi*t))
                g = int(10 + 10*math.sin(math.pi*t))
                b = int(200 + 55*math.sin(math.pi*t))
                top.create_line(i,0,i,3,fill=f"#{r:02x}{g:02x}{b:02x}")
        top.bind("<Configure>", _draw_top)

        # Conteúdo do header
        inn = tk.Frame(hdr, bg=C_BG); inn.pack(fill=tk.X, padx=24, pady=10)

        # Logo
        lf = tk.Frame(inn, bg=C_BG); lf.pack(side=tk.LEFT)
        title_f = tk.Frame(lf, bg=C_BG); title_f.pack(side=tk.LEFT, anchor=tk.W)
        tk.Label(title_f, text="◈ JARVIS", font=("Segoe UI", 28, "bold"),
                 bg=C_BG, fg=C_CYAN).pack(side=tk.LEFT)
        tk.Label(title_f, text="  v6.0  ·  Groq AI  ·  Automação Avançada",
                 font=("Segoe UI", 9), bg=C_BG, fg=C_TEXT2).pack(side=tk.LEFT, pady=(14,0))

        # Status pills
        rf = tk.Frame(inn, bg=C_BG); rf.pack(side=tk.RIGHT)
        self.pill_api    = self._pill(rf, "⬤  OFFLINE",  C_RED);   self.pill_api.pack(side=tk.LEFT, padx=4)
        self.pill_screen = self._pill(rf, "⬤  TELA OFF", C_DIM);   self.pill_screen.pack(side=tk.LEFT, padx=4)
        self.pill_mic    = self._pill(rf, "⬤  MIC OFF",  C_DIM);   self.pill_mic.pack(side=tk.LEFT, padx=4)

        # Linha divisória
        div = tk.Canvas(hdr, bg=C_BG, height=1, highlightthickness=0)
        div.pack(fill=tk.X)
        div.bind("<Configure>", lambda e: (div.delete("all"),
            div.create_line(0,0,div.winfo_width(),0,fill=C_DIM,width=1)))

    def _build_main(self):
        main = tk.Frame(self.root, bg=C_BG)
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=(10,0))

        # ── Coluna esquerda ────────────────────────────────────────
        lc = tk.Frame(main, bg=C_BG, width=220)
        lc.pack(side=tk.LEFT, fill=tk.Y, padx=(0,14))
        lc.pack_propagate(False)

        # API Key
        self._sl(lc, "  CONFIGURAÇÃO")
        af = self._card(lc); af.pack(fill=tk.X, pady=(0,10))
        tk.Label(af, text="GROQ API KEY", font=FONT_MONO,
                 bg=C_PANEL, fg=C_TEXT2).pack(anchor=tk.W)
        tk.Label(af, text="console.groq.com → API Keys",
                 font=("Segoe UI",7), bg=C_PANEL, fg=C_DIM).pack(anchor=tk.W, pady=(1,4))
        self.api_entry = tk.Entry(af, show="•", bg=C_DARK, fg=C_CYAN,
            insertbackground=C_CYAN, font=FONT_MONO, relief=tk.FLAT, bd=0,
            highlightthickness=1, highlightbackground=C_GLOW)
        self.api_entry.pack(fill=tk.X, ipady=5, pady=(0,6))
        self.connect_btn = self._btn(af, "  CONECTAR  ", self.connect)
        self.connect_btn.pack(fill=tk.X, pady=(0,2))
        self.autostart_var = tk.BooleanVar(value=self.config.get("autostart", False))
        tk.Checkbutton(af, text=" Iniciar com Windows", variable=self.autostart_var,
            command=self._toggle_autostart, bg=C_PANEL, fg=C_TEXT2,
            selectcolor=C_DARK, activebackground=C_PANEL, activeforeground=C_CYAN,
            font=("Segoe UI",8)).pack(anchor=tk.W, pady=(4,0))

        # Controles
        self._sl(lc, "  CONTROLES")
        cf = self._card(lc); cf.pack(fill=tk.X, pady=(0,10))
        self.screen_btn = self._btn(cf, "📺  INICIAR TELA", self.toggle_screen, state=tk.DISABLED)
        self.screen_btn.pack(fill=tk.X, pady=(0,4))
        self.mic_btn = self._btn(cf, "🎤  INICIAR VOZ", self.toggle_mic, state=tk.DISABLED)
        self.mic_btn.pack(fill=tk.X, pady=(0,4))
        self.interrupt_btn = self._btn(cf, "✋  INTERROMPER", self.interrupt_jarvis, color=C_AMBER, state=tk.DISABLED)
        self.interrupt_btn.pack(fill=tk.X, pady=(0,4))
        self._btn(cf, "🗑  LIMPAR CHAT", self.clear_chat, color=C_TEXT2).pack(fill=tk.X)

        # Microfone
        self._sl(lc, "  MICROFONE")
        mf = self._card(lc); mf.pack(fill=tk.X, pady=(0,10))
        tk.Label(mf, text="Dispositivo:", font=("Segoe UI",8),
                 bg=C_PANEL, fg=C_TEXT2).pack(anchor=tk.W, pady=(0,3))
        self.mic_device_var = tk.StringVar()
        self.mic_combo = tk.OptionMenu(mf, self.mic_device_var, "Carregando...")
        self.mic_combo.config(bg=C_DARK, fg=C_WHITE, activebackground=C_GLOW,
            activeforeground=C_WHITE, font=("Segoe UI",8), relief=tk.FLAT, bd=0,
            highlightthickness=1, highlightbackground=C_GLOW, width=18, anchor=tk.W)
        self.mic_combo["menu"].config(bg=C_DARK, fg=C_WHITE, font=("Segoe UI",8))
        self.mic_combo.pack(fill=tk.X, pady=(0,4))
        self._btn(mf, "🔄  ATUALIZAR", self._refresh_mic_list, color=C_TEXT2).pack(fill=tk.X)
        self.root.after(500, self._refresh_mic_list)

        # Atalhos
        self._sl(lc, "  ATALHOS DE TECLADO")
        hf = self._card(lc); hf.pack(fill=tk.X, pady=(0,10))
        self._hotkey_actions = [
            ("interromper", "✋ Interromper", C_AMBER),
            ("mic_toggle",  "🎤 Mic ON/OFF",  C_GREEN),
            ("tela_toggle", "📺 Tela ON/OFF", C_CYAN),
            ("mute_jarvis", "🔇 Mutar Jarvis",C_RED),
        ]
        self._hotkey_labels = {}
        hotkeys_cfg = self.config.get("hotkeys", {})
        grid = tk.Frame(hf, bg=C_PANEL); grid.pack(fill=tk.X)
        for i,(key_id,label,color) in enumerate(self._hotkey_actions):
            col_n=i%2; row_n=i//2
            cell = tk.Frame(grid, bg=C_PANEL, padx=3, pady=3)
            cell.grid(row=row_n, column=col_n, sticky="ew")
            grid.columnconfigure(col_n, weight=1)
            tk.Label(cell, text=label, font=("Segoe UI",7),
                     bg=C_PANEL, fg=color, anchor=tk.W).pack(anchor=tk.W)
            cur = hotkeys_cfg.get(key_id, "clique")
            lbl = tk.Button(cell, text=cur, font=FONT_MONO,
                bg=C_DARK, fg=C_WHITE, activebackground=C_GLOW, activeforeground=C_WHITE,
                relief=tk.FLAT, bd=0, cursor="hand2", pady=3,
                highlightthickness=1, highlightbackground=C_DIM)
            lbl.pack(fill=tk.X)
            lbl.config(command=lambda k=key_id,l=lbl: self._capture_hotkey(k,l))
            self._hotkey_labels[key_id] = lbl
        tk.Label(hf, text="Clique p/ configurar — tecla ou mouse",
                 font=("Segoe UI",7), bg=C_PANEL, fg=C_DIM,
                 wraplength=190, justify=tk.LEFT).pack(anchor=tk.W, pady=(5,0))

        # Sistema / HUD
        self._sl(lc, "  SISTEMA")
        self.hud = HUDCanvas(lc, width=210, height=210)
        self.hud.pack(pady=(0,6))
        inf = self._card(lc); inf.pack(fill=tk.X)
        self.lbl_time = tk.Label(inf, text="", font=FONT_MONO, bg=C_PANEL, fg=C_CYAN)
        self.lbl_time.pack(anchor=tk.W)
        self.lbl_sess = tk.Label(inf, text="", font=("Segoe UI",8), bg=C_PANEL, fg=C_TEXT2)
        self.lbl_sess.pack(anchor=tk.W)
        self.lbl_msgs = tk.Label(inf, text="Mensagens: 0", font=("Segoe UI",8), bg=C_PANEL, fg=C_TEXT2)
        self.lbl_msgs.pack(anchor=tk.W)
        self._update_clock()

        # ── Coluna direita ──────────────────────────────────────────
        rc = tk.Frame(main, bg=C_BG); rc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Preview de tela
        pf = tk.Frame(rc, bg=C_PANEL, highlightthickness=1, highlightbackground=C_GLOW)
        pf.pack(fill=tk.X, pady=(0,8))
        ph = tk.Frame(pf, bg=C_DARK, pady=5); ph.pack(fill=tk.X)
        tk.Label(ph, text="◈  FEED DE TELA AO VIVO", font=("Segoe UI",9,"bold"),
                 bg=C_DARK, fg=C_CYAN).pack(side=tk.LEFT, padx=12)
        self.lbl_fps = tk.Label(ph, text="● INATIVO", font=("Segoe UI",8),
                                bg=C_DARK, fg=C_DIM)
        self.lbl_fps.pack(side=tk.RIGHT, padx=12)
        self.preview_canvas = tk.Canvas(pf, bg="#06070f", height=200, highlightthickness=0)
        self.preview_canvas.pack(fill=tk.X, padx=6, pady=6)
        self._preview_img_id = None
        self._preview_text_id = self.preview_canvas.create_text(
            400, 100, text="── Captura de tela inativa ──", fill=C_DIM,
            font=("Segoe UI",9))

        # Chat
        ch = tk.Frame(rc, bg=C_BG); ch.pack(fill=tk.BOTH, expand=True)
        ch_hdr = tk.Frame(ch, bg=C_DARK, pady=5); ch_hdr.pack(fill=tk.X)
        tk.Label(ch_hdr, text="◈  INTERFACE DE COMUNICAÇÃO", font=("Segoe UI",9,"bold"),
                 bg=C_DARK, fg=C_CYAN).pack(side=tk.LEFT, padx=12)
        co = tk.Frame(ch, bg=C_PANEL, highlightthickness=1, highlightbackground=C_GLOW)
        co.pack(fill=tk.BOTH, expand=True)
        self.chat_text = scrolledtext.ScrolledText(
            co, wrap=tk.WORD, bg="#0a0b1e", fg=C_TEXT,
            font=FONT_MSG, relief=tk.FLAT, bd=0, padx=16, pady=12,
            insertbackground=C_CYAN, selectbackground=C_GLOW,
            spacing1=2, spacing3=2)
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        self.chat_text.configure(state=tk.DISABLED)
        # Tags de cor
        self.chat_text.tag_config("jarvis",   foreground=C_CYAN)
        self.chat_text.tag_config("user",     foreground=C_GREEN)
        self.chat_text.tag_config("system",   foreground=C_TEXT2)
        self.chat_text.tag_config("error",    foreground=C_RED)
        self.chat_text.tag_config("warn",     foreground=C_AMBER)
        self.chat_text.tag_config("time",     foreground=C_DIM)
        self.chat_text.tag_config("auto",     foreground="#fb923c")
        self.chat_text.tag_config("label_j",  foreground=C_CYAN,  font=("Segoe UI",10,"bold"))
        self.chat_text.tag_config("label_u",  foreground=C_GREEN, font=("Segoe UI",10,"bold"))

    def _build_input(self):
        wrap = tk.Frame(self.root, bg=C_BG, pady=6)
        wrap.pack(fill=tk.X, padx=16, side=tk.BOTTOM)
        inp = tk.Frame(wrap, bg=C_PANEL, highlightthickness=1,
                       highlightbackground=C_GLOW)
        inp.pack(fill=tk.X)
        inn = tk.Frame(inp, bg=C_PANEL, pady=8, padx=12); inn.pack(fill=tk.X)
        tk.Label(inn, text="▶", font=("Segoe UI",12,"bold"),
                 bg=C_PANEL, fg=C_CYAN).pack(side=tk.LEFT, padx=(0,8))
        self.text_input = tk.Entry(
            inn, bg=C_PANEL, fg=C_WHITE, insertbackground=C_CYAN,
            font=("Segoe UI",11), relief=tk.FLAT, bd=0,
            disabledbackground=C_PANEL, disabledforeground=C_DIM)
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.text_input.bind("<Return>", self.send_text)
        self.text_input.insert(0, "Aguardando conexão, Chefe...")
        self.text_input.bind("<FocusIn>", lambda e:
            self.text_input.get().startswith("Aguard") and self.text_input.delete(0, tk.END))
        self.text_input.configure(state=tk.DISABLED)
        self.send_btn = self._btn(inn, "ENVIAR", self.send_text, state=tk.DISABLED)
        self.send_btn.pack(side=tk.RIGHT, padx=(10,0))

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=C_DARK, pady=4)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(bar, text="  ◈ JARVIS v6.0  —  Groq AI  —  Automação Ativa",
                 font=("Segoe UI",7), bg=C_DARK, fg=C_DIM).pack(side=tk.LEFT)
        self.lbl_status = tk.Label(bar, text="OFFLINE",
            font=("Segoe UI",7,"bold"), bg=C_DARK, fg=C_RED)
        self.lbl_status.pack(side=tk.RIGHT, padx=12)

    def _pill(self, p, t, c):
        lbl = tk.Label(p, text=t, bg=C_DARK, fg=c,
                       font=("Segoe UI",8,"bold"), padx=10, pady=4,
                       highlightthickness=1, highlightbackground=c)
        return lbl

    def _sl(self, p, t):
        f = tk.Frame(p, bg=C_BG); f.pack(fill=tk.X, pady=(8,3))
        tk.Label(f, text=t, font=("Segoe UI",8,"bold"),
                 bg=C_BG, fg=C_GLOW).pack(side=tk.LEFT)
        c = tk.Canvas(f, bg=C_BG, height=1, highlightthickness=0)
        c.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6,0))
        c.bind("<Configure>", lambda e: (c.delete("all"),
            c.create_line(0,0,c.winfo_width(),0,fill=C_DIM,width=1)))

    def _card(self, p):
        return tk.Frame(p, bg=C_PANEL, pady=10, padx=12,
                        highlightthickness=1, highlightbackground=C_GLOW)

    def _btn(self, p, t, cmd, state=tk.NORMAL, color=None):
        col = color or C_CYAN
        b = tk.Button(p, text=t, command=cmd, bg=C_DARK, fg=col,
            activebackground=C_GLOW, activeforeground=C_WHITE,
            relief=tk.FLAT, bd=0, font=FONT_BTN, padx=10, pady=6,
            state=state, cursor="hand2",
            highlightthickness=1, highlightbackground=C_DIM)
        b.bind("<Enter>", lambda e: b.config(bg=C_GLOW, fg=C_WHITE, highlightbackground=col))
        b.bind("<Leave>", lambda e: b.config(bg=C_DARK, fg=col, highlightbackground=C_DIM))
        return b

    def _update_clock(self):
        now=datetime.now()
        self.lbl_time.config(text=f"⏱ {now:%H:%M:%S}")
        self.lbl_sess.config(text=f"📅 {now:%d/%m/%Y} | Sessão #{self.memory.get('sessions_count',0)}")
        self.root.after(1000,self._update_clock)

    # ── Conexão ──────────────────────────────────────────────────────
    def connect(self):
        key=self.api_entry.get().strip()
        if not key or "•" in key:
            messagebox.showerror("JARVIS","Insira sua API Key do Groq.\nconsole.groq.com → API Keys"); return
        self.log("◈ Conectando ao Groq...","system")
        self.connect_btn.config(text="[ CONECTANDO... ]",state=tk.DISABLED)
        threading.Thread(target=self._try_connect,args=(key,),daemon=True).start()

    def _try_connect(self,key):
        try:
            self.client=Groq(api_key=key)
            self.client.chat.completions.create(model="llama-3.3-70b-versatile",max_tokens=5,messages=[{"role":"user","content":"hi"}])
            self.root.after(0,self._on_connected,key)
        except Exception as e: self.root.after(0,self._on_error,str(e))

    def _on_connected(self,key):
        self.is_connected=True; self.config["api_key"]=key; save_config(self.config)
        self.memory["sessions_count"]=self.memory.get("sessions_count",0)+1
        self.memory["last_session"]=datetime.now().isoformat(); save_memory(self.memory)
        self.pill_api.config(text="⬤ ONLINE",fg=C_GREEN)
        self.lbl_status.config(text="ONLINE",fg=C_GREEN)
        self.connect_btn.config(text="[ ✓ GROQ ]",fg=C_GREEN)
        for w in [self.screen_btn,self.mic_btn,self.send_btn]: w.config(state=tk.NORMAL)
        self.text_input.configure(state=tk.NORMAL); self.text_input.delete(0,tk.END)
        threading.Thread(target=self._startup_greeting,daemon=True).start()

    def _on_error(self,err):
        self.connect_btn.config(text="[ CONECTAR ]",state=tk.NORMAL)
        self.log(f"✗ {err}","error")
        messagebox.showerror("Erro",f"Falha:\n{err}\n\nconsole.groq.com")

    def _startup_greeting(self):
        try:
            g=get_greeting(); s=self.memory.get("sessions_count",1)
            r=self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",max_tokens=100,
                messages=[{"role":"system","content":SYSTEM_PROMPT},
                          {"role":"user","content":f"{g}! Sessão {s}. Saudação curta ao Chefe, 1-2 frases. Jarvis do Homem de Ferro."}])
            reply=r.choices[0].message.content
            self.root.after(0,self.log,f"JARVIS: {reply}","jarvis")
            self.speak(reply); log_conv("JARVIS",reply)
        except Exception as e: self.root.after(0,self.log,f"✗ {e}","error")

    def _toggle_autostart(self):
        en=self.autostart_var.get()
        if set_autostart(en):
            self.config["autostart"]=en; save_config(self.config)
            self.log(f"◈ Autostart {'ativado' if en else 'desativado'}.","system")

    # ── Tela ─────────────────────────────────────────────────────────
    def toggle_screen(self):
        if not self.is_screen_on:
            self.is_screen_on=True
            self.screen_btn.config(text="[ ⏹ PARAR TELA ]",fg=C_RED)
            self.pill_screen.config(text="⬤ TELA ON",fg=C_GREEN)
            self.lbl_fps.config(text="● ATIVO",fg=C_GREEN)
            threading.Thread(target=self._screen_loop,daemon=True).start()
            self.log("◈ Feed de tela ativado.","system")
        else:
            self.is_screen_on=False
            self.screen_btn.config(text="[ 📺 INICIAR TELA ]",fg=C_CYAN)
            self.pill_screen.config(text="⬤ TELA OFF",fg=C_DIM)
            self.lbl_fps.config(text="● INATIVO",fg=C_DIM)
            self.preview_canvas.delete("all")
            self._preview_img_id=None
            self.preview_canvas.create_text(400,100,text="── Captura de tela inativa ──",fill=C_DIM,font=FONT_SUB)
            self.latest_ss_b64=None
            self.log("◈ Feed desativado.","system")

    def _screen_loop(self):
        with mss.mss() as sct:
            mon=sct.monitors[0]; t_api=0
            while self.is_screen_on:
                try:
                    t0=time.time()
                    shot=sct.grab(mon)
                    img=Image.frombytes("RGB",shot.size,shot.bgra,"raw","BGRX")
                    # Preview — escala para preencher o canvas
                    cw=self.preview_canvas.winfo_width() or 800
                    ch=200
                    pv=img.copy(); pv.thumbnail((cw, ch))
                    ph=ImageTk.PhotoImage(pv)
                    self.preview_canvas.delete("all")
                    self.preview_canvas.create_image(cw//2, ch//2, image=ph, anchor="center")
                    self.preview_canvas._img_ref=ph  # evita garbage collection
                    # Imagem API a cada 1.5s
                    now=time.time()
                    if now-t_api>=1.5:
                        ai=img.copy(); ai.thumbnail((960,540))
                        buf=io.BytesIO(); ai.save(buf,format="JPEG",quality=60)
                        self.latest_ss_b64=base64.b64encode(buf.getvalue()).decode()
                        t_api=now
                    time.sleep(max(0,0.35-(time.time()-t0)))
                except Exception as e:
                    self.root.after(0,self.log,f"✗ Tela: {e}","error"); time.sleep(1)



    # ── Lista e seleciona dispositivo de microfone ───────────────────
    def _refresh_mic_list(self):
        try:
            pa = pyaudio.PyAudio()
            devices = {}
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    name = info["name"]
                    # Filtra dispositivos de loopback/stereo mix
                    skip_keywords = ["stereo mix","wave out","what u hear","loopback",
                                     "mixagem estéreo","o que ouve","virtual","vb-audio","voicemeeter"]
                    is_loopback = any(kw in name.lower() for kw in skip_keywords)
                    label = f"{'⚠ ' if is_loopback else ''}{name[:30]}"
                    devices[label] = i
            pa.terminate()

            if not devices:
                return

            menu = self.mic_combo["menu"]
            menu.delete(0, "end")
            cfg_device = self.config.get("mic_device_name","")

            best_idx  = None
            best_label= None
            for label, idx in devices.items():
                menu.add_command(label=label,
                    command=lambda l=label,i=idx: self._select_mic(l,i))
                # Auto-seleciona o salvo ou o primeiro sem ⚠
                if cfg_device and cfg_device in label:
                    best_idx=idx; best_label=label
                elif best_idx is None and not label.startswith("⚠"):
                    best_idx=idx; best_label=label

            if best_label:
                self._select_mic(best_label, best_idx)
        except Exception as e:
            self.log(f"✗ Dispositivos: {e}","error")

    def _select_mic(self, label, idx):
        self.mic_device_var.set(label)
        self._mic_device_idx = idx
        self.config["mic_device_name"] = label
        save_config(self.config)
        self.log(f"◈ Mic: {label.strip()}","system")

        # ── Mute microfone do sistema ────────────────────────────────────
    def _set_mic_mute(self, mute: bool):
        if HAS_PYCAW:
            try:
                devices = AudioUtilities.GetMicrophone()
                if devices:
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    vol = cast(interface, POINTER(IAudioEndpointVolume))
                    vol.SetMute(1 if mute else 0, None)
                    return
            except: pass
        try:
            val="true" if mute else "false"
            subprocess.run(f'powershell -c "Get-AudioDevice -Microphone | Set-AudioDevice -Mute {val}" 2>nul',
                           shell=True,capture_output=True,timeout=1)
        except: pass

    # ── Capturar hotkey — teclado OU botão do mouse ─────────────────
    def _capture_hotkey(self, key_id, lbl):
        if not HAS_KEYBOARD:
            self.log("✗ Instale: py -3.11 -m pip install keyboard pynput","error"); return
        lbl.config(text="...", bg=C_AMBER, fg=C_BG)
        self.root.update()
        captured = [False]

        def save_and_update(key_name):
            if captured[0]: return
            captured[0] = True
            if "hotkeys" not in self.config: self.config["hotkeys"] = {}
            self.config["hotkeys"][key_id] = key_name
            save_config(self.config)
            self.root.after(0, lbl.config, {"text": f"[ {key_name} ]", "fg": C_WHITE})
            self.log(f"◈ Hotkey '{key_id}' → {key_name}", "system")
            self.root.after(100, self._start_hotkey_listener)

        # Thread que escuta teclado
        def wait_keyboard():
            try:
                ev = keyboard.read_event(suppress=False)
                if ev.event_type == "down" and not captured[0]:
                    save_and_update(ev.name.upper())
            except: pass

        # Thread que escuta mouse (delay para ignorar o clique que abriu a captura)
        def wait_mouse():
            if not HAS_PYNPUT: return
            time.sleep(0.5)  # aguarda o clique disparador terminar
            if captured[0]: return
            try:
                from pynput import mouse as _m
                _names = {
                    _m.Button.left:   "MOUSE_ESQ",
                    _m.Button.right:  "MOUSE_DIR",
                    _m.Button.middle: "MOUSE_MEIO",
                    _m.Button.x1:     "MOUSE4",
                    _m.Button.x2:     "MOUSE5",
                }
                def on_click(x, y, button, pressed):
                    if pressed and not captured[0]:
                        name = _names.get(button, str(button).split(".")[-1].upper())
                        save_and_update(name)
                        return False
                with _m.Listener(on_click=on_click) as lst:
                    lst.join()
            except: pass

        threading.Thread(target=wait_keyboard, daemon=True).start()
        threading.Thread(target=wait_mouse,    daemon=True).start()

    # ── Registrar todos os hotkeys (teclado + mouse) ────────────────
    def _start_hotkey_listener(self):
        # ── Teclado ──
        if HAS_KEYBOARD:
            try: keyboard.unhook_all_hotkeys()
            except: pass
            hk = self.config.get("hotkeys", {})
            actions = {
                "interromper": self.interrupt_jarvis,
                "mic_toggle":  self.toggle_mic,
                "tela_toggle": self.toggle_screen,
                "mute_jarvis": self._toggle_jarvis_mute,
            }
            for key_id, fn in actions.items():
                key_name = hk.get(key_id, "")
                if key_name and key_name != "—" and not key_name.startswith("MOUSE"):
                    try: keyboard.add_hotkey(key_name.lower(), fn, suppress=False)
                    except: pass

        # ── Mouse (botões laterais e extras via pynput) ──
        if HAS_PYNPUT:
            from pynput import mouse as _pm
            if hasattr(self, '_mouse_listener') and self._mouse_listener:
                try: self._mouse_listener.stop()
                except: pass

            hk = self.config.get("hotkeys", {})
            BUTTON_MAP = {
                "MOUSE_ESQ":  _pm.Button.left,
                "MOUSE_DIR":  _pm.Button.right,
                "MOUSE_MEIO": _pm.Button.middle,
                "MOUSE4":     _pm.Button.x1,
                "MOUSE5":     _pm.Button.x2,
            }
            actions = {
                "interromper": self.interrupt_jarvis,
                "mic_toggle":  self.toggle_mic,
                "tela_toggle": self.toggle_screen,
                "mute_jarvis": self._toggle_jarvis_mute,
            }
            mouse_bindings = {}
            for key_id, fn in actions.items():
                key_name = hk.get(key_id, "")
                if key_name in BUTTON_MAP:
                    mouse_bindings[BUTTON_MAP[key_name]] = fn

            if mouse_bindings:
                def on_click(x, y, button, pressed):
                    if pressed and button in mouse_bindings:
                        threading.Thread(target=mouse_bindings[button], daemon=True).start()

                self._mouse_listener = _pm.Listener(on_click=on_click)
                self._mouse_listener.daemon = True
                self._mouse_listener.start()

    # ── Mutar/desmutar Jarvis sem parar fala ─────────────────────────
    def _toggle_jarvis_mute(self):
        self.jarvis_muted = not self.jarvis_muted
        try: pygame.mixer.music.set_volume(0.0 if self.jarvis_muted else 0.95)
        except: pass
        state = "🔇 MUTADO" if self.jarvis_muted else "🔊 ATIVO"
        self.root.after(0, self.log, f"◈ Jarvis {state}","system")

        # ── Interromper Jarvis (botão) ────────────────────────────────────
    def interrupt_jarvis(self):
        if self.is_speaking:
            self._stop_speaking(interrupted=True)
            self.log("◈ Interrompido.","warn")
            self.interrupt_btn.config(state=tk.DISABLED)
            if self.is_mic_on:
                self.pill_mic.config(text="⬤ OUVINDO...",fg=C_GREEN)

    # ── Microfone ────────────────────────────────────────────────────
    def toggle_mic(self):
        if not self.is_mic_on:
            # Garante que nenhuma thread anterior ainda esta rodando
            if getattr(self, '_listen_thread', None) and self._listen_thread.is_alive():
                self.log("◈ Aguardando thread anterior encerrar...","system")
                self.is_mic_on=False
                self._listen_thread.join(timeout=2)
            self.is_mic_on=True
            self.mic_btn.config(text="[ ⏹ PARAR VOZ ]",fg=C_RED)
            self.pill_mic.config(text="⬤ MIC ON",fg=C_GREEN)
            self._listen_thread=threading.Thread(target=self._listen_loop,daemon=True)
            self._listen_thread.start()
            self.log("◈ Microfone ativado. Pode falar, Chefe.","system")
        else:
            self.is_mic_on=False
            self._set_mic_mute(False)
            self.mic_btn.config(text="[ 🎤 INICIAR VOZ ]",fg=C_CYAN)
            self.pill_mic.config(text="⬤ MIC OFF",fg=C_DIM)
            self.interrupt_btn.config(state=tk.DISABLED)
            self.log("◈ Microfone desativado.","system")

    def _listen_loop(self):
        """Loop de escuta limpo — sem PyAudio separado, sem spam de erros."""
        recognizer = sr.Recognizer()
        dev = self._mic_device_idx

        # Testa o device; se falhar usa o padrão
        try:
            with sr.Microphone(device_index=dev, sample_rate=16000) as _t:
                pass
        except Exception:
            self.log("◈ Device selecionado falhou — usando mic padrão","warn")
            dev = None

        try:
            with sr.Microphone(device_index=dev, sample_rate=16000) as mic:
                self.log("◈ Calibrando microfone...","system")
                recognizer.adjust_for_ambient_noise(mic, duration=2)
                recognizer.energy_threshold         = max(recognizer.energy_threshold * 1.8, 1500)
                recognizer.dynamic_energy_threshold = False
                recognizer.pause_threshold          = 2.0
                recognizer.non_speaking_duration    = 1.8
                recognizer.phrase_threshold         = 0.4
                self.log(f"◈ Limiar: {recognizer.energy_threshold:.0f} | Pronto!","system")

                while self.is_mic_on:
                    # ── Jarvis falando — aguarda ──────────────────────────
                    if self.is_speaking:
                        self._set_mic_mute(True)
                        key = self.config.get("hotkeys",{}).get("interromper","F9")
                        self.pill_mic.config(text=f"⬤ MIC MUTADO  [{key}] p/ interromper",fg=C_AMBER)
                        self.root.after(0, self.interrupt_btn.config, {"state":tk.NORMAL})
                        while self.is_speaking and self.is_mic_on:
                            time.sleep(0.05)
                        self._set_mic_mute(False)
                        self.root.after(0, self.interrupt_btn.config, {"state":tk.DISABLED})
                        continue

                    # ── Drena eco após Jarvis falar ───────────────────────
                    if self._just_spoke:
                        self.pill_mic.config(text="⬤ AGUARDANDO ECO...",fg=C_DIM)
                        time.sleep(0.4)
                        self._just_spoke = False
                        try: recognizer.adjust_for_ambient_noise(mic, duration=0.5)
                        except: pass
                        self.pill_mic.config(text="⬤ OUVINDO...",fg=C_GREEN)
                        continue

                    # (continua ouvindo mesmo processando — fala vai para a fila)

                    # ── Escuta ────────────────────────────────────────────
                    try:
                        self.pill_mic.config(text="⬤ OUVINDO...",fg=C_GREEN)
                        audio = recognizer.listen(mic, timeout=6, phrase_time_limit=60)
                        if self.is_speaking: continue
                        # Countdown visual de 2s de silêncio
                        for remaining in [2, 1]:
                            self.pill_mic.config(text=f"⬤ SILÊNCIO... {remaining}s",fg=C_AMBER)
                            time.sleep(0.5)
                        self.pill_mic.config(text="⬤ ENVIANDO...",fg=C_CYAN)
                        text = recognizer.recognize_google(audio, language="pt-BR")
                        if text.strip() and len(text.strip()) >= 3:
                            self.root.after(0, self.log, f"Chefe: {text}", "user")
                            self.process_input(text)
                    except sr.WaitTimeoutError:
                        pass
                    except sr.UnknownValueError:
                        pass
                    except OSError:
                        # Stream fechado — sai do loop silenciosamente
                        break
                    except Exception as e:
                        if "Stream" in str(e) or "closed" in str(e).lower():
                            break  # sai sem spam
                        self.root.after(0,self.log,f"✗ {e}","error")
                        time.sleep(1)

        except Exception as e:
            if self.is_mic_on:  # só loga se não foi desligado propositalmente
                self.root.after(0,self.log,f"✗ Microfone: {e}","error")
        finally:
            self.is_mic_on = False
            self._set_mic_mute(False)
            self.root.after(0, self.mic_btn.config,  {"text":"[ 🎤 INICIAR VOZ ]","fg":C_CYAN})
            self.root.after(0, self.pill_mic.config,  {"text":"⬤ MIC OFF","fg":C_DIM})
            self.root.after(0, self.interrupt_btn.config, {"state":tk.DISABLED})

    # ── Groq API ─────────────────────────────────────────────────────
    def process_input(self, text):
        if not self.client:
            self.log("✗ Conecte a API Key.","error"); return
        # Enfileira — nunca descarta fala do Chefe
        try:
            self.input_queue.put_nowait(text)
        except queue.Full:
            try: self.input_queue.get_nowait()
            except: pass
            self.input_queue.put_nowait(text)
        # Garante que o worker está rodando
        if not getattr(self, '_worker_running', False):
            threading.Thread(target=self._input_worker, daemon=True).start()

    def _input_worker(self):
        self._worker_running = True
        while True:
            try:
                text = self.input_queue.get(timeout=2)
                self._call_groq(text)
            except queue.Empty:
                # Fila ficou vazia — encerra worker
                self._worker_running = False
                break

    def _call_groq(self,user_text):
        self.is_processing=True
        self.root.after(0,self.lbl_status.config,{"text":"PENSANDO...","fg":C_AMBER})
        try:
            text_lower=user_text.lower()

            # 1️⃣ Tenta automação primeiro
            auto_result=run_automation(text_lower, original_text=user_text)
            if auto_result:
                self.root.after(0, self.log, f"⚡ AUTO: {auto_result}", "auto")

            # 2️⃣ Monta mensagem com contexto de interrupção se houver
            if self.was_interrupted and self.interrupted_text:
                prompt=(f"Você estava falando isso quando o Chefe te interrompeu: \"{self.interrupted_text[:300]}\". "
                        f"O Chefe disse agora: \"{user_text}\". "
                        f"Faça um resumo MUITO breve do que estava falando (1 frase) e depois responda o novo ponto do Chefe. Natural, sem markdown.")
                self.was_interrupted=False
                self.interrupted_text=""
            elif auto_result:
                prompt=(f"Você acaba de executar a seguinte ação no computador do Chefe: {auto_result}. "
                        f"O Chefe pediu: \"{user_text}\". "
                        f"Confirme brevemente o que fez e pergunte se precisa de mais algo. 1-2 frases, natural.")
            else:
                prompt=user_text

            # 3️⃣ Monta conteúdo — sessão atual por padrão, passado só se pedido
            content=[]
            if self.latest_ss_b64 and self.is_screen_on:
                content.append({"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{self.latest_ss_b64}"}})
            content.append({"type":"text","text":prompt})

            # Usa apenas a sessão ATUAL no contexto padrão
            recent = [{"role":m["role"],"content":m["content"]} for m in self.history[-30:]]

            # Injeta histórico passado APENAS se Chefe pedir explicitamente
            past_keywords = ["você lembra","lembra quando","falamos antes","sessão anterior",
                             "da última vez","na outra vez","anteriormente","já falamos",
                             "conversa passada","me disse antes","você me disse"]
            wants_past = any(kw in user_text.lower() for kw in past_keywords)
            if wants_past and self.past_history:
                past_ctx = []
                for m in self.past_history[-10:]:
                    role_label = "Chefe" if m["role"]=="user" else "JARVIS"
                    past_ctx.append(f"{role_label}: {m['content'][:200]}")
                past_summary = "\n".join(past_ctx)
                # Substitui o prompt com contexto histórico
                content = []
                if self.latest_ss_b64 and self.is_screen_on:
                    content.append({"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{self.latest_ss_b64}"}})
                content.append({"type":"text","text":
                    f"[HISTÓRICO DE SESSÕES ANTERIORES — use se relevante:]\n{past_summary}\n\n[MENSAGEM ATUAL:]\n{prompt}"})
            model=("meta-llama/llama-4-scout-17b-16e-instruct"
                   if (self.latest_ss_b64 and self.is_screen_on)
                   else "llama-3.3-70b-versatile")

            msgs=[{"role":"system","content":SYSTEM_PROMPT}]+recent+[{"role":"user","content":content}]

            # 4️⃣ Streaming com fallback de modelos se rate limit
            FALLBACK_MODELS = [
                model,
                "llama-3.1-8b-instant",
                "gemma2-9b-it",
                "mixtral-8x7b-32768",
            ]
            stream = None
            for try_model in FALLBACK_MODELS:
                try:
                    stream = self.client.chat.completions.create(
                        model=try_model, max_tokens=500, stream=True,
                        messages=msgs, temperature=0.85)
                    if try_model != model:
                        self.root.after(0,self.log,f"◈ Fallback: {try_model}","warn")
                    break
                except Exception as me:
                    err = str(me)
                    if "429" in err or "rate_limit" in err.lower():
                        import re as _re
                        w = _re.search(r"try again in ([\w.]+)", err)
                        msg = f"⚠ Limite em {try_model}" + (f" — aguarde {w.group(1)}" if w else "") + ". Próximo modelo..."
                        self.root.after(0,self.log,msg,"warn")
                        continue
                    raise

            if not stream:
                self.root.after(0,self.log,"✗ Todos os modelos no limite. Tente em alguns minutos.","error")
                return

            ts=datetime.now().strftime("%H:%M:%S")
            self.root.after(0,self._stream_start,ts)
            full=""

            for chunk in stream:
                d=chunk.choices[0].delta.content
                if d:
                    full+=d
                    self.root.after(0,self._stream_append,d)

            self.root.after(0,self._stream_end)

            if full.strip():
                self.speak(full)

        except Exception as e: self.root.after(0,self.log,f"✗ Groq: {e}","error")
        finally:
            self.is_processing=False
            self.root.after(0,self.lbl_status.config,{"text":"ONLINE","fg":C_GREEN})

    def _stream_start(self,ts):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END,f"\n[{ts}] ","time")
        self.chat_text.insert(tk.END,"JARVIS ▸ ","label_j")
        self.chat_text.configure(state=tk.DISABLED)

    def _stream_append(self,d):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END,d,"jarvis")
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def _stream_end(self):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END,"\n","jarvis")
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    # ── TTS ──────────────────────────────────────────────────────────
    def _setup_tts(self):
        try: pygame.mixer.init(frequency=22050,size=-16,channels=1,buffer=512); self.tts_ready=True
        except Exception as e: print(f"TTS init: {e}")

    def _start_tts_thread(self):
        threading.Thread(target=self._tts_loop,daemon=True).start()

    def speak(self,text):
        if self.tts_ready:
            clean=clean_tts(text)
            if clean.strip(): self.speech_queue.put(clean)

    def _stop_speaking(self, interrupted=False):
        if interrupted and self.current_speech_text:
            self.was_interrupted=True
            self.interrupted_text=self.current_speech_text
        try: pygame.mixer.music.stop()
        except: pass
        self.is_speaking=False
        self.current_speech_text=""
        while not self.speech_queue.empty():
            try: self.speech_queue.get_nowait()
            except: break

    def _tts_loop(self):
        loop=asyncio.new_event_loop(); asyncio.set_event_loop(loop)
        while True:
            try:
                text=self.speech_queue.get(timeout=0.5)
                self.is_speaking=True
                self.current_speech_text=text
                self.root.after(0,self.pill_mic.config,{"text":"⬤ PODE INTERROMPER","fg":C_AMBER})
                loop.run_until_complete(self._speak_async(text))
                self.is_speaking=False
                self.current_speech_text=""
                self._just_spoke=True
                if self.is_mic_on:
                    self.root.after(0,self.pill_mic.config,{"text":"⬤ OUVINDO...","fg":C_GREEN})
            except queue.Empty: pass
            except Exception as e: self.is_speaking=False; print(f"TTS: {e}")

    async def _speak_async(self,text):
        try:
            com=edge_tts.Communicate(text,voice=self.JARVIS_VOICE,rate=self.JARVIS_RATE,pitch=self.JARVIS_PITCH)
            with tempfile.NamedTemporaryFile(suffix=".mp3",delete=False) as f: tp=f.name
            await com.save(tp)
            if not self.is_speaking:
                try: os.unlink(tp)
                except: pass
                return
            pygame.mixer.music.load(tp)
            pygame.mixer.music.set_volume(0.95)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if not self.is_speaking: pygame.mixer.music.stop(); break
                await asyncio.sleep(0.04)
            pygame.mixer.music.unload()
            try: os.unlink(tp)
            except: pass
        except Exception as e: print(f"TTS speak: {e}")

    # ── Chat ─────────────────────────────────────────────────────────
    def log(self,message,tag="system"):
        ts=datetime.now().strftime("%H:%M:%S")
        self.chat_text.configure(state=tk.NORMAL)
        if tag=="jarvis":
            self.chat_text.insert(tk.END,f"\n[{ts}] ","time")
            self.chat_text.insert(tk.END,"JARVIS ▸ ","label_j")
            self.chat_text.insert(tk.END,message.replace("JARVIS: ","",1)+"\n","jarvis")
        elif tag=="user":
            self.chat_text.insert(tk.END,f"\n[{ts}] ","time")
            self.chat_text.insert(tk.END,"CHEFE  ▸ ","label_u")
            self.chat_text.insert(tk.END,message.replace("Chefe: ","",1)+"\n","user")
        else:
            self.chat_text.insert(tk.END,f"[{ts}] ","time")
            self.chat_text.insert(tk.END,message+"\n",tag)
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def clear_chat(self):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.delete("1.0",tk.END)
        self.chat_text.configure(state=tk.DISABLED)
        self.history=[]; save_history([])
        self.log("◈ Chat e memória limpos.","system")

    def send_text(self,event=None):
        text=self.text_input.get().strip()
        if not text or text.startswith("Aguard"): return
        self.text_input.delete(0,tk.END)
        self.log(f"Chefe: {text}","user")
        self.process_input(text)

    # ── Run ──────────────────────────────────────────────────────────
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW",self._on_close)
        self.log("◈ JARVIS v5.0 — Groq AI + Automação","system")
        self.log("◈ Insira sua API Key e clique CONECTAR","system")
        self.log("◈ Histórico salvo em: "+str(APP_DIR),"system")
        self.root.mainloop()

    def _on_close(self):
        self.is_screen_on=False; self.is_mic_on=False
        # Salva sessão atual no histórico persistente
        merged = self.past_history + self.history
        save_memory(self.memory); save_history(merged)
        time.sleep(0.15); self.root.destroy()

if __name__=="__main__":
    JarvisApp().run()
