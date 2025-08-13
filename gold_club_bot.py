# gold_club_bot.py (Doğru ve Son Hali)

import os, time, traceback, re, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class GoldClubBot:
    def __init__(self, email, password, target_group=None, project_path='.'):
        self.email, self.password, self.target_group, self.project_path = email, password, target_group, project_path
        self.driver, self.wait, self.base_url = None, None, "https://goldclubhosting.xyz/"
    def _take_screenshot_on_error(self):
        try:
            if self.driver:
                screenshot_path = os.path.join(self.project_path, 'error_screenshot.png')
                self.driver.save_screenshot(screenshot_path)
                print(f"HATA: Ekran görüntüsü şuraya kaydedildi: {screenshot_path}")
        except Exception as ss_error:
            print(f"Ekran görüntüsü alınırken ek bir hata oluştu: {ss_error}")
    def _find_element_with_retry(self, by, value, retries=3, delay=5):
        for i in range(retries):
            try: return self.wait.until(EC.visibility_of_element_located((by, value)))
            except TimeoutException:
                if i < retries - 1: print(f"-> Element '{value}' bulunamadı. Tekrar deneniyor..."); time.sleep(delay)
                else: raise
    def _click_element_with_retry(self, by, value, retries=3, delay=5):
        for i in range(retries):
            try: element = self.wait.until(EC.element_to_be_clickable((by, value))); element.click(); return
            except TimeoutException:
                if i < retries - 1: print(f"-> Tıklanabilir element '{value}' bulunamadı. Tekrar deneniyor..."); time.sleep(delay)
                else: raise
    def _parse_playlist(self, m3u_url):
        print(f"-> Playlist indiriliyor ve '{self.target_group or 'Tümü'}' grubuna göre filtreleniyor...")
        try:
            response = requests.get(m3u_url, timeout=20); response.raise_for_status(); content = response.text
            channels = [{"name": n.strip(), "group": g.strip(), "url": u.strip()} for g, n, u in re.findall(r'#EXTINF:-1.*?group-title="(.*?)".*?,(.*?)\n(https?://.*)', content) if not self.target_group or self.target_group.lower() in g.lower()]
            print(f"-> Analiz tamamlandı: {len(channels)} kanal bulundu.")
            if not channels: print(f"[UYARI] '{self.target_group}' grubunda hiç kanal bulunamadı.")
            return channels
        except requests.RequestException as e: print(f"[HATA] Playlist indirilemedi: {e}"); return None
    def _setup_driver(self):
        print("-> WebDriver hazırlanıyor (Render.com Build Script modu)...")
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 20)
            print("-> WebDriver başarıyla başlatıldı.")
        except WebDriverException as e:
            print(f"[HATA] WebDriver başlatılamadı: {e.msg}")
            self._take_screenshot_on_error()
            raise
    def _login(self):
        print("-> Giriş yapılıyor..."); self.driver.get(f"{self.base_url}index.php?rp=/login"); self._find_element_with_retry(By.ID, "inputEmail").send_keys(self.email); self._find_element_with_retry(By.ID, "inputPassword").send_keys(self.password); self._click_element_with_retry(By.ID, "login"); self.wait.until(EC.url_contains("clientarea.php"))
    def _order_free_trial(self):
        print("-> Ücretsiz deneme sipariş ediliyor..."); self.driver.get(f"{self.base_url}index.php?rp=/store/free-trial"); self._click_element_with_retry(By.ID, "product7-order-button"); self._click_element_with_retry(By.ID, "checkout"); self._click_element_with_retry(By.XPATH, "//label[contains(., 'I have read and agree to the')]"); self._click_element_with_retry(By.ID, "btnCompleteOrder"); self.wait.until(EC.url_contains("cart.php?a=complete"))
    def _navigate_to_product_details(self):
        print("-> Ürün detaylarına gidiliyor..."); self._click_element_with_retry(By.PARTIAL_LINK_TEXT, "Continue To Client Area"); view_details_button = self._find_element_with_retry(By.XPATH, "(//button[contains(., 'View Details')])[1]"); view_details_button.click()
    def _extract_data(self):
        print("-> Veriler çekiliyor..."); m3u_input = self._find_element_with_retry(By.ID, "m3ulinks"); m3u_link = m3u_input.get_attribute("value"); expiry_date_element = self._find_element_with_retry(By.XPATH, "//div[contains(., 'Expiry Date:')]/strong"); expiry_date = expiry_date_element.text.strip()
        if not (m3u_link and expiry_date): raise Exception("M3U linki veya son kullanma tarihi alınamadı.")
        return {"url": m3u_link, "expiry": expiry_date, "channels": self._parse_playlist(m3u_link)}
    def _cleanup(self):
        if self.driver: self.driver.quit(); print("-> Tarayıcı kapatıldı.")
    def run_full_process(self):
        try:
            self._setup_driver(); self._login(); self._order_free_trial(); self._navigate_to_product_details(); return self._extract_data()
        except Exception as e:
            print(f"[KRİTİK HATA] Bot sürecinde bir hata oluştu: {e}"); traceback.print_exc()
            self._take_screenshot_on_error()
            raise e
        finally: self._cleanup()
