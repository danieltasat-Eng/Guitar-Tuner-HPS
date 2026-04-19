import numpy as np
import matplotlib.pyplot as plt

# Basic settings
fs = 8000
N = 8000
freq_base = 110  #The frequency we want

# Creating harmonics to visualize
t = np.linspace(0, 1, fs)
signal = (1.0 * np.sin(2 * np.pi * freq_base * t) + 
          1.5 * np.sin(2 * np.pi * (freq_base * 2) * t) + 
          1.2 * np.sin(2 * np.pi * (freq_base * 3) * t))

# FFT calculation
fft_res = np.abs(np.fft.rfft(signal))
freqs = np.fft.rfftfreq(N, 1/fs)

# HPS scaling
hps_2 = fft_res[::2]
hps_3 = fft_res[::3]

# Adjustments for multipling
L = len(hps_3)
hps_final = fft_res[:L] * hps_2[:L] * hps_3[:L]

# Graphic visualization - first one shows the harmonics
plt.figure(figsize=(12, 8))
plt.subplot(2, 1, 1)
plt.plot(freqs[:500], fft_res[:500])
plt.title("Original FFT (Notice the harmonics are louder than the base!)")
plt.grid(True)

# Second plot shows the right harmonic after HPS
plt.subplot(2, 1, 2)
plt.plot(freqs[:len(hps_final)][:500], hps_final[:500], color='orange')
plt.title("After HPS (The base frequency 110Hz is now the clear winner)")
plt.xlabel("Frequency [Hz]")
plt.grid(True)

plt.tight_layout()
plt.show()
