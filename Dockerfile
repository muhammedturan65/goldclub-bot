# Python'un resmi, hafif bir versiyonunu temel al
FROM python:3.10-slim

# Sistemin paket yöneticisini güncelle ve Chrome tarayıcısını kur
# Bu, "cannot find Chrome binary" hatasını çözer
RUN apt-get update && apt-get install -y chromium chromium-driver --no-install-recommends

# Proje dosyalarının kopyalanacağı bir çalışma dizini oluştur
WORKDIR /app

# Önce gereksinimler dosyasını kopyala ve kütüphaneleri yükle
# Bu katmanlama, kod değiştiğinde kütüphanelerin tekrar tekrar yüklenmesini önler
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Geri kalan tüm proje dosyalarını kopyala
COPY . .

# Render.com'un uygulamayı başlatmak için kullanacağı komut
# Gunicorn, uygulamayı internet ortamında stabil çalıştırır
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]