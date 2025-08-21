from dotenv import load_dotenv
import os
import time
from getpass import getpass
from pathlib import Path

import instaloader
from instaloader.exceptions import TwoFactorAuthRequiredException, BadCredentialsException, ConnectionException
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from PIL import Image, UnidentifiedImageError
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import numpy as np

# ================= CONFIGURAÇÃO =================
load_dotenv()
USUARIO = os.getenv("IG_USERNAME")
SENHA = os.getenv("IG_PASSWORD")  # opcional; se None, será solicitado
LOGO_PATH = "logo_evento.png"
PASTA_ORIG = Path("stories")
PASTA_SAIDA = Path("stories_processados")
MARGEM_PX = 30
FATOR_LARGURA_LOGO = 1 / 3

USUARIOS = [
    "educa_drones",
    "dronesguanambi",
    "ceteia_ifbaiano"
]
# ==================================================

def carregar_logo():
    if not Path(LOGO_PATH).exists():
        print(f"❌ Logo não encontrada em {LOGO_PATH}. Coloque um PNG 2:1 vertical nesse caminho.")
        exit(1)
    return Image.open(LOGO_PATH).convert("RGBA")


def login_instagram(L: instaloader.Instaloader):
    SESSOES_DIR = Path(".insta_sessions")
    SESSOES_DIR.mkdir(exist_ok=True)
    sess_file = SESSOES_DIR / f"{USUARIO}.session"

    if sess_file.exists():
        try:
            L.load_session_from_file(USUARIO, str(sess_file))
            print("🔐 Sessão carregada com sucesso.")
            return
        except Exception:
            print("ℹ️ Não foi possível carregar a sessão existente. Tentando login...")

    senha = SENHA or getpass("Senha do Instagram: ")

    try:
        L.login(USUARIO, senha)
        print("🔑 Login efetuado sem 2FA.")
    except TwoFactorAuthRequiredException:
        code = input("Digite o código 2FA: ").strip()
        L.two_factor_login(code)
        print("🔑 Login com 2FA concluído.")
    except BadCredentialsException:
        print("❌ Credenciais inválidas (usuário/senha).")
        exit(1)
    except ConnectionException as e:
        print(f"❌ Erro de conexão: {e}")
        exit(1)

    try:
        L.save_session_to_file(str(sess_file))
        print(f"💾 Sessão salva em {sess_file}")
    except Exception as e:
        print(f"⚠️ Não foi possível salvar a sessão: {e}")

def baixar_stories(L: instaloader.Instaloader, logo_img: Image.Image):
    for username in USUARIOS:
        try:
            perfil = instaloader.Profile.from_username(L.context, username)
            print(f"\n👤 Usuário: {perfil.username} (id {perfil.userid})")

            user_dir = PASTA_ORIG
            user_dir.mkdir(parents=True, exist_ok=True)

            for story in L.get_stories(userids=[perfil.userid]):
                for item in story.get_items():
                    # salva story diretamente na pasta do usuário
                    L.download_storyitem(item, target=str(user_dir))
                    time.sleep(0.5)

                    # identifica último arquivo baixado
                    arquivos = [f for f in user_dir.iterdir() if f.suffix.lower() in [".jpg",".jpeg",".png",".webp",".mp4"]]
                    if not arquivos:
                        print(f"⚠️ Nenhum arquivo encontrado para {username}.")
                        continue
                    arquivo = sorted(arquivos, key=lambda p: p.stat().st_mtime)[-1]

                    saida_processada = ""

                    if item.is_video:
                        saida = PASTA_ORIG / arquivo.name                        
                        arquivo.replace(saida)
                        print(f"🎬 Vídeo baixado: {saida.name}")
                    else:
                        saida = PASTA_ORIG / f"{item.owner_username}_{arquivo.stem}.png"
                        print(f"🖼️ Imagem baixada: {saida.name}")

        except Exception as e:
            print(f"⚠️ Erro ao processar {username}: {e}")

def main():
    logo_img = carregar_logo()

    L = instaloader.Instaloader(
        dirname_pattern=str(PASTA_ORIG),  # evita subpastas extras
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
        max_connection_attempts=3,
        request_timeout=30.0,
        download_geotags=False,
        download_comments=False,
        post_metadata_txt_pattern=""
    )

    print("🔧 Efetuando login / carregando sessão…")
    login_instagram(L)

    print("🚀 Iniciando download de stories dos usuários…")
    baixar_stories(L, logo_img)



    print("\n🎉 Concluído! Arquivos finais em:", PASTA_SAIDA.resolve())

if __name__ == "__main__":
    main()
