sudo apt install -y build-essential cmake git \
    libopencv-dev libtesseract-dev libleptonica-dev \
    liblog4cplus-dev libcurl4-openssl-dev \
    tesseract-ocr tesseract-ocr-eng

sudo apt update
sudo apt install -y tesseract-ocr libtesseract-dev libleptonica-dev


cd /usr/local/src
sudo git clone https://github.com/openalpr/openalpr.git
cd openalpr/src

sudo mkdir build && cd build
cd /usr/local/src/openalpr/src/build
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

sudo nano /etc/openalpr/openalpr.conf
#A AJOUTER A LA MAIN

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
#FIN

sudo chmod 644 /etc/openalpr/openalpr.conf
sudo chown root:root /etc/openalpr/openalpr.conf



sudo mkdir -p /etc/openalpr
sudo cp -r /usr/local/src/openalpr/runtime_data /etc/openalpr/

pip install --break-system-packages openalpr
sudo apt install -y python3-picamera2
