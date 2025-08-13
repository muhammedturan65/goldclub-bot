#!/usr/bin/env bash
# Bu betik, Render.com üzerinde dağıtım (deploy) işlemi sırasında çalıştırılır.

# Herhangi bir komut başarısız olursa betiği hemen sonlandır.
set -o errexit

# 1. Adım: requirements.txt dosyasında listelenen Python kütüphanelerini kur.
echo "---> Python kütüphaneleri kuruluyor..."
pip install -r requirements.txt

# 2. Adım: Selenium'un ihtiyaç duyduğu sistem bağımlılıklarını kur.
# Bu komutlar, "cannot find Chrome binary" hatasını çözmek için
# Chromium tarayıcısını ve ilgili sürücüsünü sunucuya yükler.
echo "---> Sistem bağımlılıkları (Chromium & ChromeDriver) kuruluyor..."
apt-get update
apt-get install -y chromium chromium-driver

echo "---> Kurulum betiği başarıyla tamamlandı."
