#!/usr/bin/env bash
# Hata durumunda betiği sonlandır
set -o errexit

# Python kütüphanelerini requirements.txt dosyasından yükle
pip install -r requirements.txt

# Chromium'u kur (Render'ın önbelleğe alma özelliğini kullanarak)
STORAGE_DIR=/opt/render/project/.render
if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...Chrome indiriliyor"
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome
  wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x ./google-chrome-stable_current_amd64.deb .
  rm ./google-chrome-stable_current_amd64.deb
  # Betiğin çalıştığı önceki dizine geri dön
  cd $HOME/project/src
else
  echo "...Önbellekten Chrome kullanılıyor"
fi