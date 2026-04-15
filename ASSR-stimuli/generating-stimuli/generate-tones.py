""" Generates 500 ms click trains (1 ms rarefaction clicks) at 40Hz 

parameters taken from AMP SCZ:
https://www.nature.com/articles/s41537-025-00622-0#Sec9
--> check if ok/ask tineke?
"""

import numpy as np
from scipy.io import wavfile
from pathlib import Path

# ----------------- STEP 0: PARAMETERS -----------------
############# should this fs be changed? to what
fs = 44000  # sampling rate (Hz)
#############



click_ms = 1.0            # click duration in milliseconds
trial_duration_s = 0.5    # 500 ms click-train

# outdir should be in the same folder as this script
out_dir = Path(__file__)
out_dir.mkdir(parents=True, exist_ok=True)

# amplitudes
max_int16 = np.iinfo(np.int16).max
click_amp = 0.9                # amplitude (0..1) of the impulse

# frequencies to create (Hz) and filenames
freqs = {
   # 20: out_dir / "clicktrain_20Hz_500ms.wav",
   # 60: out_dir / "clicktrain_60Hz_500ms.wav",
   40: out_dir / "clicktrain_40Hz_500ms.wav"
}

# ----------------- STEP 1: HELPER - create single click waveform -----------------
def make_rarefaction_click(fs, click_ms, amp=1.0):
    """
    Make a short 1 ms 'rarefaction' click: starts with a negative deflection.
    We create a short impulse spread over click_samples to avoid extreme single-sample impulses.
    """
    click_samples = int(round(fs * (click_ms / 1000.0)))
    if click_samples < 1:
        click_samples = 1
    # create a short raised-cosine (half-Hann) windowed negative pulse
    t = np.arange(click_samples)
    # half-Hann from 0..1 then negate -> negative-first deflection
    pulse = -np.hanning(click_samples)  # negative deflection (rarefaction)
    pulse = pulse / np.max(np.abs(pulse))  # normalize to -1..0..-1 shape
    pulse = pulse * amp
    return pulse.astype(np.float32)

# ----------------- STEP 2: CREATE AND SAVE TRAIN -----------------
for freq_hz, out_path in freqs.items():
    period_samples = int(round(fs / freq_hz))  # samples between click onsets
    total_samples = int(round(trial_duration_s * fs))
    click = make_rarefaction_click(fs, click_ms, amp=click_amp)

    # initialize waveform (float)
    waveform = np.zeros(total_samples, dtype=np.float32)

    # place clicks at 0, period_samples, 2*period_samples, ... while keeping within total_samples
    pos = 0
    while pos < total_samples:
        # add click (ensure we don't overflow the buffer)
        end_pos = pos + len(click)
        if end_pos <= total_samples:
            waveform[pos:end_pos] += click
        else:
            # truncated click at end if necessary
            waveform[pos:total_samples] += click[:total_samples - pos]
        pos += period_samples

    # normalize (to avoid clipping) and convert to int16 for wavfile.write
    max_val = np.max(np.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val * 0.95  # scale to 95% of int16 range
    waveform_int16 = np.int16(waveform * max_int16)

    # write file
    wavfile.write(str(out_path), fs, waveform_int16)
    print(f"Saved {out_path} (freq {freq_hz} Hz, {len(waveform_int16)} samples)")

print("All click trains written.")
