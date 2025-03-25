from picamera2 import Picamera2
from flask import Flask, Response
import cv2
import threading
import time
import os
import subprocess
import json
import requests
from datetime import datetime
from gps_reader import get_gps_location

# Configuration
SERVER_URL = "http://3.91.80.122:80/send_plate"
DEVICE_ID = "d3d9a27c-40b3-4c71-9a56-6d8a89e9f15b"
STATIC_LATITUDE = 43.6
STATIC_LONGITUDE = 3.88
CAPTURE_INTERVAL = 10

# Répertoires
AUTO_DIR = "../captured/automatic/"
MANUAL_DIR = "../captured/manual/"
os.makedirs(AUTO_DIR, exist_ok=True)
os.makedirs(MANUAL_DIR, exist_ok=True)

# Configuration caméra
MAX_RESOLUTION = (3280, 2464)  # Résolution maximale IMX219
PREVIEW_RES = (640, 480)       # Résolution flux vidéo

picam2 = None
app = Flask(__name__)

def initialize_camera():
    """Initialisation avec meilleures configurations"""
    global picam2
    try:
        picam2 = Picamera2()

        # Configuration preview
        preview_config = picam2.create_preview_configuration(
            main={"size": PREVIEW_RES},
            encode="main"
        )

        # Configuration haute résolution
        still_config = picam2.create_still_configuration(
            main={"size": MAX_RESOLUTION},
            raw={"size": MAX_RESOLUTION},
            encode="main"
        )

        picam2.configure(preview_config)
        picam2.start()
        print(f"Caméra initialisée | Résolution max: {MAX_RESOLUTION}")
        return still_config

    except Exception as e:
        print(f"Erreur caméra: {str(e)}")
        return None

def generate_video():
    """Flux vidéo basse résolution"""
    while True:
        try:
            frame = picam2.capture_array("main")
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        except Exception as e:
            print(f"Erreur flux: {str(e)}")
            time.sleep(1)

@app.route('/')
def video_feed():
    return Response(generate_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

def capture_high_res(still_config, path):
    """Capture haute résolution avec paramètres optimaux"""
    request = picam2.capture_request()
    request.save("main", path)
    request.release()
    print(f"Capture sauvegardée: {path} ({MAX_RESOLUTION[0]}x{MAX_RESOLUTION[1]})")

def analyze_plate(image_path):
    """Analyse ALPR"""
    try:
        result = subprocess.run(['alpr', '-c', 'eu', '-j', image_path],
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Erreur analyse: {str(e)}")
        return None

def auto_capture(still_config):
    """Boucle de capture automatique"""
    while True:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = os.path.join(AUTO_DIR, f"HQ_{timestamp}.jpg")

            # Capture en haute qualité
            capture_high_res(still_config, img_path)

            # Analyse
            result = analyze_plate(img_path)

            if result and result.get('results'):
                best = result['results'][0]
                plate = best['plate']
                confidence = best['confidence']

                if confidence >= 90:
                    print("PLAQUE LUE: "+ plate)
                    new_path = os.path.join(AUTO_DIR, f"VALIDEE_{plate}_{timestamp}.jpg")
                    os.rename(img_path, new_path)

                    # Envoi des données
                    latitude, longitude = get_gps_location()
                    payload = {
                        "license_plate": plate,
                        "latitude": latitude or STATIC_LATITUDE,
                        "longitude": longitude or STATIC_LONGITUDE,
                        "device_id": DEVICE_ID,
                    }
                    headers = {'Content-Type': 'application/json'}

                    response = requests.post(SERVER_URL, json=payload, headers=headers)
                    print(f"Envoi réussi: {response.status_code}, réponse: {response.text}")


                else:
                    os.remove(img_path)
            else:
                os.remove(img_path)

        except Exception as e:
            print(f"Erreur capture auto: {str(e)}")

        time.sleep(CAPTURE_INTERVAL)

def manual_capture(still_config):
    """Capture manuelle haute résolution"""
    while True:
        try:
            cmd = input("\nCommande [s/q]: ")
            if cmd.lower() == 's':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img_path = os.path.join(MANUAL_DIR, f"MANUEL_HQ_{timestamp}.jpg")
                capture_high_res(still_config, img_path)
            elif cmd.lower() == 'q':
                os._exit(0)

        except Exception as e:
            print(f"Erreur commande: {str(e)}")

if __name__ == '__main__':
    still_config = initialize_camera()
    if not still_config:
        exit(1)

    try:
        # Threads
        threading.Thread(target=auto_capture, args=(still_config,), daemon=True).start()
        threading.Thread(target=manual_capture, args=(still_config,), daemon=True).start()

        # Serveur Flask
        print("Streaming sur http://10.10.10.226:8080")
        app.run(host='10.10.10.226', port=8080)

    except KeyboardInterrupt:
        print("\nArrêt propre...")
    finally:
        picam2.stop()