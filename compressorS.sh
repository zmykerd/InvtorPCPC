#!/bin/bash

# RICHIEDE: sudo apt-get install imagemagick libheif-examples jpegoptim ffmpeg

shopt -s nocaseglob

# 1. Converti PNG in JPG (aggiungendo suffisso _conv)
for img in *.png; do
    if [[ -f "$img" ]]; then
        convert "$img" "${img%.png}_conv.jpg"
    fi
done

rm -rf *.png

# 2. Converti HEIC in JPG (aggiungendo suffisso _conv)
for f in *.HEIC; do
    if [[ -f "$f" ]]; then
        heif-convert -q 100 "$f" "${f%.HEIC}_conv.jpg"
    fi
done

rm -rf *.HEIC

# 3. Comprimi tutti i JPG/JPEG (inclusi quelli convertiti)
for img in *.jpg *.jpeg *.JPG *.JPEG; do
    if [[ -f "$img" ]]; then
        jpegoptim --strip-all --max=25 "$img"
    fi
done

# 4. Comprimi i file .mp4
for file in *.mp4; do
    if [[ -f "$file" ]]; then
        if ! ffmpeg -err_detect ignore_err -i "$file" -c:v libx264 -crf 25 -c:a aac "compressed_$file"; then
            echo "Errore durante la lavorazione di $file, salto il file."
        else
            echo "File $file compresso con successo."
        fi
    fi
done

# 5. Comprimi i file .MOV
for file in *.MOV; do
    if [[ -f "$file" ]]; then
        if ! ffmpeg -err_detect ignore_err -i "$file" -c:v libx264 -crf 25 -c:a aac "compressed_$file"; then
            echo "Errore durante la lavorazione di $file, salto il file."
        else
            echo "File $file compresso con successo."
        fi
    fi
done

shopt -u nocaseglob  # Disabilita la gestione case-insensitive

# 6. Rimuovi i file originali non compressi (video)
for file in *.mp4 *.MOV *.MP4 *.mov; do
    if [[ -f "$file" && ! "$file" =~ ^compressed_ ]]; then
        echo "Rimuovendo il file originale: $file"
        rm -f "$file"
    fi
done
