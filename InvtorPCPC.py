#!/usr/bin/env python3
"""
InvtorPCPC - Software professionale per compressione file e confronto cartelle
Versione 1.0 | Interfaccia in italiano | Target: Linux
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import io
import hashlib
import csv
import shutil
import tempfile
import time
import json
import base64
import re
from pathlib import Path
from datetime import datetime

# ─── Importazioni per compressione immagini ───────────────────────────────────
try:
    from PIL import Image, ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ─── Importazioni per compressione video ─────────────────────────────────────
try:
    import av
    AV_AVAILABLE = True
except ImportError:
    AV_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
#  PALETTE COLORI — Lusso femminile, tutto chiaro, sfumature rosa/pesca/oro
# ═══════════════════════════════════════════════════════════════════════════════
COLORS = {
    # ── Sfondi ──────────────────────────────────────────────────────────────
    "bg_main":        "#FFF8F5",   # Bianco pesca caldissimo
    "bg_panel":       "#FFF0F6",   # Rosa candido
    "bg_card":        "#FFFFFF",   # Bianco puro
    "bg_sidebar":     "#FDF2F8",   # Lavanda rosata chiarissima
    "bg_input":       "#FFF5FA",   # Input quasi bianco rosato
    "bg_log":         "#FDFAFA",   # Log chiaro: panna
    # ── Accenti principali ──────────────────────────────────────────────────
    "accent_primary": "#D4789C",   # Rosa antico profondo (principale)
    "accent_deep":    "#A8487A",   # Rosa bordeaux (hover/attivo)
    "accent_rose":    "#E8A0C0",   # Rosa medio brillante
    "accent_blush":   "#F4C2D8",   # Blush chiaro
    "accent_peach":   "#F9D5C0",   # Pesca chiaro
    "accent_gold":    "#D4A574",   # Oro rosato (accento lusso)
    "accent_lilac":   "#C9A8D4",   # Lilla cipria
    "accent_light":   "#FCE8F3",   # Rosa chiarissimo per sfondi bottoni secondari
    # ── Testi ───────────────────────────────────────────────────────────────
    "text_primary":   "#2D1B2E",   # Quasi nero viola scurissimo
    "text_secondary": "#6B3D5C",   # Viola-bordeaux medio
    "text_muted":     "#C4909E",   # Rosa grigio muted
    "text_light":     "#E8C4D4",   # Testo chiarissimo su scuro
    # ── Bordi e separatori ──────────────────────────────────────────────────
    "border":         "#F0D0E4",   # Bordo rosa chiarissimo
    "border_focus":   "#D4789C",   # Bordo focus (primario)
    "separator":      "#F5D5E8",   # Separatori interni
    # ── Stati ───────────────────────────────────────────────────────────────
    "success":        "#6BAF8A",   # Verde salvia elegante
    "success_bg":     "#EDFAF3",   # Sfondo successo
    "warning":        "#C8935A",   # Ambra calda
    "warning_bg":     "#FDF3E7",   # Sfondo warning
    "error":          "#C06070",   # Rosso antico
    "error_bg":       "#FDF0F0",   # Sfondo errore
    "info":           "#7A9FC0",   # Azzurro grigio
    "info_bg":        "#EEF4FB",   # Sfondo info
    # ── Progresso ───────────────────────────────────────────────────────────
    "progress_bg":    "#F5D8EB",   # Track barra progresso
    "progress_fill":  "#D4789C",   # Fill barra progresso
    "progress_shine": "#E8A0C0",   # Highlight lucido barra
    # ── Log (tema CHIARO) ───────────────────────────────────────────────────
    "log_bg":         "#FDFAFA",   # Sfondo log chiaro panna
    "log_border":     "#F0D0E4",   # Bordo log
    "log_text":       "#3D1F2E",   # Testo log scuro leggibile
    "log_muted":      "#C4909E",   # Testo muted nel log
    "log_success":    "#4A8F6A",   # Verde scuro per successi nel log chiaro
    "log_warning":    "#A06A30",   # Ambra scura per warning
    "log_error":      "#A04050",   # Rosso scuro per errori
    "log_title":      "#D4789C",   # Titoli nel log
    "log_info":       "#5A7A9A",   # Info nel log
    # ── Superfici speciali ───────────────────────────────────────────────────
    "header_grad_start": "#FFF0F6",
    "header_grad_end":   "#FDE8F4",
    "card_shadow":    "#F0D0E4",
}

FONTS = {
    "display":  ("Georgia", 28, "bold"),
    "title":    ("Georgia", 20, "bold"),
    "subtitle": ("Georgia", 13, "italic"),
    "heading":  ("Georgia", 12, "bold"),
    "body":     ("Helvetica Neue", 11),
    "body_b":   ("Helvetica Neue", 11, "bold"),
    "small":    ("Helvetica Neue", 9),
    "small_b":  ("Helvetica Neue", 9, "bold"),
    "mono":     ("Courier New", 10),
    "btn":      ("Georgia", 11, "bold"),
    "btn_sm":   ("Helvetica Neue", 10, "bold"),
    "metric":   ("Georgia", 20, "bold"),
    "metric_sm":("Georgia", 14, "bold"),
}

# ═══════════════════════════════════════════════════════════════════════════════
#  LOGICA BUSINESS — COMPRESSIONE
# ═══════════════════════════════════════════════════════════════════════════════

class CompressoreImmagini:
    """Gestisce la compressione di immagini con Pillow."""

    @staticmethod
    def comprimi_jpg(percorso: Path, qualita: int = 82) -> dict:
        """Comprime un file JPG/JPEG. Restituisce info sull'operazione."""
        risultato = {
            "file": str(percorso),
            "successo": False,
            "dim_originale": 0,
            "dim_finale": 0,
            "riduzione": 0.0,
            "errore": None,
        }
        try:
            dim_orig = percorso.stat().st_size
            risultato["dim_originale"] = dim_orig

            # Backup temporaneo
            backup = percorso.with_suffix(".bak_invtor")
            shutil.copy2(percorso, backup)

            try:
                img = Image.open(percorso)
                # Preserva EXIF se disponibile
                exif_data = None
                try:
                    exif_data = img.info.get("exif")
                except Exception:
                    pass

                # Converti in RGB se necessario
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")

                save_kwargs = {"quality": qualita, "optimize": True, "progressive": True}
                if exif_data:
                    save_kwargs["exif"] = exif_data

                img.save(percorso, "JPEG", **save_kwargs)
                img.close()

                dim_finale = percorso.stat().st_size
                risultato["dim_finale"] = dim_finale

                # Se la compressione ha ingrandito il file, ripristina
                if dim_finale >= dim_orig:
                    shutil.copy2(backup, percorso)
                    risultato["dim_finale"] = dim_orig
                    risultato["successo"] = True
                    risultato["riduzione"] = 0.0
                else:
                    riduzione = (1 - dim_finale / dim_orig) * 100
                    risultato["riduzione"] = riduzione
                    risultato["successo"] = True

                backup.unlink(missing_ok=True)

            except Exception as e:
                # Ripristina da backup
                if backup.exists():
                    shutil.copy2(backup, percorso)
                    backup.unlink(missing_ok=True)
                raise e

        except Exception as e:
            risultato["errore"] = str(e)

        return risultato

    @staticmethod
    def converti_png_in_jpg(percorso: Path, qualita: int = 82) -> dict:
        """Converte PNG in JPG e comprime. Elimina PNG solo se successo."""
        risultato = {
            "file": str(percorso),
            "successo": False,
            "dim_originale": 0,
            "dim_finale": 0,
            "riduzione": 0.0,
            "errore": None,
            "tipo": "png->jpg",
        }
        try:
            dim_orig = percorso.stat().st_size
            risultato["dim_originale"] = dim_orig

            img = Image.open(percorso)
            # Gestione trasparenza: sfondo bianco
            if img.mode in ("RGBA", "LA", "P"):
                sfondo = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                if img.mode in ("RGBA", "LA"):
                    sfondo.paste(img, mask=img.split()[-1])
                else:
                    sfondo.paste(img)
                img = sfondo
            elif img.mode != "RGB":
                img = img.convert("RGB")

            percorso_jpg = percorso.with_suffix(".jpg")
            # Evita sovrascrittura di file .jpg già esistenti con nome identico
            if percorso_jpg.exists():
                percorso_jpg = percorso.with_stem(percorso.stem + "_conv").with_suffix(".jpg")

            img.save(percorso_jpg, "JPEG", quality=qualita, optimize=True, progressive=True)
            img.close()

            dim_finale = percorso_jpg.stat().st_size
            risultato["dim_finale"] = dim_finale
            riduzione = (1 - dim_finale / dim_orig) * 100 if dim_orig > 0 else 0
            risultato["riduzione"] = riduzione
            risultato["successo"] = True
            risultato["file_output"] = str(percorso_jpg)

            # Elimina PNG originale solo se conversione riuscita
            percorso.unlink()

        except Exception as e:
            risultato["errore"] = str(e)

        return risultato


