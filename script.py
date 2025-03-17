from picamera2 import Picamera2
from flask import Flask, Response
import cv2
import threading
import time
import os
import subprocess
import json
from datetime import datetime

# Définition des dossiers
AUTO_CAPTURE_DIR = "captured/automatic/"
MANUAL_CAPTURE_DIR = "captured/manual/"
os.makedirs(AUTO_CAPTURE_DIR, exist_ok=True)
os.makedirs(MANUAL_CAPTURE_DIR, exist_ok=True)

# Initialisation de la caméra
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration()
still_config = picam2.create_still_configuration()
picam2.configure(preview_config)
picam2.start()

# Flask pour le streaming vidéo
app = Flask(__name__)

def generate_video():
    """ Génère le flux vidéo pour Flask """
    while True:
        frame = picam2.capture_array()
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

@app.route('/')
def video_feed():
    """ Route pour le flux vidéo """
    return Response(generate_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

def analyze_plate(image_path):
    """ Analyse l'image avec OpenALPR via l'interface CLI """
    try:
        result = subprocess.run(['alpr', '-c', 'eu', '-j', image_path],
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Erreur d'analyse: {str(e)}")
        return None

def capture_and_analyze():
    """ Capture automatique et analyse """
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(AUTO_CAPTURE_DIR, f"{timestamp}.jpg")

        print(f"[INFO] Capture automatique : {image_path}")
        picam2.capture_file(image_path)

        results = analyze_plate(image_path)
        
        if results and results.get('results'):
            best = results['results'][0]
            plate = best['plate']
            confidence = best['confidence']
            
            print(f"Plaque: {plate} | Confiance: {confidence:.1f}%")
            
            if confidence >= 90:
                print(f"✅ PLAQUE VALIDÉE: {plate}")
                os.rename(image_path, os.path.join(AUTO_CAPTURE_DIR, f"VALIDEE_{plate}_{timestamp}.jpg"))
            else:
                print(f"❌ Confiance insuffisante ({confidence:.1f}%)")
                os.remove(image_path)
        else:
            print("Aucune plaque détectée")
            os.remove(image_path)
        
        time.sleep(10)

def manual_capture():
    """ Capture manuelle """
    while True:
        key = input("\nAppuyez sur 's' pour capture manuelle, 'q' pour quitter: ")
        if key.lower() == 's':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(MANUAL_CAPTURE_DIR, f"MANUEL_{timestamp}.jpg")
            print(f"Capture manuelle: {image_path}")
            picam2.capture_file(image_path)
        elif key.lower() == 'q':
            os._exit(0)

# Démarrage des threads
threading.Thread(target=capture_and_analyze, daemon=True).start()
threading.Thread(target=manual_capture, daemon=True).start()

# Lancer le serveur Flask
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8080, threaded=True)
    finally:
        picam2.stop()
        print("\nNettoyage terminé")