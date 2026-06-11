# ==============================================================================
#                 İŞARET DİLİ ANALİZ SİSTEMİ PROJESİ (BAP)
# ==============================================================================
# Geliştirici / Yazar : Recep Emirhan Öztürk
# E-posta            : emrhanozt06@gmail.com
# GitHub             : https://github.com/emir0901
#
# © 2026 Recep Emirhan Öztürk. Tüm hakları saklıdır.
# ==============================================================================

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def train_system():
    print("🚀 EĞİTİM BAŞLIYOR...")

    data_path = 'isaret_dili_izleme/veriuma.csv'
    if not os.path.exists(data_path):
        data_path = 'isaret_dili_izleme/veriokumayyeni.csv'

    if not os.path.exists(data_path):
        print(f"❌ HATA: {data_path} bulunamadı!")
        return

    # 1. Veriyi Yükle ve Temizle
    try:
        df = pd.read_csv(data_path, on_bad_lines='skip')
        df = df.dropna()
        print(f"📊 Toplam Ham Veri: {len(df)}")
    except Exception as e:
        print(f"❌ Veri okuma hatası: {e}")
        return

    # 2. Veriyi Dengele (Her harften en fazla 800 örnek al)
    min_counts = df['label'].value_counts().min()
    target_samples = min(min_counts, 800)
    print(f"⚖️ Her harf için {target_samples} örnek alınarak dengeleniyor...")
    df = df.groupby('label').apply(lambda x: x.sample(n=target_samples, random_state=42)).reset_index(drop=True)
    print(f"✅ Dengelenmiş Veri Sayısı: {len(df)}")

    # 3. Ön İşleme
    X = df.drop('label', axis=1).values
    y_raw = df['label'].values

    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Eğitim / Doğrulama bölünmesi (%80 eğitim, %20 doğrulama)
    X_train, X_val, y_train, y_val = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. MLP Modelini Eğit
    print("\n🧠 MLP modeli eğitiliyor...")
    clf = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=1000, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_val)
    acc = accuracy_score(y_val, y_pred)
    print(f"✅ MLP Doğrulama Başarı Oranı: %{acc*100:.2f}")

    # 5. Modeli Kaydet
    with open('sign_language_model.pkl', 'wb') as f:
        pickle.dump(clf, f)
    with open('scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open('label_encoder.pkl', 'wb') as f:
        pickle.dump(le, f)

    print("\n✨ MODEL BAŞARIYLA GÜNCELLENDİ!")

if __name__ == "__main__":
    train_system()
