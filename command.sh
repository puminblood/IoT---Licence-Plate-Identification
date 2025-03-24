#!/bin/bash

# 🧱 Install system dependencies
sudo apt install -y build-essential cmake git \
    libopencv-dev libtesseract-dev libleptonica-dev \
    liblog4cplus-dev libcurl4-openssl-dev \
    tesseract-ocr tesseract-ocr-eng \
    python3-picamera2 libcamera-dev \
    gpsd gpsd-clients python3-gps \
    python3-pip

sudo apt update
sudo apt install -y tesseract-ocr libtesseract-dev libleptonica-dev

# 🐍 Python packages
pip install --break-system-packages openalpr flask gps3 requests boto3

# 📥 Clone openalpr if needed
cd /usr/local/src
if [ ! -d "openalpr" ]; then
    sudo git clone https://github.com/openalpr/openalpr.git
fi

# 🔧 Compilation section (with permission handling)
cd /usr/local/src/openalpr/src
sudo rm -rf build
sudo mkdir -p build
sudo chown $USER:$USER build  # 👈 Donne les droits à l'utilisateur courant pour éviter erreurs cmake
cd build

cmake -DTesseract_INCLUDE_DIR=/usr/include/tesseract \
      -DTesseract_INCLUDE_BASEAPI_DIR=/usr/include/tesseract \
      -DTesseract_INCLUDE_CCSTRUCT_DIR=/usr/include/tesseract \
      -DTesseract_INCLUDE_CCMAIN_DIR=/usr/include/tesseract \
      -DTesseract_INCLUDE_CCUTIL_DIR=/usr/include/tesseract \
      -DTesseract_LIBRARY=/usr/lib/arm-linux-gnueabihf/libtesseract.so \
      -DLeptonica_LIBRARY=/usr/lib/arm-linux-gnueabihf/liblept.so \
      ..

make -j$(nproc)
sudo make install
sudo ldconfig

# 📝 Config
sudo mkdir -p /etc/openalpr
sudo tee /etc/openalpr/openalpr.conf > /dev/null <<EOF
# OpenALPR configuration file

config_dir = /etc/openalpr/runtime_data/config

country = eu  # Changer en "us" si besoin
pattern_match_max = 5
openalpr_use_gpu = 0
openalpr_use_opencv = 1

# Paths
topn = 10
prewarp_enabled = 1
prewarp_minplate_height = 10
prewarp_maxplate_height = 100
EOF

sudo chmod 644 /etc/openalpr/openalpr.conf
sudo chown root:root /etc/openalpr/openalpr.conf
sudo cp -r /usr/local/src/openalpr/runtime_data /etc/openalpr/

# 👁️ Access to camera
sudo apt install libcamera-dev
sudo usermod -aG video $USER
