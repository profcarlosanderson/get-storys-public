from pathlib import Path
from PIL import Image, UnidentifiedImageError
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import numpy as np

# Constantes
FATOR_LARGURA_LOGO = 1 / 3
MARGEM_PX = 30

# Caminhos
PASTA_STORIES = Path("stories")
PASTA_PROCESSADO = Path("stories_processado")
LOGO_PATH = Path("logo_evento.png")  # caminho para sua logo

def aplicar_logo_arquivo(arquivo_path: Path, logo_img: Image.Image, saida_path: Path):
    try:
        # --- Detectar se é imagem ---
        is_image = True
        try:
            base = Image.open(arquivo_path).convert("RGBA")
        except UnidentifiedImageError:
            is_image = False

        if is_image:
            # ---- TRATAR IMAGEM ----
            largura_logo = max(1, int(base.width * FATOR_LARGURA_LOGO))
            altura_logo = int(largura_logo * (logo_img.height / logo_img.width))
            logo_resized = logo_img.resize((largura_logo, altura_logo))

            pos_x = max(0, base.width - largura_logo - MARGEM_PX)
            pos_y = max(0, base.height - altura_logo - MARGEM_PX)

            base.paste(logo_resized, (pos_x, pos_y), logo_resized)

            saida_path.parent.mkdir(parents=True, exist_ok=True)
            saida_path = saida_path.with_suffix(".png")
            base.save(saida_path, "PNG")
            print(f"✅ Logo aplicada na imagem: {saida_path}")

        else:
            # ---- TRATAR VÍDEO ----
            clip = VideoFileClip(str(arquivo_path))

            # Redimensiona logo proporcional ao vídeo
            largura_logo = max(1, int(clip.w * FATOR_LARGURA_LOGO))
            altura_logo = int(largura_logo * (logo_img.height / logo_img.width))
            logo_resized = logo_img.resize((largura_logo, altura_logo))

            # Converte para array NumPy
            logo_array = np.array(logo_resized)

            # Cria ImageClip do logo
            logo_clip = (ImageClip(logo_array)
                         .set_duration(clip.duration)
                         .set_pos((clip.w - largura_logo - MARGEM_PX,
                                   clip.h - altura_logo - MARGEM_PX)))

            # Compor logo sobre o vídeo
            video_com_logo = CompositeVideoClip([clip, logo_clip])
            saida_path.parent.mkdir(parents=True, exist_ok=True)

            # Força saída em .mp4
            saida_path = saida_path.with_suffix(".mp4")
            video_com_logo.write_videofile(str(saida_path), codec="libx264", audio_codec="aac")
            print(f"✅ Logo aplicada no vídeo: {saida_path}")

    except Exception as e:
        print(f"⚠️ Erro ao aplicar logo em {arquivo_path}: {e}")


def processar_stories():
    # Carrega a logo
    logo_img = Image.open(LOGO_PATH).convert("RGBA")

    # Itera por todos os arquivos da pasta /stories
    for arquivo in PASTA_STORIES.iterdir():
        if arquivo.is_file():
            nome_saida = PASTA_PROCESSADO / arquivo.name
            try:
                aplicar_logo_arquivo(arquivo, logo_img, nome_saida)
            except Exception as e:
                print(f"⚠️ Erro ao processar {arquivo}: {e}")


if __name__ == "__main__":
    processar_stories()
