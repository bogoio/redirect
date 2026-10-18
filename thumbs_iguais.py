#!/usr/bin/env python3
"""
Encontra vídeos com thumbnails iguais (ou quase iguais).

Para cada vídeo, extrai um frame com ffmpeg (por padrão a 10% da duração),
calcula um hash perceptual (dHash) e agrupa os vídeos cujos hashes diferem
em no máximo N bits.

Requisitos:
  - ffmpeg e ffprobe no PATH  (https://ffmpeg.org/download.html)
  - pip install pillow

Uso:
  python thumbs_iguais.py "D:\\Videos" "E:\\Outros"
  python thumbs_iguais.py C:\\ --tolerancia 4 --posicao 0.05 --saida relatorio.txt

No Windows, ao final abre a pasta "resultado_thumbs" com atalhos para os
vídeos repetidos, nomeados "G0001 - ...", "G0002 - ...". Use a exibição
Ícones grandes para comparar as thumbs. Os vídeos originais não são mexidos.
"""
import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image
import io

EXTENSOES = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
             ".mpg", ".mpeg", ".3gp", ".ts", ".m2ts", ".vob"}


def listar_videos(pastas):
    for pasta in pastas:
        for raiz, _, arquivos in os.walk(pasta):
            for nome in arquivos:
                if os.path.splitext(nome)[1].lower() in EXTENSOES:
                    yield os.path.join(raiz, nome)


def duracao(caminho):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", caminho],
        capture_output=True, text=True, timeout=60)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def extrair_frame(caminho, posicao):
    t = duracao(caminho) * posicao
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", caminho,
         "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, timeout=120)
    if not r.stdout:
        return None
    return Image.open(io.BytesIO(r.stdout))


def dhash(img, tamanho=8):
    img = img.convert("L").resize((tamanho + 1, tamanho), Image.LANCZOS)
    px = list(img.getdata())
    bits = 0
    for y in range(tamanho):
        for x in range(tamanho):
            i = y * (tamanho + 1) + x
            bits = (bits << 1) | (px[i] > px[i + 1])
    return bits


def processar(caminho, posicao):
    try:
        img = extrair_frame(caminho, posicao)
        return caminho, (dhash(img) if img else None)
    except Exception as e:
        print(f"  erro em {caminho}: {e}", file=sys.stderr)
        return caminho, None


def agrupar(hashes, tolerancia):
    # union-find simples
    pai = list(range(len(hashes)))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    for i in range(len(hashes)):
        for j in range(i + 1, len(hashes)):
            if bin(hashes[i][1] ^ hashes[j][1]).count("1") <= tolerancia:
                pai[raiz(i)] = raiz(j)

    grupos = {}
    for i, (caminho, _) in enumerate(hashes):
        grupos.setdefault(raiz(i), []).append(caminho)
    return [g for g in grupos.values() if len(g) > 1]


def main():
    ap = argparse.ArgumentParser(description="Busca vídeos com thumbnails iguais.")
    ap.add_argument("pastas", nargs="+", help="pastas a varrer (recursivo)")
    ap.add_argument("--tolerancia", type=int, default=5,
                    help="bits de diferença aceitos (0 = idêntico; padrão 5)")
    ap.add_argument("--posicao", type=float, default=0.10,
                    help="ponto do vídeo usado como thumb, 0 a 1 (padrão 0.10)")
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--saida", help="salvar relatório num arquivo .txt")
    ap.add_argument("--pasta-resultado", default="resultado_thumbs",
                    help="pasta onde ficam os atalhos agrupados (Windows)")
    args = ap.parse_args()

    videos = list(listar_videos(args.pastas))
    print(f"{len(videos)} vídeos encontrados. Extraindo thumbs...")

    hashes = []
    with ThreadPoolExecutor(args.threads) as ex:
        for n, (caminho, h) in enumerate(
                ex.map(lambda v: processar(v, args.posicao), videos), 1):
            if h is not None:
                hashes.append((caminho, h))
            print(f"\r  {n}/{len(videos)}", end="", flush=True)
    print()

    grupos = agrupar(hashes, args.tolerancia)
    linhas = []
    for k, g in enumerate(grupos, 1):
        linhas.append(f"\nGrupo {k} ({len(g)} vídeos):")
        for c in sorted(g):
            tam = os.path.getsize(c) / 1024 / 1024
            linhas.append(f"  {tam:10.1f} MB  {c}")
    linhas.append(f"\n{len(grupos)} grupos com thumbs iguais.")
    texto = "\n".join(linhas)
    print(texto)

    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"Relatório salvo em {args.saida}")

    if grupos and os.name == "nt":
        criar_atalhos(grupos, os.path.abspath(args.pasta_resultado))


def criar_atalhos(grupos, pasta):
    """Cria uma pasta com atalhos para os vídeos, nomeados por grupo, para
    ver no Explorer como uma busca (exibição em Ícones grandes)."""
    os.makedirs(pasta, exist_ok=True)
    for nome in os.listdir(pasta):
        if nome.lower().endswith(".lnk"):
            os.remove(os.path.join(pasta, nome))

    def ps(s):
        return "'" + s.replace("'", "''") + "'"

    linhas = ["$sh = New-Object -ComObject WScript.Shell"]
    for k, g in enumerate(grupos, 1):
        for n, c in enumerate(sorted(g), 1):
            nome = f"G{k:04d}-{n} - {os.path.basename(c)}"[:150] + ".lnk"
            linhas.append(f"$l = $sh.CreateShortcut({ps(os.path.join(pasta, nome))})")
            linhas.append(f"$l.TargetPath = {ps(c)}")
            linhas.append("$l.Save()")

    script = os.path.join(pasta, "_criar_atalhos.ps1")
    with open(script, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(linhas))
    print("Criando atalhos...")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", script])
    os.remove(script)
    print(f"Pronto. Abrindo {pasta}")
    os.startfile(pasta)


if __name__ == "__main__":
    main()
