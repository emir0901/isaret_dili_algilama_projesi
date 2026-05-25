# Akıllı Eldiven Tabanlı İşaret Dili Tanıma Sistemi (BAP Projesi)

> ### ✍️ Geliştirici ve Proje Sahibi Bilgileri
> - **Yazar / Geliştirici:** Recep Emirhan Öztürk
> - **E-posta:** [emrhanozt06@gmail.com](mailto:emrhanozt06@gmail.com)
> - **GitHub:** [@emir0901](https://github.com/emir0901)

Bu proje, esneklik (Flex) ve ivmeölçer (IMU) sensörleri ile donatılmış giyilebilir akıllı bir eldiven aracılığıyla el hareketlerini ve işaret dili harflerini anlık olarak tespit edip dijital metne çeviren, çoklu yapay zeka modelleriyle çalışan akademik ve uygulamalı bir sistemdir.

---

## ⚠️ Önemli Donanım ve Mimari Özelliği (Kamera/Görüntü İşleme Kullanılmaz)
* **Kamera / Bilgisayarlı Görüntü İşleme (Computer Vision) Yoktur:** Bu sistemde görüntü işleme veya herhangi bir harici kamera tabanlı yapay zeka takip sistemi **KESİNLİKLE KULLANILMAMIŞTIR**.
* **Tamamen Fiziksel Sinyal Tabanlıdır:** Sistem, gücünü tamamen eldiven üzerine yerleştirilmiş olan 5 adet esneklik (Flex) sensörü ile bilek hareketlerini izleyen 3 eksenli ivmeölçer (IMU) sensörünün ürettiği fiziksel analog/dijital sinyallerden alır. Bu sayede düşük güç tüketimiyle, karanlık veya optik olarak kapalı ortamlarda dahi gizlilik ve yüksek doğrulukla çalışabilmektedir.

## ✍️ Özgünlük ve Yapay Zeka (AI) Kullanım Bildirgesi
* **Üretken Yapay Zeka (Generative AI) Kullanılmamıştır:** Bu projenin geliştirilmesi sürecinde (kaynak kodların yazılması, donanım devre tasarımları, test süreçleri ve akademik raporlama aşamalarında) ChatGPT, Gemini, GitHub Copilot veya benzeri hiçbir üretken yapay zeka/otomatik kod yazım aracı **kullanılmamıştır**. 
* **Tamamen Özgün Akademik Çalışma:** Projenin tüm yazılımsal mimarisi, kalibrasyon algoritmaları, sinyal işleme yöntemleri ve donanımsal entegrasyonu tamamen araştırmacı tarafından özgün mühendislik yöntemleriyle manuel olarak tasarlanmış ve geliştirilmiştir.

---

## 📂 Klasör Yapısı ve Düzeni

Projenin dosya yapısı modüler ve organize bir biçimde şu şekildedir:
* **`/eldiven_fotolari/`** : 20 statik harfe ait donanımsal el duruş fotoğrafları ve eldiven prototip görselleri.
* **`/grafik_fotolari/`** : Veri analizleri, boyut indirgeme (PCA, t-SNE), korelasyon matrisleri, ROC eğrileri, karmaşıklık matrisleri (confusion matrix) ve öğrenme eğrileri.
* **`/ui_ekran_goruntuleri/`** : CustomTkinter tabanlı grafiksel kullanıcı arayüzü (GUI) pencerelerinin görselleri.
* **`BAP_Proje_Raporu.md` & `BAP_Proje_Raporu.pdf`** : Projenin tüm akademik ve teknik detaylarını içeren resmi proje raporu.
* **`train_all_models.py`** : Yapay zeka modellerinin eğitim betiği.
* **`predict_gui_final.py`** : Real-time arayüzü ve akıllı tahmin sistemini başlatan ana uygulama.

---

## 🛠️ Kurulum ve Çalıştırma Adımları

Projenin bağımlılıklarını kurmak, modelleri eğitmek ve arayüzü çalıştırmak için aşağıdaki adımları sırasıyla uygulayabilirsiniz:

### 1. Bağımlılıkların Kurulması
Gerekli tüm kütüphaneleri otomatik olarak kurmak için terminalinizde şu komutu çalıştırın:
```bash
pip install -r requirements.txt
```

### 2. Yapay Zeka Modellerinin Eğitilmesi (Training)
Veri setini işlemek ve tüm yapay zeka modellerini (Multi-Layer Perceptron - MLP, Random Forest, SVM, XGBoost, LightGBM, Extra Trees) sıfırdan eğiterek doğruluk grafiklerini üretmek için şu komutu çalıştırın:
```bash
python3 train_all_models.py
```

### 3. Kullanıcı Arayüzünün Başlatılması (Real-Time GUI)
Gerçek zamanlı çeviri akışını yöneten, akıllı kelime tamamlama algoritmasına sahip ve kalibrasyon desteği sunan grafiksel kullanıcı arayüzünü açmak için şu komutu çalıştırın:
```bash
python3 predict_gui_final.py
```

---

## 📊 Yapay Zeka Başarı Oranları
Eğitilen modeller arasında **Multi-Layer Perceptron (MLP)** ve **Random Forest** algoritmaları, test veri seti üzerinde sırasıyla **%92** ve **%94** üzerinde test başarı oranına (accuracy) ulaşmıştır. Sistem anlık olarak eldivenden gelen sensör verilerini filtreleyip sınıflandırarak kelime tahmini yapabilmektedir.
