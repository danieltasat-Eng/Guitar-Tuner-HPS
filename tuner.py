import sounddevice as sd
import numpy as np

# Audio and FFT Settings
FREQ_SAMPLE = 48000       # Sampling rate in Hz
CONCERT_PITCH = 440       # Reference frequency for A4
WINDOW_SIZE = FREQ_SAMPLE # One second window for analysis
ALL_NOTES = ['A','A#','B','C','C#','D','D#','E','F','F#','G','G#']
HARMONIC_NUM = 4          # Number of harmonics for HPS multiplication
HANN_WINDOW = np.hanning(WINDOW_SIZE) # Window function to reduce spectral leakage

# Zero-padding for interpolation (achieving 0.1Hz frequency resolution)
N_FFT = WINDOW_SIZE * 10
DELTA_FREQ = FREQ_SAMPLE / N_FFT 

# Global buffers
window_samples = np.zeros(WINDOW_SIZE)
history = [] 

def find_closest_note(pitch):
    """
    Calculates the nearest musical note based on the detected frequency.
    Uses a logarithmic scale to determine semitones relative to A4 (440Hz).
    """
    if pitch <= 0 or np.isnan(pitch):
        return "---", 0.0
        
    # Calculate distance in semitones from reference pitch
    semi_tones = int(np.round(12 * np.log2(pitch / CONCERT_PITCH)))
    
    # Calculate octave and note name
    octave = 4 + (semi_tones + 9) // 12
    closest_note = ALL_NOTES[semi_tones % 12] + str(octave)
    
    # Theoretical frequency of the target note
    closest_pitch = CONCERT_PITCH * 2**(semi_tones / 12)
    return closest_note, closest_pitch

def process_audio(indata, frames, time, status):
    """
    Callback function called by sounddevice for every audio block.
    Performs real-time DSP: Windowing -> FFT -> HPS -> Pitch Detection.
    """
    global history, window_samples

    if status:
        print(status)
        
    # Use mono channel and maintain a sliding window of samples
    new_data = indata[:, 0]
    window_samples = np.concatenate((window_samples, new_data))
    window_samples = window_samples[-WINDOW_SIZE:] 
    
    # Root Mean Square (RMS) to check if input signal is loud enough
    volume = np.sqrt(np.mean(window_samples**2))
    
    if volume > 0.005: 
        # Apply Hann window to minimize discontinuities at the edges
        hann_samples = window_samples * HANN_WINDOW 
        
        # Compute Magnitude Spectrum using RFFT (Real FFT)
        fft_data = abs(np.fft.rfft(hann_samples, n=N_FFT))
        
        # Harmonic Product Spectrum (HPS) Algorithm:
        # Highlights fundamental frequency by multiplying downsampled versions of the spectrum
        hps_spec = fft_data.copy() 
        hps_spec = hps_spec**2 # Energy spectrum
        
        for i in range(2, HARMONIC_NUM + 1): 
            down_sampled = fft_data[::i]
            hps_spec = hps_spec[:len(down_sampled)]
            hps_spec = hps_spec * down_sampled
            
        # Identify the peak frequency index
        max_index = np.argmax(hps_spec) 
        dominant_freq = max_index * DELTA_FREQ 
        
        if dominant_freq > 0:
            tuning_note, target_pitch = find_closest_note(dominant_freq)
            
            # Stabilization: use the most frequent note in the last 10 detections
            history.append(tuning_note)
            history = history[-10:]
            stable_note = max(set(history), key=history.count)
            
            output = f"\rClosest note: {stable_note:4} {dominant_freq:6.1f} / {target_pitch:5.1f} Hz          "
            print(output, end="", flush=True)

# Main Execution Loop
try:
    print("Starting Guitar Tuner... Press Ctrl+C to stop.")
    # blocksize=12000 provides a good balance between latency and processing time
    with sd.InputStream(channels=1, callback=process_audio, 
                        samplerate=FREQ_SAMPLE, blocksize=12000):
        while True:
            sd.sleep(500)
except KeyboardInterrupt:
    print("\nStopped by user.")
