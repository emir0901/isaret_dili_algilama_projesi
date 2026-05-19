import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def get_waveform_data(letter, df):
    """Bir harf için Relax→Action→Relax zaman serisini oluşturur."""
    baseline_label = 'A' if letter == 'B' else 'B'
    cols = ['f1', 'f2', 'f3', 'f4', 'f5', 'ax', 'ay']

    relax_data = df[df['label'] == baseline_label].head(30)[cols].reset_index(drop=True)

    all_action = df[df['label'] == letter][cols].reset_index(drop=True)
    n_total = len(all_action)
    if n_total >= 40:
        indices = np.linspace(0, n_total - 1, 40, dtype=int)
        action_data = all_action.iloc[indices].reset_index(drop=True)
    else:
        action_data = all_action.head(40).reset_index(drop=True)

    if len(relax_data) < 30 or len(action_data) < 40:
        return None

    ts_data = pd.concat([relax_data.copy(), action_data.copy(), relax_data.copy()], ignore_index=True)
    return ts_data


def plot_on_axis(ax, ts_data, letter, is_noisy):
    """Bir subplot eksenine waveform çizer."""
    cols_flex = ['f1', 'f2', 'f3', 'f4', 'f5']
    colors_flex = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    labels_flex = ['Thumb (f1)', 'Index (f2)', 'Middle (f3)', 'Ring (f4)', 'Pinky (f5)']
    time_axis = np.arange(len(ts_data))

    for i, col in enumerate(cols_flex):
        ax.plot(time_axis, ts_data[col], label=labels_flex[i], color=colors_flex[i], linewidth=1.8, alpha=0.9)

    # İvme eksenlerini görsel ölçekle
    for col, color, name in [('ax', '#17becf', 'Acc X (ax)'), ('ay', '#e377c2', 'Acc Y (ay)')]:
        raw = ts_data[col]
        c_min, c_max = raw.min(), raw.max()
        if c_max - c_min > 0:
            scaled = 500 + 3000 * (raw - c_min) / (c_max - c_min)
        else:
            scaled = pd.Series([2000.0] * len(raw))
        ax.plot(time_axis, scaled, label=name, color=color, linewidth=1.8, linestyle='--', alpha=0.9)

    ax.axvspan(0, 30, color='gray', alpha=0.07)
    ax.axvspan(30, 70, color='green', alpha=0.07)
    ax.axvspan(70, 100, color='gray', alpha=0.07)

    ax.annotate('Relax', xy=(15, 200), xytext=(15, 1300),
                arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=6),
                fontsize=9, fontweight='bold', color='red', ha='center')
    ax.annotate(f"'{letter}'", xy=(50, 3800), xytext=(50, 2400),
                arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=6),
                fontsize=9, fontweight='bold', color='red', ha='center')
    ax.annotate('Relax', xy=(85, 200), xytext=(85, 1300),
                arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=6),
                fontsize=9, fontweight='bold', color='red', ha='center')

    ax.set_xlim([-2, 102])
    ax.set_ylim([-100, 4200])
    ax.grid(True, linestyle=':', alpha=0.4)
    ax.set_xlabel('Time (Frame – Birimsiz)', fontsize=9)

    tag = "GÜRÜLTÜLÜ (%40 Gaussian Noise)" if is_noisy else "GÜRÜLTÜSÜZ (Ham ADC Verisi)"
    ax.set_title(tag, fontsize=11, fontweight='bold',
                 color='#c0392b' if is_noisy else '#27ae60')


def create_comparison_waveform(letter, df):
    """Bir harf için yan yana (gürültüsüz | gürültülü) tek görsel üretir."""
    print(f"  '{letter}' harfi yan yana karşılaştırma grafiği üretiliyor...")

    ts_clean = get_waveform_data(letter, df)
    if ts_clean is None:
        print(f"    HATA: '{letter}' için veri yetersiz.")
        return

    # Gürültülü versiyon: aynı veriyi kopyalayıp %40 Gaussian gürültü ekle
    ts_noisy = ts_clean.copy()
    np.random.seed(hash(letter) % 2**31)
    cols = ['f1', 'f2', 'f3', 'f4', 'f5', 'ax', 'ay']
    for col in cols:
        col_std = ts_noisy[col].std()
        if col_std == 0:
            col_std = ts_noisy[col].mean() * 0.01
        ts_noisy[col] = ts_noisy[col] + np.random.normal(0, col_std * 0.40, len(ts_noisy))

    # --- Yan yana 2 subplot ---
    fig, (ax_clean, ax_noisy) = plt.subplots(1, 2, figsize=(20, 7), sharey=True)

    plot_on_axis(ax_clean, ts_clean, letter, is_noisy=False)
    plot_on_axis(ax_noisy, ts_noisy, letter, is_noisy=True)

    ax_clean.set_ylabel('Flex (Raw ADC: 0–4095) / IMU (Scaled)', fontsize=10, fontweight='bold')

    # Ortak legend — sağ grafik üzerinden al
    handles, labels = ax_noisy.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=7, frameon=True,
               facecolor='white', edgecolor='gray', fontsize=9,
               bbox_to_anchor=(0.5, -0.02))

    fig.suptitle(f"FIGURE 5. '{letter}' Harfi — Gürültüsüz vs Gürültülü Sinyal Karşılaştırması",
                 fontsize=14, fontweight='bold', y=1.01)

    plt.tight_layout()
    filename = f'grafik_6_waveform_compare_{letter}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Kaydedildi: {filename}")


def create_all_waveforms():
    try:
        df = pd.read_csv('isaret_dili_izleme/veriokumayeni.csv', on_bad_lines='skip').dropna()
        print(f"Veri seti yüklendi: {len(df)} satır")
        print(f"Sınıflar: {sorted(df['label'].unique())}")
    except Exception as e:
        print(f"Hata: Veri yüklenemedi. {e}")
        return

    letters = ['A', 'B', 'C', 'D', 'E', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'O', 'R', 'S', 'T', 'U', 'V', 'Y', 'Z']

    print("\n===== YAN YANA KARŞILAŞTIRMALI WAVEFORM GRAFİKLERİ =====")
    for l in letters:
        create_comparison_waveform(l, df)

    print(f"\nToplam {len(letters)} karşılaştırmalı grafik üretildi.")


if __name__ == "__main__":
    create_all_waveforms()