class CompressoreVideo:
    """
    Gestisce la compressione video tramite PyAV o OpenCV.

    Strategia file temporaneo:
    - Viene creato con tempfile.mkstemp() nella stessa cartella del file originale,
      con estensione corretta (.mp4 / .mov). Questo garantisce che FFmpeg/PyAV
      riceva sempre un path con una sola estensione valida, eliminando EINVAL.
    - Il file temporaneo viene rinominato sull'originale solo se la compressione
      ha prodotto un file più piccolo, altrimenti viene eliminato.
    """

    @staticmethod
    def _crea_tmp(percorso: Path) -> Path:
        """
        Crea un file temporaneo vuoto nella stessa directory del file sorgente,
        con la stessa estensione. Restituisce il Path del file creato.
        Usa tempfile.mkstemp per evitare conflitti e path malformati.
        """
        ext = percorso.suffix  # es. ".mp4"
        cartella = str(percorso.parent)
        fd, tmp_path = tempfile.mkstemp(suffix=ext, dir=cartella)
        os.close(fd)  # chiude il file descriptor, il file esiste già su disco
        return Path(tmp_path)

    @staticmethod
    def comprimi_con_pyav(percorso: Path, callback_progresso=None) -> dict:
        """Comprime video con PyAV (H.264 + AAC) mantenendo qualità visiva."""
        risultato = {
            "file": str(percorso),
            "successo": False,
            "dim_originale": 0,
            "dim_finale": 0,
            "riduzione": 0.0,
            "errore": None,
        }
        percorso_tmp = None
        input_container = None
        output_container = None
        try:
            dim_orig = percorso.stat().st_size
            risultato["dim_originale"] = dim_orig

            # File temporaneo con estensione corretta — nessun doppio punto
            percorso_tmp = CompressoreVideo._crea_tmp(percorso)

            # Apre input
            input_container = av.open(str(percorso))

            # Determina formato container di output in base all'estensione
            ext = percorso.suffix.lower().lstrip(".")   # "mp4" o "mov"
            fmt = "mp4" if ext in ("mp4", "mov") else ext

            # Apre output specificando esplicitamente il formato — elimina EINVAL
            output_container = av.open(str(percorso_tmp), mode="w", format=fmt)

            # Totale frame per la barra di progresso
            try:
                video_stream_in = input_container.streams.video[0]
                totale_frame = video_stream_in.frames or 0
            except Exception:
                totale_frame = 0

            frame_count = 0
            stream_map = {}

            for stream in input_container.streams:
                if stream.type == "video":
                    out_stream = output_container.add_stream("libx264", rate=stream.average_rate)
                    out_stream.width = stream.width
                    out_stream.height = stream.height
                    out_stream.pix_fmt = "yuv420p"
                    # Riduce il bitrate del 40%; se non disponibile usa 2 Mbit/s
                    if stream.bit_rate:
                        out_stream.bit_rate = int(stream.bit_rate * 0.6)
                    else:
                        out_stream.bit_rate = 2_000_000
                    out_stream.options = {"crf": "26", "preset": "medium"}
                    stream_map[stream.index] = out_stream

                elif stream.type == "audio":
                    try:
                        out_stream = output_container.add_stream("aac", rate=stream.sample_rate)
                        out_stream.bit_rate = 128_000
                        stream_map[stream.index] = out_stream
                    except Exception:
                        pass  # stream audio non supportato: lo salta senza crash

            # Decode → encode
            for packet in input_container.demux(*list(input_container.streams)):
                if packet.dts is None:
                    continue
                if packet.stream.index not in stream_map:
                    continue
                out_stream = stream_map[packet.stream.index]

                try:
                    if packet.stream.type == "video":
                        for frame in packet.decode():
                            frame_count += 1
                            enc_packets = out_stream.encode(frame)
                            if enc_packets:
                                output_container.mux(enc_packets)
                            if callback_progresso and totale_frame > 0:
                                callback_progresso(frame_count / totale_frame)
                    elif packet.stream.type == "audio":
                        for frame in packet.decode():
                            enc_packets = out_stream.encode(frame)
                            if enc_packets:
                                output_container.mux(enc_packets)
                except Exception:
                    continue  # frame corrotto: lo salta senza interrompere

            # Flush di tutti gli encoder
            for out_stream in stream_map.values():
                try:
                    enc_packets = out_stream.encode(None)
                    if enc_packets:
                        output_container.mux(enc_packets)
                except Exception:
                    pass

            input_container.close()
            input_container = None
            output_container.close()
            output_container = None

            dim_finale = percorso_tmp.stat().st_size
            if dim_finale > 0 and dim_finale < dim_orig:
                shutil.move(str(percorso_tmp), str(percorso))
                percorso_tmp = None
                risultato["dim_finale"] = dim_finale
                risultato["riduzione"] = (1 - dim_finale / dim_orig) * 100
            else:
                risultato["dim_finale"] = dim_orig
                risultato["riduzione"] = 0.0

            risultato["successo"] = True

        except Exception as e:
            risultato["errore"] = str(e)
        finally:
            # Chiude i container se ancora aperti (es. eccezione nel mezzo)
            try:
                if input_container:
                    input_container.close()
            except Exception:
                pass
            try:
                if output_container:
                    output_container.close()
            except Exception:
                pass
            # Pulizia file temporaneo in ogni caso
            if percorso_tmp and percorso_tmp.exists():
                percorso_tmp.unlink(missing_ok=True)

        return risultato

    @staticmethod
    def comprimi_con_opencv(percorso: Path, callback_progresso=None) -> dict:
        """Fallback compressione video con OpenCV."""
        risultato = {
            "file": str(percorso),
            "successo": False,
            "dim_originale": 0,
            "dim_finale": 0,
            "riduzione": 0.0,
            "errore": None,
        }
        percorso_tmp = None
        cap = None
        out = None
        try:
            dim_orig = percorso.stat().st_size
            risultato["dim_originale"] = dim_orig

            cap = cv2.VideoCapture(str(percorso))
            if not cap.isOpened():
                raise RuntimeError("OpenCV non riesce ad aprire il file video")

            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            totale = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # File temporaneo sicuro con la stessa estensione
            percorso_tmp = CompressoreVideo._crea_tmp(percorso)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(percorso_tmp), fourcc, fps, (w, h))

            frame_n = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                frame_n += 1
                if callback_progresso and totale > 0:
                    callback_progresso(frame_n / totale)

            cap.release()
            cap = None
            out.release()
            out = None

            dim_finale = percorso_tmp.stat().st_size
            if dim_finale > 0 and dim_finale < dim_orig:
                shutil.move(str(percorso_tmp), str(percorso))
                percorso_tmp = None
                risultato["dim_finale"] = dim_finale
                risultato["riduzione"] = (1 - dim_finale / dim_orig) * 100
            else:
                risultato["dim_finale"] = dim_orig
                risultato["riduzione"] = 0.0

            risultato["successo"] = True

        except Exception as e:
            risultato["errore"] = str(e)
        finally:
            try:
                if cap:
                    cap.release()
            except Exception:
                pass
            try:
                if out:
                    out.release()
            except Exception:
                pass
            if percorso_tmp and percorso_tmp.exists():
                percorso_tmp.unlink(missing_ok=True)

        return risultato


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGICA BUSINESS — CONFRONTO CARTELLE
# ═══════════════════════════════════════════════════════════════════════════════

