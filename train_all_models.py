import pandas as pd
import numpy as np
import pickle
import os
import csv
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def train_system():
    print("🚀 DENGELİ EĞİTİM BAŞLIYOR...")
    
    data_path = 'isaret_dili_izleme/veriuma.csv' # Yeni isme göre güncelledik (Önceki adımda veriokuma.csv yapmıştık)
    # Eğer dosya ismi veriokuma.csv ise kontrol et
    if not os.path.exists(data_path):
        data_path = 'isaret_dili_izleme/veriokumayyeni.csv'

    if not os.path.exists(data_path):
        print(f"❌ HATA: {data_path} bulunamadı!")
        return

    # 1. Veriyi Yükle ve Temizle
    try:
        # Bozuk satırları atlayarak oku
        df = pd.read_csv(data_path, on_bad_lines='skip')
        df = df.dropna()
        print(f"📊 Toplam Ham Veri: {len(df)}")
    except Exception as e:
        print(f"❌ Veri okuma hatası: {e}")
        return

    # 2. Veriyi Dengele (Her harften tam olarak 800 örnek al)
    # Eğer bir harften 800'den az varsa, olanın tamamını al
    min_counts = df['label'].value_counts().min()
    target_samples = min(min_counts, 800)
    
    print(f"⚖️ Her harf için {target_samples} örnek alınarak dengeleniyor...")
    df = df.groupby('label').apply(lambda x: x.sample(n=target_samples, random_state=42)).reset_index(drop=True)
    print(f"✅ Dengelenmiş Veri Sayısı: {len(df)}")

    # 3. Ön İşleme
    X = df.drop('label', axis=1).values
    y_raw = df['label'].values

    # Label Encoder (Harfleri 0, 1, 2... formatına çevirir - XGBoost için şart)
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    
    # Ölçeklendirme
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Veriyi Bölme (Eşit dağılım için stratify kullanıyoruz)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Model Tanımları
    models = {
        "MLP (Ana)": {
            "model": MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=1000, random_state=42),
            "suffix": ""
        },
        "Extra Trees": {
            "model": ExtraTreesClassifier(n_estimators=200, random_state=42),
            "suffix": "_test10et"
        },
        "Random Forest": {
            "model": RandomForestClassifier(n_estimators=200, random_state=42),
            "suffix": "_test4rf"
        },
        "XGBoost": {
            "model": XGBClassifier(n_estimators=200, random_state=42),
            "suffix": "_test8xgb"
        },
        "LightGBM": {
            "model": LGBMClassifier(n_estimators=200, random_state=42, verbose=-1, importance_type='split'),
            "suffix": "_test9lgbm"
        },
        "SVM": {
            "model": SVC(probability=True, random_state=42),
            "suffix": "_test3svm"
        }
    }

    # 5. Eğitim ve Kayıt
    for name, config in models.items():
        print(f"\n🧠 {name} eğitiliyor...")
        clf = config['model']
        clf.fit(X_train, y_train)
        
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"✅ {name} Başarı Oranı: %{acc*100:.2f}")

        # Her model için kendi scaler ve encoder'ını kaydet (Tahmin tarafıyla uyum için)
        suffix = config['suffix']
        with open(f'sign_language_model{suffix}.pkl', 'wb') as f:
            pickle.dump(clf, f)
        with open(f'scaler{suffix}.pkl', 'wb') as f:
            pickle.dump(scaler, f)
        with open(f'label_encoder{suffix}.pkl', 'wb') as f:
            pickle.dump(le, f)
        
    print("\n✨ TÜM MODELLER BAŞARIYLA GÜNCELLENDİ!")

if __name__ == "__main__":
    train_system()
