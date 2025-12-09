import os
import json
import subprocess
import shutil

# Konfiguration
RAW_INPUT_FOLDER = 'processed' 
FINAL_OUTPUT_FOLDER = 'sources' 
METADATA_FILE = 'metadata.json'

VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.mpeg', '.ts'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS.union(IMAGE_EXTENSIONS)

# --- FFmpeg Funktionen ---

# Funktion für Videos (NUR WebM Konvertierung)
def run_ffmpeg_video_command(input_path, output_webm_path):
    """Führt FFmpeg-Befehle für WebM-Konvertierung aus (ohne Thumbnail)."""
    
    # --- 1. WebM Konvertierung (Primär) ---
    print(f"Verarbeite Video WebM: {input_path} -> {os.path.basename(output_webm_path)}")
    webm_command = [
        'ffmpeg', '-i', input_path,
        '-vcodec', 'libvpx-vp9', '-crf', '35', '-b:v', '0', 
        '-an',                        # Audio entfernen
        '-y',
        output_webm_path
    ]
    try:
        subprocess.run(webm_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"WebM-Fehler bei {input_path}: {e.output.decode('utf-8')}")
        return False
    except FileNotFoundError:
        print("FEHLER: FFmpeg nicht gefunden.")
        return False

    # --- 2. JPG Thumbnail Generierung ENTFALLEN ---
    
    print("Video-Konvertierung erfolgreich.")
    return True

# NEUE Funktion für Bilder (Konvertierung zu WebP)
def run_ffmpeg_image_command(input_path, output_webp_path):
    """Konvertiert Bilder (JPG, PNG) zu WebP."""
    print(f"Konvertiere Bild WebP: {input_path} -> {os.path.basename(output_webp_path)}")
    
    # -q:v 80 ist eine gute Qualität/Kompromiss für WebP
    image_command = [
        'ffmpeg',
        '-i', input_path,
        '-vcodec', 'libwebp',
        '-q:v', '80',
        '-y',
        output_webp_path
    ]
    try:
        subprocess.run(image_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("Bild-Konvertierung erfolgreich.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"WebP-Konvertierungsfehler bei {input_path}: {e.output.decode('utf-8')}")
        return False
    except FileNotFoundError:
        print("FEHLER: FFmpeg nicht gefunden.")
        return False

# --- Hauptfunktion ---

def main():
    if not os.path.exists(FINAL_OUTPUT_FOLDER):
        os.makedirs(FINAL_OUTPUT_FOLDER)
        
    if not os.path.exists(RAW_INPUT_FOLDER):
        print(f"ACHTUNG: Der Rohdaten-Ordner '{RAW_INPUT_FOLDER}' existiert nicht. Es gibt nichts zu verarbeiten.")
        os.makedirs(RAW_INPUT_FOLDER)
        return 

    # 2. Existierende Metadata laden (Unverändert)
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"tags": ["funny", "cute"], "assignments": {}, "files": []}
    else:
        data = {"tags": ["funny", "cute"], "assignments": {}, "files": []}
    
    if "assignments" not in data: data["assignments"] = {}

    
    # 3. Dateien verarbeiten
    final_files = [] 
    raw_files_list = os.listdir(RAW_INPUT_FOLDER)
    
    if not raw_files_list:
        print(f"Der Rohdaten-Ordner '{RAW_INPUT_FOLDER}' ist leer.")

    
    for filename in raw_files_list:
        input_path = os.path.join(RAW_INPUT_FOLDER, filename)
        
        if os.path.isdir(input_path) or filename.startswith('.'):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            print(f"Ignoriere unbekannten Dateityp: {filename}")
            continue

        base_name = os.path.splitext(filename)[0]
        
        if ext in VIDEO_EXTENSIONS:
            # Video Verarbeitung: Generiere NUR WebM
            
            output_webm_filename = base_name + '.webm'
            # output_thumb_filename wurde entfernt
            
            output_webm_path = os.path.join(FINAL_OUTPUT_FOLDER, output_webm_filename)
            # output_thumb_path wurde entfernt
            
            # Überprüfe die Änderungszeit
            needs_processing = True
            if os.path.exists(output_webm_path):
                if os.path.getmtime(output_webm_path) >= os.path.getmtime(input_path):
                    needs_processing = False
            
            if needs_processing:
                print(f"Verarbeite {filename} (neu oder geändert)...")
                # run_ffmpeg_video_command nur mit WebM-Pfad aufrufen
                if run_ffmpeg_video_command(input_path, output_webm_path):
                    final_files.append(output_webm_filename)
                    # final_files.append(output_thumb_filename) entfernt
            else:
                final_files.append(output_webm_filename)
                # final_files.append(output_thumb_filename) entfernt
                
        elif ext in IMAGE_EXTENSIONS:
            # Bild Verarbeitung
            
            if ext in {'.jpg', '.jpeg', '.png'}:
                # Konvertiere JPG/PNG zu WebP
                output_webp_filename = base_name + '.webp'
                output_webp_path = os.path.join(FINAL_OUTPUT_FOLDER, output_webp_filename)
                
                # Überprüfe die Änderungszeit
                needs_processing = True
                if os.path.exists(output_webp_path):
                    if os.path.getmtime(output_webp_path) >= os.path.getmtime(input_path):
                        needs_processing = False

                if needs_processing:
                    print(f"Verarbeite Bild {filename} (neu oder geändert)...")
                    if run_ffmpeg_image_command(input_path, output_webp_path):
                        final_files.append(output_webp_filename)
                else:
                    final_files.append(output_webp_filename)
                    
            elif ext in {'.gif', '.webp'}:
                # GIFs und bereits vorhandene WebP-Dateien nur kopieren
                output_path = os.path.join(FINAL_OUTPUT_FOLDER, filename)
                
                if not os.path.exists(output_path) or os.path.getmtime(input_path) > os.path.getmtime(output_path):
                    print(f"Kopiere/Aktualisiere {ext.upper()}: {filename}")
                    shutil.copy2(input_path, output_path)
                
                final_files.append(filename)

    # 4. Cleanup alter verarbeiteter Dateien im FINAL_OUTPUT_FOLDER
    
    files_in_output = os.listdir(FINAL_OUTPUT_FOLDER)
    for processed_file in files_in_output:
        # Dies löscht nun auch alte .jpg-Thumbnails, die nicht mehr in final_files sind.
        if os.path.isfile(os.path.join(FINAL_OUTPUT_FOLDER, processed_file)) and processed_file not in final_files:
             os.remove(os.path.join(FINAL_OUTPUT_FOLDER, processed_file))
             print(f"Alte verarbeitete Datei gelöscht: {processed_file}")


    # 5. Metadaten abgleichen und speichern (Unverändert)
    final_files.sort()
    data["files"] = final_files
    
    orphaned_assignments = [f for f in data["assignments"] if f not in final_files]
    for orphan in orphaned_assignments:
        del data["assignments"][orphan]

    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"\nAlle Dateien verarbeitet und {len(final_files)} Einträge in {METADATA_FILE} registriert.")
    print("Die HTML-Seite lädt jetzt aus dem '/sources' Ordner.")


if __name__ == "__main__":
    main()