class AnalizzatoreCartelle:
    """Analizza e confronta due strutture di cartelle."""

    ESTENSIONI_VIDEO = {".mp4", ".mov"}
    ESTENSIONI_IMMAGINI = {".jpg", ".jpeg", ".png"}

    @staticmethod
    def calcola_hash(percorso: Path, algoritmo: str = "sha256") -> str:
        """Calcola hash SHA256 in streaming (memoria efficiente)."""
        h = hashlib.new(algoritmo)
        try:
            with open(percorso, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def leggi_struttura(cartella: Path, callback=None) -> dict:
        """
        Legge ricorsivamente la struttura di una cartella.
        Restituisce dict: {percorso_relativo: {size, path_assoluto}}
        """
        struttura = {}
        try:
            tutti_file = list(cartella.rglob("*"))
            for i, percorso in enumerate(tutti_file):
                if percorso.is_file():
                    rel = percorso.relative_to(cartella)
                    try:
                        size = percorso.stat().st_size
                    except Exception:
                        size = -1
                    struttura[str(rel)] = {
                        "path": percorso,
                        "size": size,
                    }
                if callback:
                    callback(i, len(tutti_file), str(percorso.name))
        except Exception as e:
            pass
        return struttura

    @staticmethod
    def verifica_integrita_immagine(percorso: Path) -> tuple[bool, str]:
        """Verifica che un'immagine sia leggibile completamente decodificando i dati."""
        if not PIL_AVAILABLE:
            return True, "Pillow non disponibile, verifica saltata"
        
        # Salviamo lo stato originale della flag
        original_flag = ImageFile.LOAD_TRUNCATED_IMAGES
        try:
            # Forza il fallimento se l'immagine è corrotta o troncata
            ImageFile.LOAD_TRUNCATED_IMAGES = False 
            
            with Image.open(percorso) as img:
                # img.verify()  <-- Questo non basta, controlla solo l'header, se però sei masochista bro, abilitalo!
                img.load()    # <-- Forza la decodifica di ogni singolo pixel
            return True, "OK"
        except Exception as e:
            return False, f"Immagine corrotta: {str(e)}"
        finally:
            # Ripristiniamo la flag per non rompere il resto del programma
            ImageFile.LOAD_TRUNCATED_IMAGES = original_flag

    @staticmethod
    def verifica_integrita_video(percorso: Path) -> tuple[bool, str]:
        """Verifica che un video non sia troncato o corrotto."""
        if AV_AVAILABLE:
            try:
                container = av.open(str(percorso))
                # Cerca di leggere qualche frame
                for i, packet in enumerate(container.demux()):
                    if i > 50:
                        break
                container.close()
                return True, "OK"
            except Exception as e:
                return False, str(e)
        elif CV2_AVAILABLE:
            try:
                cap = cv2.VideoCapture(str(percorso))
                if not cap.isOpened():
                    cap.release()
                    return False, "Impossibile aprire il file video"
                ret, _ = cap.read()
                cap.release()
                if ret:
                    return True, "OK"
                return False, "Nessun frame leggibile"
            except Exception as e:
                return False, str(e)
        return True, "Nessuna libreria video disponibile, verifica saltata"

    def confronta(
        self,
        cartella1: Path,
        cartella2: Path,
        verifica_hash: bool = True,
        verifica_integrita: bool = True,
        callback_log=None,
        callback_progresso=None,
        stop_event: threading.Event = None,
    ) -> dict:
        """
        Esegue il confronto completo tra due cartelle.
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "cartella1": str(cartella1),
            "cartella2": str(cartella2),
            "file_identici": [],
            "file_diversi": [],       # stesso nome, contenuto diverso
            "solo_in_1": [],
            "solo_in_2": [],
            "corrotti_1": [],
            "corrotti_2": [],
            "riepilogo": {},
        }

        def log(msg, livello="info"):
            if callback_log:
                callback_log(msg, livello)

        # ── Leggi strutture ──────────────────────────────────────────────────
        log("📂 Lettura struttura Cartella 1...", "info")
        struttura1 = self.leggi_struttura(cartella1)
        log(f"   → {len(struttura1)} file trovati", "success")

        if stop_event and stop_event.is_set():
            return report

        log("📂 Lettura struttura Cartella 2...", "info")
        struttura2 = self.leggi_struttura(cartella2)
        log(f"   → {len(struttura2)} file trovati", "success")

        if stop_event and stop_event.is_set():
            return report

        # ── File presenti solo in una cartella ───────────────────────────────
        chiavi1 = set(struttura1.keys())
        chiavi2 = set(struttura2.keys())

        solo1 = chiavi1 - chiavi2
        solo2 = chiavi2 - chiavi1
        comuni = chiavi1 & chiavi2

        for k in solo1:
            report["solo_in_1"].append(k)
            log(f"⚠️  Solo in Cartella 1: {k}", "warning")

        for k in solo2:
            report["solo_in_2"].append(k)
            log(f"⚠️  Solo in Cartella 2: {k}", "warning")

        # ── Confronto file comuni ─────────────────────────────────────────────
        totale_comuni = len(comuni)
        log(f"\n🔍 Confronto {totale_comuni} file in comune...", "info")

        for i, chiave in enumerate(sorted(comuni)):
            if stop_event and stop_event.is_set():
                break

            info1 = struttura1[chiave]
            info2 = struttura2[chiave]
            p1 = info1["path"]
            p2 = info2["path"]

            if callback_progresso:
                callback_progresso(i / totale_comuni if totale_comuni > 0 else 1)

            # Confronto dimensioni
            if info1["size"] != info2["size"]:
                log(f"📋 Diverso (dimensione): {chiave}", "warning")
                report["file_diversi"].append({
                    "percorso": chiave,
                    "motivo": "dimensione_diversa",
                    "size_1": info1["size"],
                    "size_2": info2["size"],
                })
                continue

            # Confronto hash
            if verifica_hash:
                log(f"   🔐 Hash: {chiave}", "muted")
                h1 = self.calcola_hash(p1)
                h2 = self.calcola_hash(p2)
                if h1 != h2:
                    log(f"📋 Diverso (contenuto): {chiave}", "warning")
                    report["file_diversi"].append({
                        "percorso": chiave,
                        "motivo": "hash_diverso",
                        "hash_1": h1,
                        "hash_2": h2,
                    })
                    continue

            log(f"✅ Identico: {chiave}", "success")
            report["file_identici"].append(chiave)

        # ── Verifica integrità ────────────────────────────────────────────────
        if verifica_integrita:
            tutti_da_verificare = []
            for k, v in struttura1.items():
                ext = Path(k).suffix.lower()
                if ext in self.ESTENSIONI_VIDEO or ext in self.ESTENSIONI_IMMAGINI:
                    tutti_da_verificare.append(("1", k, v["path"]))
            for k, v in struttura2.items():
                ext = Path(k).suffix.lower()
                if ext in self.ESTENSIONI_VIDEO or ext in self.ESTENSIONI_IMMAGINI:
                    tutti_da_verificare.append(("2", k, v["path"]))

            log(f"\n🏥 Verifica integrità {len(tutti_da_verificare)} file multimediali...", "info")

            for idx, (cartella_num, chiave, percorso) in enumerate(tutti_da_verificare):
                if stop_event and stop_event.is_set():
                    break

                ext = percorso.suffix.lower()
                if ext in self.ESTENSIONI_IMMAGINI:
                    ok, msg = self.verifica_integrita_immagine(percorso)
                elif ext in self.ESTENSIONI_VIDEO:
                    ok, msg = self.verifica_integrita_video(percorso)
                else:
                    continue

                if not ok:
                    log(f"💔 Corrotto (Cartella {cartella_num}): {chiave} — {msg}", "error")
                    entry = {"percorso": chiave, "errore": msg}
                    if cartella_num == "1":
                        report["corrotti_1"].append(entry)
                    else:
                        report["corrotti_2"].append(entry)
                else:
                    log(f"   ✔ Integrità OK: {chiave}", "muted")

        # ── Riepilogo ─────────────────────────────────────────────────────────
        report["riepilogo"] = {
            "totale_file_1": len(struttura1),
            "totale_file_2": len(struttura2),
            "file_identici": len(report["file_identici"]),
            "file_diversi": len(report["file_diversi"]),
            "solo_in_1": len(report["solo_in_1"]),
            "solo_in_2": len(report["solo_in_2"]),
            "corrotti_1": len(report["corrotti_1"]),
            "corrotti_2": len(report["corrotti_2"]),
        }

        if callback_progresso:
            callback_progresso(1.0)

        return report


# ═══════════════════════════════════════════════════════════════════════════════
#  WIDGET PERSONALIZZATI
# ═══════════════════════════════════════════════════════════════════════════════

class BottoneBello(tk.Canvas):
    """Bottone con angoli arrotondati e animazione hover."""

    def __init__(self, parent, testo, comando=None, larghezza=200, altezza=44,
                 colore_bg=COLORS["accent_primary"], colore_testo=COLORS["bg_card"],
                 colore_hover=COLORS["accent_deep"], raggio=22, **kwargs):
        super().__init__(parent, width=larghezza, height=altezza,
                         bg=parent.cget("bg") if hasattr(parent, 'cget') else COLORS["bg_main"],
                         highlightthickness=0, cursor="hand2", **kwargs)
        self.comando = comando
        self.larghezza = larghezza
        self.altezza = altezza
        self.raggio = raggio
        self.colore_bg = colore_bg
        self.colore_hover = colore_hover
        self.colore_testo = colore_testo
        self.testo = testo
        self._disegnato = False
        self._hover = False
        self._abilitato = True

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", self._on_configure)

        self._disegna(colore_bg)

    def _rect_arrotondato(self, x1, y1, x2, y2, r, **kwargs):
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, **kwargs)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, **kwargs)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, **kwargs)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, **kwargs)
        self.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
        self.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)

    def _disegna(self, colore):
        self.delete("all")
        w, h = self.larghezza, self.altezza
        r = self.raggio
        self._rect_arrotondato(2, 2, w-2, h-2, r,
                                fill=colore, outline=colore)
        self.create_text(w//2, h//2, text=self.testo,
                         fill=self.colore_testo if self._abilitato else COLORS["text_muted"],
                         font=FONTS["btn"])

    def _on_configure(self, event):
        self._disegna(self.colore_hover if self._hover else self.colore_bg)

    def _on_enter(self, event):
        if self._abilitato:
            self._hover = True
            self._disegna(self.colore_hover)

    def _on_leave(self, event):
        self._hover = False
        self._disegna(self.colore_bg)

    def _on_click(self, event):
        if self._abilitato and self.comando:
            self.comando()

    def abilita(self):
        self._abilitato = True
        self._disegna(self.colore_bg)

    def disabilita(self):
        self._abilitato = False
        self._disegna(COLORS["border"])

    def config_testo(self, testo):
        self.testo = testo
        self._disegna(self.colore_hover if self._hover else self.colore_bg)


class BarraProgresso(tk.Canvas):
    """Barra progresso con stile arrotondato."""

    def __init__(self, parent, larghezza=400, altezza=12, **kwargs):
        super().__init__(parent, width=larghezza, height=altezza,
                         bg=parent.cget("bg") if hasattr(parent, 'cget') else COLORS["bg_main"],
                         highlightthickness=0, **kwargs)
        self.larghezza = larghezza
        self.altezza = altezza
        self._valore = 0.0
        self._disegna()

    def _rect_arrotondato(self, x1, y1, x2, y2, r, colore):
        if x2 - x1 < 2*r:
            r = max(1, (x2-x1)//2)
        r = min(r, (y2-y1)//2)
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=colore, outline=colore)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=colore, outline=colore)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=colore, outline=colore)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=colore, outline=colore)
        self.create_rectangle(x1+r, y1, x2-r, y2, fill=colore, outline=colore)
        self.create_rectangle(x1, y1+r, x2, y2-r, fill=colore, outline=colore)

    def _disegna(self):
        self.delete("all")
        w, h = self.larghezza, self.altezza
        r = h // 2
        # Sfondo
        self._rect_arrotondato(0, 0, w, h, r, COLORS["progress_bg"])
        # Riempimento
        if self._valore > 0:
            fill_w = max(h, int(w * self._valore))
            fill_w = min(fill_w, w)
            self._rect_arrotondato(0, 0, fill_w, h, r, COLORS["progress_fill"])

    def imposta(self, valore: float):
        """Imposta valore tra 0.0 e 1.0."""
        self._valore = max(0.0, min(1.0, valore))
        self._disegna()

    def azzera(self):
        self._valore = 0.0
        self._disegna()


class LogArea(tk.Frame):
    """Area di log scrollabile con colorazione messaggi."""

    TAG_COLORI = {
        "info":    COLORS["log_text"],
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "error":   COLORS["error"],
        "muted":   COLORS["text_muted"],
        "title":   COLORS["accent_rose"],
    }

    def __init__(self, parent, altezza=15, **kwargs):
        super().__init__(parent, bg=COLORS["log_bg"], **kwargs)
        self.text = tk.Text(
            self,
            bg=COLORS["log_bg"],
            fg=COLORS["log_text"],
            font=FONTS["mono"],
            height=altezza,
            wrap=tk.WORD,
            state=tk.DISABLED,
            insertbackground=COLORS["log_text"],
            relief=tk.FLAT,
            padx=10,
            pady=8,
            selectbackground=COLORS["accent_primary"],
        )
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)

        for tag, colore in self.TAG_COLORI.items():
            self.text.tag_configure(tag, foreground=colore)

        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text.bind("<MouseWheel>", lambda e: self.text.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.text.bind("<Button-4>",   lambda e: self.text.yview_scroll(-3, "units"))
        self.text.bind("<Button-5>",   lambda e: self.text.yview_scroll( 3, "units"))
        self.bind("<Button-4>",        lambda e: self.text.yview_scroll(-3, "units"))
        self.bind("<Button-5>",        lambda e: self.text.yview_scroll( 3, "units"))

    def aggiungi(self, messaggio: str, livello: str = "info"):
        self.text.configure(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        riga = f"[{timestamp}] {messaggio}\n"
        self.text.insert(tk.END, riga, livello)
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def pulisci(self):
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)


# ═══════════════════════════════════════════════════════════════════════════════
#  SCHERMATE FUNZIONALI
# ═══════════════════════════════════════════════════════════════════════════════

class SchermataBase(tk.Frame):
    """Classe base per le schermate."""

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, bg=COLORS["bg_main"], **kwargs)
        self.controller = controller
        self._stop_event = threading.Event()
        self._thread_attivo = None
        self._costruisci()

    def _costruisci(self):
        pass

    def _torna_home(self):
        self.controller.mostra_home()

    def _crea_header(self, titolo: str, sottotitolo: str = ""):
        header = tk.Frame(self, bg=COLORS["bg_panel"], pady=0)
        header.pack(fill=tk.X)

        # Barra decorativa superiore
        barra = tk.Frame(header, bg=COLORS["accent_primary"], height=3)
        barra.pack(fill=tk.X)

        inner = tk.Frame(header, bg=COLORS["bg_panel"], pady=16, padx=28)
        inner.pack(fill=tk.X)

        # Bottone indietro
        btn_back = BottoneBello(
            inner, "← Home", self._torna_home,
            larghezza=90, altezza=32,
            colore_bg=COLORS["accent_light"],
            colore_testo=COLORS["text_secondary"],
            colore_hover=COLORS["accent_rose"],
            raggio=16,
        )
        btn_back.pack(side=tk.LEFT)

        testo_frame = tk.Frame(inner, bg=COLORS["bg_panel"])
        testo_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(testo_frame, text=titolo, font=FONTS["title"],
                 bg=COLORS["bg_panel"], fg=COLORS["text_primary"]).pack(anchor="w")
        if sottotitolo:
            tk.Label(testo_frame, text=sottotitolo, font=FONTS["subtitle"],
                     bg=COLORS["bg_panel"], fg=COLORS["text_secondary"]).pack(anchor="w")

    def _crea_selettore_cartella(self, parent, etichetta: str, var: tk.StringVar,
                                  comando_selezione) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["bg_card"], pady=10, padx=16,
                          relief=tk.FLAT, bd=0)
        frame.pack(fill=tk.X, pady=4)

        # Bordo simulato
        bordo = tk.Frame(frame, bg=COLORS["border"], height=1)
        bordo.pack(fill=tk.X, side=tk.BOTTOM)

        top = tk.Frame(frame, bg=COLORS["bg_card"])
        top.pack(fill=tk.X)

        tk.Label(top, text=etichetta, font=FONTS["heading"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(side=tk.LEFT)

        BottoneBello(
            top, "📁 Sfoglia", comando_selezione,
            larghezza=110, altezza=32,
            colore_bg=COLORS["accent_light"],
            colore_testo=COLORS["text_secondary"],
            colore_hover=COLORS["accent_rose"],
            raggio=16,
        ).pack(side=tk.RIGHT)

        entry = tk.Entry(frame, textvariable=var, font=FONTS["body"],
                         bg=COLORS["bg_main"], fg=COLORS["text_primary"],
                         relief=tk.FLAT, bd=0, highlightthickness=1,
                         highlightcolor=COLORS["accent_primary"],
                         highlightbackground=COLORS["border"])
        entry.pack(fill=tk.X, pady=(6, 0), ipady=4, padx=2)

        return frame

    def ferma_operazione(self):
        self._stop_event.set()


class SchermataCompressione(SchermataBase):
    """Schermata per la compressione di file multimediali."""

    def _costruisci(self):
        self._crea_header(
            "Compressione File Multimediali",
            "Comprimi immagini e video mantenendo la qualità visiva"
        )

        # ── Contenuto principale ──────────────────────────────────────────────
        contenuto = tk.Frame(self, bg=COLORS["bg_main"])
        contenuto.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # Card selezione cartella
        card = tk.Frame(contenuto, bg=COLORS["bg_card"],
                        highlightthickness=1, highlightbackground=COLORS["border"])
        card.pack(fill=tk.X, pady=(0, 12))

        inner_card = tk.Frame(card, bg=COLORS["bg_card"], padx=20, pady=16)
        inner_card.pack(fill=tk.X)

        self._cartella_var = tk.StringVar()
        self._crea_selettore_cartella(
            inner_card, "📂 Cartella da comprimere",
            self._cartella_var, self._seleziona_cartella
        )

        # Opzioni qualità
        opt_frame = tk.Frame(inner_card, bg=COLORS["bg_card"], pady=8)
        opt_frame.pack(fill=tk.X)

        tk.Label(opt_frame, text="Qualità immagini:",
                 font=FONTS["body"], bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"]).pack(side=tk.LEFT)

        self._qualita_var = tk.IntVar(value=82)
        scala = ttk.Scale(opt_frame, from_=50, to=95, variable=self._qualita_var,
                          orient=tk.HORIZONTAL, length=180)
        scala.pack(side=tk.LEFT, padx=8)

        self._lbl_qualita = tk.Label(opt_frame, text="82%",
                                      font=FONTS["body"], bg=COLORS["bg_card"],
                                      fg=COLORS["accent_deep"], width=5)
        self._lbl_qualita.pack(side=tk.LEFT)

        self._qualita_var.trace_add("write", self._aggiorna_qualita_label)

        # Bottoni azione
        btn_frame = tk.Frame(inner_card, bg=COLORS["bg_card"], pady=8)
        btn_frame.pack(fill=tk.X)

        self._btn_avvia = BottoneBello(
            btn_frame, "▶  Avvia Compressione", self._avvia_compressione,
            larghezza=200, altezza=44,
        )
        self._btn_avvia.pack(side=tk.LEFT, padx=(0, 12))

        self._btn_ferma = BottoneBello(
            btn_frame, "⏹  Interrompi", self._interrompi,
            larghezza=130, altezza=44,
            colore_bg=COLORS["error"],
            colore_hover="#A05555",
        )
        self._btn_ferma.pack(side=tk.LEFT)
        self._btn_ferma.disabilita()

        # Stato e progresso
        stato_frame = tk.Frame(contenuto, bg=COLORS["bg_main"])
        stato_frame.pack(fill=tk.X, pady=(0, 8))

        self._lbl_stato = tk.Label(stato_frame, text="In attesa...",
                                    font=FONTS["body"], bg=COLORS["bg_main"],
                                    fg=COLORS["text_muted"])
        self._lbl_stato.pack(side=tk.LEFT)

        self._lbl_percentuale = tk.Label(stato_frame, text="",
                                          font=FONTS["heading"], bg=COLORS["bg_main"],
                                          fg=COLORS["accent_deep"])
        self._lbl_percentuale.pack(side=tk.RIGHT)

        self._barra = BarraProgresso(contenuto, larghezza=700, altezza=14)
        self._barra.pack(fill=tk.X, pady=(0, 12))

        # Log
        tk.Label(contenuto, text="Log operazioni", font=FONTS["heading"],
                 bg=COLORS["bg_main"], fg=COLORS["text_secondary"]).pack(anchor="w")
        self._log = LogArea(contenuto, altezza=14)
        self._log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    def _aggiorna_qualita_label(self, *args):
        self._lbl_qualita.config(text=f"{self._qualita_var.get()}%")

    def _seleziona_cartella(self):
        cartella = filedialog.askdirectory(title="Seleziona cartella da comprimere")
        if cartella:
            self._cartella_var.set(cartella)

    def _avvia_compressione(self):
        cartella = self._cartella_var.get().strip()
        if not cartella:
            messagebox.showwarning("Cartella mancante", "Seleziona prima una cartella.")
            return
        if not Path(cartella).is_dir():
            messagebox.showerror("Errore", "La cartella specificata non esiste.")
            return

        self._stop_event.clear()
        self._btn_avvia.disabilita()
        self._btn_ferma.abilita()
        self._log.pulisci()
        self._barra.azzera()
        self._lbl_stato.config(text="Avvio in corso...")
        self._lbl_percentuale.config(text="0%")

        qualita = self._qualita_var.get()

        self._thread_attivo = threading.Thread(
            target=self._esegui_compressione,
            args=(Path(cartella), qualita),
            daemon=True,
        )
        self._thread_attivo.start()

    def _interrompi(self):
        self._stop_event.set()
        self._log_thread("⏹ Interruzione richiesta...", "warning")

    def _log_thread(self, msg, livello="info"):
        self.after(0, lambda: self._log.aggiungi(msg, livello))

    def _set_stato(self, msg, perc=None):
        def _():
            self._lbl_stato.config(text=msg)
            if perc is not None:
                self._barra.imposta(perc)
                self._lbl_percentuale.config(text=f"{int(perc*100)}%")
        self.after(0, _)

    def _esegui_compressione(self, cartella: Path, qualita: int):
        ESTENSIONI_SUPPORTATE = {".jpg", ".jpeg", ".png", ".mp4", ".mov"}
        comp_img = CompressoreImmagini()
        comp_vid = CompressoreVideo()

        try:
            # Raccogli tutti i file
            self._log_thread("🔍 Scansione file in corso...", "info")
            tutti_file = [
                p for p in cartella.rglob("*")
                if p.is_file() and p.suffix.lower() in ESTENSIONI_SUPPORTATE
            ]
            totale = len(tutti_file)
            self._log_thread(f"   → {totale} file trovati", "success")

            if totale == 0:
                self._log_thread("⚠️  Nessun file compatibile trovato.", "warning")
                self.after(0, self._fine_operazione)
                return

            successi = 0
            errori = 0
            byte_risparmiati = 0

            for i, percorso in enumerate(tutti_file):
                if self._stop_event.is_set():
                    self._log_thread("⏹ Operazione interrotta dall'utente.", "warning")
                    break

                ext = percorso.suffix.lower()
                nome_breve = percorso.name
                self._set_stato(f"Elaborazione: {nome_breve}", i / totale)

                try:
                    if ext == ".png":
                        if not PIL_AVAILABLE:
                            self._log_thread(f"⚠️  Pillow non disponibile, salto PNG: {nome_breve}", "warning")
                            continue
                        ris = comp_img.converti_png_in_jpg(percorso, qualita)
                        if ris["successo"]:
                            risparmio = ris["dim_originale"] - ris["dim_finale"]
                            byte_risparmiati += max(0, risparmio)
                            self._log_thread(
                                f"✅ PNG→JPG: {nome_breve} | -{ris['riduzione']:.1f}%", "success"
                            )
                            successi += 1
                        else:
                            self._log_thread(f"❌ Errore PNG: {nome_breve} — {ris['errore']}", "error")
                            errori += 1

                    elif ext in (".jpg", ".jpeg"):
                        if not PIL_AVAILABLE:
                            self._log_thread(f"⚠️  Pillow non disponibile, salto JPG: {nome_breve}", "warning")
                            continue
                        ris = comp_img.comprimi_jpg(percorso, qualita)
                        if ris["successo"]:
                            risparmio = ris["dim_originale"] - ris["dim_finale"]
                            byte_risparmiati += max(0, risparmio)
                            self._log_thread(
                                f"✅ JPG: {nome_breve} | -{ris['riduzione']:.1f}%", "success"
                            )
                            successi += 1
                        else:
                            self._log_thread(f"❌ Errore JPG: {nome_breve} — {ris['errore']}", "error")
                            errori += 1

                    elif ext in (".mp4", ".mov"):
                        self._log_thread(f"🎬 Video: {nome_breve}...", "info")

                        def cb_progresso(p):
                            self._set_stato(
                                f"Video: {nome_breve} ({int(p*100)}%)",
                                (i + p) / totale,
                            )

                        if AV_AVAILABLE:
                            ris = comp_vid.comprimi_con_pyav(percorso, cb_progresso)
                        elif CV2_AVAILABLE:
                            ris = comp_vid.comprimi_con_opencv(percorso, cb_progresso)
                        else:
                            self._log_thread(
                                f"⚠️  Nessuna libreria video (PyAV/OpenCV). Salto: {nome_breve}", "warning"
                            )
                            continue

                        if ris["successo"]:
                            risparmio = ris["dim_originale"] - ris["dim_finale"]
                            byte_risparmiati += max(0, risparmio)
                            self._log_thread(
                                f"✅ Video: {nome_breve} | -{ris['riduzione']:.1f}%", "success"
                            )
                            successi += 1
                        else:
                            self._log_thread(f"❌ Errore video: {nome_breve} — {ris['errore']}", "error")
                            errori += 1

                except Exception as e:
                    self._log_thread(f"❌ Eccezione su {nome_breve}: {e}", "error")
                    errori += 1

            # Riepilogo finale
            mb_risparmiati = byte_risparmiati / (1024 * 1024)
            self._log_thread("\n" + "─" * 50, "muted")
            self._log_thread("📊 RIEPILOGO COMPRESSIONE", "title")
            self._log_thread(f"   ✅ Successi: {successi}", "success")
            self._log_thread(f"   ❌ Errori: {errori}", "error" if errori > 0 else "info")
            self._log_thread(f"   💾 Spazio risparmiato: {mb_risparmiati:.2f} MB", "info")
            self._log_thread("─" * 50, "muted")

        except Exception as e:
            self._log_thread(f"❌ Errore critico: {e}", "error")

        self.after(0, self._fine_operazione)

    def _fine_operazione(self):
        self._btn_avvia.abilita()
        self._btn_ferma.disabilita()
        self._lbl_stato.config(text="Operazione completata")
        self._barra.imposta(1.0)
        self._lbl_percentuale.config(text="100%")


class SchermataConfronto(SchermataBase):
    """Schermata per il confronto avanzato tra due cartelle."""

    def __init__(self, parent, controller, **kwargs):
        self._report_corrente = None
        super().__init__(parent, controller, **kwargs)

    def _costruisci(self):
        self._crea_header(
            "Confronto Avanzato Cartelle",
            "Verifica integrità e corrispondenza tra due cartelle"
        )

        contenuto = tk.Frame(self, bg=COLORS["bg_main"])
        contenuto.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # Card selezione cartelle
        card = tk.Frame(contenuto, bg=COLORS["bg_card"],
                        highlightthickness=1, highlightbackground=COLORS["border"])
        card.pack(fill=tk.X, pady=(0, 12))

        inner = tk.Frame(card, bg=COLORS["bg_card"], padx=20, pady=16)
        inner.pack(fill=tk.X)

        self._cartella1_var = tk.StringVar()
        self._cartella2_var = tk.StringVar()

        self._crea_selettore_cartella(
            inner, "📂 Cartella 1 (es. PC)",
            self._cartella1_var, self._seleziona_cartella1
        )
        self._crea_selettore_cartella(
            inner, "📂 Cartella 2 (es. USB / Backup)",
            self._cartella2_var, self._seleziona_cartella2
        )

        # Opzioni
        opt_frame = tk.Frame(inner, bg=COLORS["bg_card"], pady=8)
        opt_frame.pack(fill=tk.X)

        self._hash_var = tk.BooleanVar(value=True)
        self._integrita_var = tk.BooleanVar(value=True)

        def stile_check(parent, testo, var):
            cb = tk.Checkbutton(parent, text=testo, variable=var,
                                bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                                font=FONTS["body"],
                                selectcolor=COLORS["accent_light"],
                                activebackground=COLORS["bg_card"],
                                activeforeground=COLORS["accent_deep"],
                                relief=tk.FLAT, bd=0)
            cb.pack(side=tk.LEFT, padx=(0, 20))

        stile_check(opt_frame, "🔐 Confronto hash SHA256", self._hash_var)
        stile_check(opt_frame, "🏥 Verifica integrità file", self._integrita_var)

        # Bottoni
        btn_frame = tk.Frame(inner, bg=COLORS["bg_card"], pady=8)
        btn_frame.pack(fill=tk.X)

        self._btn_avvia = BottoneBello(
            btn_frame, "▶  Avvia Analisi", self._avvia_confronto,
            larghezza=180, altezza=44,
        )
        self._btn_avvia.pack(side=tk.LEFT, padx=(0, 12))

        self._btn_ferma = BottoneBello(
            btn_frame, "⏹  Interrompi", self._interrompi,
            larghezza=130, altezza=44,
            colore_bg=COLORS["error"],
            colore_hover="#A05555",
        )
        self._btn_ferma.pack(side=tk.LEFT, padx=(0, 20))

        self._btn_esporta_txt = BottoneBello(
            btn_frame, "📄 Esporta TXT", self._esporta_txt,
            larghezza=140, altezza=44,
            colore_bg=COLORS["info"],
            colore_hover="#5A7FA0",
        )
        self._btn_esporta_txt.pack(side=tk.LEFT, padx=(0, 8))

        self._btn_esporta_csv = BottoneBello(
            btn_frame, "📊 Esporta CSV", self._esporta_csv,
            larghezza=140, altezza=44,
            colore_bg=COLORS["success"],
            colore_hover="#5D8F5D",
        )
        self._btn_esporta_csv.pack(side=tk.LEFT)

        self._btn_ferma.disabilita()
        self._btn_esporta_txt.disabilita()
        self._btn_esporta_csv.disabilita()

        # Progresso
        stato_frame = tk.Frame(contenuto, bg=COLORS["bg_main"])
        stato_frame.pack(fill=tk.X, pady=(0, 8))

        self._lbl_stato = tk.Label(stato_frame, text="In attesa...",
                                    font=FONTS["body"], bg=COLORS["bg_main"],
                                    fg=COLORS["text_muted"])
        self._lbl_stato.pack(side=tk.LEFT)

        self._lbl_percentuale = tk.Label(stato_frame, text="",
                                          font=FONTS["heading"], bg=COLORS["bg_main"],
                                          fg=COLORS["accent_deep"])
        self._lbl_percentuale.pack(side=tk.RIGHT)

        self._barra = BarraProgresso(contenuto, larghezza=700, altezza=14)
        self._barra.pack(fill=tk.X, pady=(0, 12))

        # Pannello riepilogo e log side by side
        pnl = tk.Frame(contenuto, bg=COLORS["bg_main"])
        pnl.pack(fill=tk.BOTH, expand=True)

        # Riepilogo a sinistra
        riepilogo_frame = tk.Frame(pnl, bg=COLORS["bg_card"],
                                    highlightthickness=1, highlightbackground=COLORS["border"],
                                    width=220)
        riepilogo_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        riepilogo_frame.pack_propagate(False)

        tk.Label(riepilogo_frame, text="📊 Riepilogo",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["text_primary"], pady=10).pack()

        self._metriche = {}
        metriche_dati = [
            ("totale_file_1", "File in Cartella 1", COLORS["info"]),
            ("totale_file_2", "File in Cartella 2", COLORS["info"]),
            ("file_identici", "Identici", COLORS["success"]),
            ("file_diversi", "Diversi", COLORS["warning"]),
            ("solo_in_1", "Solo in Cart. 1", COLORS["warning"]),
            ("solo_in_2", "Solo in Cart. 2", COLORS["warning"]),
            ("corrotti_1", "Corrotti (Cart. 1)", COLORS["error"]),
            ("corrotti_2", "Corrotti (Cart. 2)", COLORS["error"]),
        ]

        for chiave, etichetta, colore in metriche_dati:
            fr = tk.Frame(riepilogo_frame, bg=COLORS["bg_card"], pady=4, padx=12)
            fr.pack(fill=tk.X)
            tk.Label(fr, text=etichetta, font=FONTS["small"],
                     bg=COLORS["bg_card"], fg=COLORS["text_secondary"]).pack(anchor="w")
            lbl_val = tk.Label(fr, text="—", font=FONTS["heading"],
                                bg=COLORS["bg_card"], fg=colore)
            lbl_val.pack(anchor="w")
            self._metriche[chiave] = lbl_val

        # Log a destra
        log_frame = tk.Frame(pnl, bg=COLORS["bg_main"])
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="Log analisi", font=FONTS["heading"],
                 bg=COLORS["bg_main"], fg=COLORS["text_secondary"]).pack(anchor="w")
        self._log = LogArea(log_frame, altezza=14)
        self._log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    def _seleziona_cartella1(self):
        c = filedialog.askdirectory(title="Seleziona Cartella 1")
        if c:
            self._cartella1_var.set(c)

    def _seleziona_cartella2(self):
        c = filedialog.askdirectory(title="Seleziona Cartella 2")
        if c:
            self._cartella2_var.set(c)

    def _interrompi(self):
        self._stop_event.set()
        self._log_thread("⏹ Interruzione richiesta...", "warning")

    def _log_thread(self, msg, livello="info"):
        self.after(0, lambda: self._log.aggiungi(msg, livello))

    def _set_stato(self, msg, perc=None):
        def _():
            self._lbl_stato.config(text=msg)
            if perc is not None:
                self._barra.imposta(perc)
                self._lbl_percentuale.config(text=f"{int(perc*100)}%")
        self.after(0, _)

    def _avvia_confronto(self):
        c1 = self._cartella1_var.get().strip()
        c2 = self._cartella2_var.get().strip()

        if not c1 or not c2:
            messagebox.showwarning("Cartelle mancanti", "Seleziona entrambe le cartelle.")
            return
        if not Path(c1).is_dir() or not Path(c2).is_dir():
            messagebox.showerror("Errore", "Una delle cartelle specificate non esiste.")
            return

        self._stop_event.clear()
        self._report_corrente = None
        self._btn_avvia.disabilita()
        self._btn_ferma.abilita()
        self._btn_esporta_txt.disabilita()
        self._btn_esporta_csv.disabilita()
        self._log.pulisci()
        self._barra.azzera()
        self._lbl_stato.config(text="Analisi in corso...")

        for lbl in self._metriche.values():
            lbl.config(text="...")

        self._thread_attivo = threading.Thread(
            target=self._esegui_confronto,
            args=(Path(c1), Path(c2)),
            daemon=True,
        )
        self._thread_attivo.start()

    def _esegui_confronto(self, c1: Path, c2: Path):
        analizzatore = AnalizzatoreCartelle()

        report = analizzatore.confronta(
            c1, c2,
            verifica_hash=self._hash_var.get(),
            verifica_integrita=self._integrita_var.get(),
            callback_log=self._log_thread,
            callback_progresso=lambda p: self._set_stato(
                f"Confronto in corso... {int(p*100)}%", p
            ),
            stop_event=self._stop_event,
        )

        self._report_corrente = report
        self.after(0, lambda: self._aggiorna_riepilogo(report))
        self.after(0, self._fine_operazione)

    def _aggiorna_riepilogo(self, report):
        r = report.get("riepilogo", {})
        for chiave, lbl in self._metriche.items():
            valore = r.get(chiave, "—")
            lbl.config(text=str(valore))

    def _fine_operazione(self):
        self._btn_avvia.abilita()
        self._btn_ferma.disabilita()
        if self._report_corrente:
            self._btn_esporta_txt.abilita()
            self._btn_esporta_csv.abilita()
        self._lbl_stato.config(text="Analisi completata")
        self._barra.imposta(1.0)
        self._lbl_percentuale.config(text="100%")

        if self._report_corrente:
            self._log.aggiungi("\n✅ Analisi completata. Usa i bottoni per esportare il report.", "success")

    def _esporta_txt(self):
        if not self._report_corrente:
            return
        percorso = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File di testo", "*.txt")],
            title="Salva report TXT",
            initialfile=f"report_confronto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if not percorso:
            return
        try:
            with open(percorso, "w", encoding="utf-8") as f:
                r = self._report_corrente
                riepilogo = r.get("riepilogo", {})
                f.write("=" * 60 + "\n")
                f.write("REPORT CONFRONTO CARTELLE - InvtorPCPC\n")
                f.write(f"Data: {r.get('timestamp', '')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Cartella 1: {r.get('cartella1', '')}\n")
                f.write(f"Cartella 2: {r.get('cartella2', '')}\n\n")
                f.write("── RIEPILOGO ──────────────────────────────────\n")
                f.write(f"  File in Cartella 1: {riepilogo.get('totale_file_1', 0)}\n")
                f.write(f"  File in Cartella 2: {riepilogo.get('totale_file_2', 0)}\n")
                f.write(f"  File identici: {riepilogo.get('file_identici', 0)}\n")
                f.write(f"  File diversi: {riepilogo.get('file_diversi', 0)}\n")
                f.write(f"  Solo in Cartella 1: {riepilogo.get('solo_in_1', 0)}\n")
                f.write(f"  Solo in Cartella 2: {riepilogo.get('solo_in_2', 0)}\n")
                f.write(f"  Corrotti in Cart. 1: {riepilogo.get('corrotti_1', 0)}\n")
                f.write(f"  Corrotti in Cart. 2: {riepilogo.get('corrotti_2', 0)}\n\n")

                if r.get("file_diversi"):
                    f.write("── FILE DIVERSI ───────────────────────────────\n")
                    for fd in r["file_diversi"]:
                        f.write(f"  {fd['percorso']}\n")
                        f.write(f"    Motivo: {fd.get('motivo', 'sconosciuto')}\n")
                        if "size_1" in fd:
                            f.write(f"    Dim. Cart.1: {fd['size_1']} byte\n")
                            f.write(f"    Dim. Cart.2: {fd['size_2']} byte\n")
                    f.write("\n")

                if r.get("solo_in_1"):
                    f.write("── SOLO IN CARTELLA 1 ─────────────────────────\n")
                    for p in r["solo_in_1"]:
                        f.write(f"  {p}\n")
                    f.write("\n")

                if r.get("solo_in_2"):
                    f.write("── SOLO IN CARTELLA 2 ─────────────────────────\n")
                    for p in r["solo_in_2"]:
                        f.write(f"  {p}\n")
                    f.write("\n")

                if r.get("corrotti_1"):
                    f.write("── FILE CORROTTI (CARTELLA 1) ─────────────────\n")
                    for fc in r["corrotti_1"]:
                        f.write(f"  {fc['percorso']} — {fc['errore']}\n")
                    f.write("\n")

                if r.get("corrotti_2"):
                    f.write("── FILE CORROTTI (CARTELLA 2) ─────────────────\n")
                    for fc in r["corrotti_2"]:
                        f.write(f"  {fc['percorso']} — {fc['errore']}\n")
                    f.write("\n")

            messagebox.showinfo("Esportazione riuscita", f"Report salvato:\n{percorso}")
        except Exception as e:
            messagebox.showerror("Errore esportazione", str(e))

    def _esporta_csv(self):
        if not self._report_corrente:
            return
        percorso = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("File CSV", "*.csv")],
            title="Salva report CSV",
            initialfile=f"report_confronto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not percorso:
            return
        try:
            r = self._report_corrente
            with open(percorso, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Tipo", "Percorso", "Dettagli"])

                for p in r.get("file_identici", []):
                    writer.writerow(["Identico", p, ""])
                for fd in r.get("file_diversi", []):
                    writer.writerow(["Diverso", fd["percorso"], fd.get("motivo", "")])
                for p in r.get("solo_in_1", []):
                    writer.writerow(["Solo in Cartella 1", p, ""])
                for p in r.get("solo_in_2", []):
                    writer.writerow(["Solo in Cartella 2", p, ""])
                for fc in r.get("corrotti_1", []):
                    writer.writerow(["Corrotto (Cart.1)", fc["percorso"], fc.get("errore", "")])
                for fc in r.get("corrotti_2", []):
                    writer.writerow(["Corrotto (Cart.2)", fc["percorso"], fc.get("errore", "")])

            messagebox.showinfo("Esportazione riuscita", f"CSV salvato:\n{percorso}")
        except Exception as e:
            messagebox.showerror("Errore esportazione", str(e))


# ═══════════════════════════════════════════════════════════════════════════════
#  HOME
# ═══════════════════════════════════════════════════════════════════════════════

class SchermataHome(tk.Frame):
    """Schermata principale con i due grandi pulsanti."""

    # =========================================================
    # ICONA PRINCIPALE (FILE PATH O DATA URI BASE64)
    # =========================================================
    MAIN_ICON = "data:image/png;base64,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"
    # =========================================================

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, bg=COLORS["bg_main"], **kwargs)
        self.controller = controller

        # evita garbage collection immagini Tkinter
        self._img_refs = []

        self._costruisci()

    # =========================================================
    # Loader immagine (PNG file oppure Base64 Data URI)
    # =========================================================
    def _carica_immagine(self, sorgente):
        if not sorgente:
            return None

        try:
            # DATA URI
            if isinstance(sorgente, str) and sorgente.startswith("data:image"):
                base64_data = re.sub(r"^data:image/.+;base64,", "", sorgente)
                img = tk.PhotoImage(data=base64_data)
                self._img_refs.append(img)
                return img

            # FILE PATH
            if isinstance(sorgente, str):
                img = tk.PhotoImage(file=sorgente)
                self._img_refs.append(img)
                return img

        except Exception as e:
            print("Errore caricamento immagine:", e)

        return None

    def _costruisci(self):
        # Header decorativo
        header = tk.Frame(self, bg=COLORS["bg_panel"])
        header.pack(fill=tk.X)

        barra = tk.Frame(header, bg=COLORS["accent_primary"], height=4)
        barra.pack(fill=tk.X)

        inner = tk.Frame(header, bg=COLORS["bg_panel"], pady=30, padx=40)
        inner.pack(fill=tk.X)

        tk.Label(inner, text="InvtorPCPC", font=("Georgia", 32, "bold"),
                 bg=COLORS["bg_panel"], fg=COLORS["text_primary"]).pack()

        tk.Label(inner, text="Gestione professionale di file multimediali",
                 font=("Georgia", 13, "italic"),
                 bg=COLORS["bg_panel"], fg=COLORS["text_secondary"]).pack(pady=(4, 0))

        # Linea separatrice decorativa
        sep_frame = tk.Frame(inner, bg=COLORS["bg_panel"], pady=12)
        sep_frame.pack()
        tk.Frame(sep_frame, bg=COLORS["accent_rose"], height=2, width=200).pack()

        # Contenuto centrale
        center = tk.Frame(self, bg=COLORS["bg_main"])
        center.pack(fill=tk.BOTH, expand=True)

        # Griglia pulsanti
        grid = tk.Frame(center, bg=COLORS["bg_main"])
        grid.place(relx=0.5, rely=0.45, anchor="center")

        self._crea_card_funzione(
            grid,
            "🗜️",
            "Compressione File",
            "Comprimi immagini (JPG, PNG) e\nvideo (MP4, MOV) in modo\nprofessionale e sicuro.",
            self.controller.mostra_compressione,
            lato=tk.LEFT,
        )

        # ================= ICONA CENTRALE PRINCIPALE =================
        middle = tk.Frame(
            grid,
            bg=COLORS["bg_main"],
            width=120,
            height=160   # <<< FIX ALTEZZA
        )
        middle.pack(side=tk.LEFT, padx=10)
        middle.pack_propagate(False)

        # Container interno per centraggio perfetto
        middle_inner = tk.Frame(middle, bg=COLORS["bg_main"])
        middle_inner.place(relx=0.5, rely=0.5, anchor="center")

        img_center = self._carica_immagine(self.MAIN_ICON)
        if img_center:
            tk.Label(
                middle_inner,
                image=img_center,
                bg=COLORS["bg_main"]
            ).pack()
        # =============================================================

        self._crea_card_funzione(
            grid,
            "🔍",
            "Confronto Cartelle",
            "Verifica corrispondenza e integrità\ntra due cartelle. Nessun file\nviene modificato.",
            self.controller.mostra_confronto,
            lato=tk.LEFT,
        )

        # Footer
        footer = tk.Frame(self, bg=COLORS["bg_panel"], pady=10)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Frame(footer, bg=COLORS["border"], height=1).pack(fill=tk.X)

        tk.Label(
            footer,
            text="InvtorPCPC v1.0 — Software professionale per Linux",
            font=FONTS["small"],
            bg=COLORS["bg_panel"],
            fg=COLORS["text_muted"]
        ).pack(pady=(8, 0))

    def _crea_card_funzione(self, parent, icona, titolo, descrizione, comando, lato):
        card = tk.Frame(
            parent,
            bg=COLORS["bg_card"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            width=280,
            height=320
        )
        card.pack(side=lato)
        card.pack_propagate(False)

        inner = tk.Frame(card, bg=COLORS["bg_card"], padx=28, pady=24)
        inner.pack(fill=tk.BOTH, expand=True)

        # ===== ICONA =====
        icon_container = tk.Frame(inner, bg=COLORS["bg_card"], height=90)
        icon_container.pack(fill="x")
        icon_container.pack_propagate(False)

        icon_label = tk.Label(
            icon_container,
            text=icona,
            font=("Segoe UI Emoji", 48),
            bg=COLORS["bg_card"]
        )

        icon_label.place(relx=0.5, rely=0.55, anchor="center")
        # =================

        tk.Label(
            inner,
            text=titolo,
            font=("Georgia", 16, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"]
        ).pack(pady=(10, 6))

        tk.Label(
            inner,
            text=descrizione,
            font=FONTS["body"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            justify=tk.CENTER
        ).pack()

        tk.Frame(inner, bg=COLORS["bg_card"]).pack(expand=True)

        BottoneBello(
            inner,
            "Apri →",
            comando,
            larghezza=150,
            altezza=40,
        ).pack(pady=(10, 0))

        # Hover effect sulla card
        def on_enter(e):
            card.configure(highlightbackground=COLORS["accent_primary"])

        def on_leave(e):
            card.configure(highlightbackground=COLORS["border"])

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        for widget in card.winfo_children():
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

# ═══════════════════════════════════════════════════════════════════════════════
#  APPLICAZIONE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    """Controller principale dell'applicazione."""

    def __init__(self):
        super().__init__()
        self.title("InvtorPCPC")
        self.geometry("900x680")
        self.minsize(820, 580)
        self.configure(bg=COLORS["bg_main"])

        # Configura stile ttk
        self._configura_stile()

        # Contenitore unico per le schermate
        self._container = tk.Frame(self, bg=COLORS["bg_main"])
        self._container.pack(fill=tk.BOTH, expand=True)

        # Istanzia schermate
        self._home = SchermataHome(self._container, self)
        self._compressione = SchermataCompressione(self._container, self)
        self._confronto = SchermataConfronto(self._container, self)

        self.mostra_home()

    def _configura_stile(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TScrollbar",
                        troughcolor=COLORS["bg_panel"],
                        background=COLORS["accent_light"],
                        bordercolor=COLORS["border"],
                        arrowcolor=COLORS["text_muted"],
                        relief=tk.FLAT)

        style.configure("TScale",
                        troughcolor=COLORS["progress_bg"],
                        background=COLORS["accent_primary"],
                        bordercolor=COLORS["border"])

    def _nascondi_tutte(self):
        for schermata in (self._home, self._compressione, self._confronto):
            schermata.pack_forget()

    def mostra_home(self):
        self._nascondi_tutte()
        self._home.pack(fill=tk.BOTH, expand=True)

    def mostra_compressione(self):
        self._nascondi_tutte()
        self._compressione.pack(fill=tk.BOTH, expand=True)

    def mostra_confronto(self):
        self._nascondi_tutte()
        self._confronto.pack(fill=tk.BOTH, expand=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()
