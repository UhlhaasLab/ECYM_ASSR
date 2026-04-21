""" Generates
    500 ms click trains (1 ms rarefaction clicks) at 40Hz 

parameters taken from AMP SCZ:
https://www.nature.com/articles/s41537-025-00622-0#Sec9
which states "Each click train comprised 1 ms rarefaction clicks presented every 25 ms, yielding a 40-Hz stimulation frequency to drive the ASSR. Participants were instructed to maintain visual focus on a fixation cross on the computer display while passively listening to click trains."



- look at powerspectral density fft of the file. shoude peak at 40hz
"""

import numpy as np
from scipy.io import wavfile
from pathlib import Path

# wavfile package check it out

# ===================== PARAMETERS =====================
fs = 48000                  # sampling rate (Hz)
freq_hz = 40                # target ASSR frequency (Hz)
click_ms = 1.0              # click duration (ms) so i have a 1ms click every 25ms, which gives me 40Hz stimulation frequency
trial_duration_s = 0.5      # total duration (s)



click_amp = 0.99             # amplitude (0..1)
# make click amp 0.99
max_int16 = np.iinfo(np.int16).max
print("max int16 value:", max_int16)

# output path
out_dir = Path(__file__).resolve().parent
out_path = out_dir / "clicktrain_40Hz_500ms.wav"


# ===================== CLICK GENERATION =====================
def make_rarefaction_click(fs, click_ms, amp=1.0):
    """
    Create a short 'rarefaction' click:
    - negative-first deflection (common in auditory research)
    - windowed (Hann) to avoid spectral splatter from a single-sample impulse
    """
    click_samples = max(1, int(round(fs * click_ms / 1000.0)))

    # create smooth pulse (Hann window), then invert → negative-first
    pulse = -np.hanning(click_samples)

    # normalize to [-1, 1] range and scale by amplitude
    pulse = pulse / np.max(np.abs(pulse))
    pulse = pulse * amp

    return pulse.astype(np.float32)


# ===================== TIMING =====================
# Exact period in samples (integer division guarantees stable spacing)
period_samples = fs // freq_hz   # e.g., 48000 / 40 = 1200 samples exactly.

# Total number of samples in the trial
total_samples = int(round(trial_duration_s * fs)) # = 24000

# Number of clicks (integer, avoids drift)
n_clicks = total_samples // period_samples  # e.g., 24000 // 1200 = 20 clicks 


# ===================== WAVEFORM CONSTRUCTION =====================
waveform = np.zeros(total_samples, dtype=np.float32)    # putting 0s to the lenght of my signal
click = make_rarefaction_click(fs, click_ms, amp=click_amp)

# Place each click at exact multiples of period_samples
# first click is a 0. then at the position of the second click, I have 1200 samples (which is 25ms), then at the position of the third click, I have 2400 samples (which is 50ms), and so on. this way I avoid any cumulative timing errors that could arise from using time-based loops or floating-point calculations.
for i in range(n_clicks):
    pos = i * period_samples  # exact placement → no cumulative error

    end_pos = pos + len(click)

    if end_pos <= total_samples:
        waveform[pos:end_pos] += click
    else: # if the click would exceed the total length of the waveform, we only add the portion of the click that fits within the remaining samples. this ensures we don't get an index error and that we still include as much of the final click as possible without exceeding the buffer.
        # truncate final click if it exceeds buffer
        # DOUBLECHECK
        waveform[pos:total_samples] += click[:total_samples - pos]


# ===================== NORMALIZATION & EXPORT =====================
# Prevent clipping while maximizing dynamic range
# max_val = np.max(np.abs(waveform)) 
# if max_val > 0:
#     waveform = waveform / max_val * 0.95

waveform_int16 = np.int16(waveform * max_int16)

out_path.parent.mkdir(parents=True, exist_ok=True)
wavfile.write(out_path, fs, waveform_int16) # function wavfile.write takes the output path, sampling rate, and the waveform data (as int16) and writes it to a .wav file. The resulting file will contain the 500 ms click train at 40 Hz with the specified parameters.
# 16-bit PCM format is standard for .wav files and ensures compatibility with most audio software and hardware. The waveform is scaled to the full range of int16 to maximize audio quality without clipping, given the specified click amplitude.

print(f"Wrote {out_path}")
print(f"fs={fs} Hz | freq={freq_hz} Hz | period={period_samples} samples | clicks={n_clicks}")