""" Generates
    500 ms click trains (1 ms rarefaction clicks) at 40Hz 

parameters taken from AMP SCZ:
https://www.nature.com/articles/s41537-025-00622-0#Sec9
which states "Each click train comprised 1 ms rarefaction clicks presented every 25 ms, yielding a 40-Hz stimulation frequency to drive the ASSR. Participants were instructed to maintain visual focus on a fixation cross on the computer display while passively listening to click trains."
"""

import numpy as np
from scipy.io import wavfile
from pathlib import Path

#############
fs = 48000  # sampling rate (Hz)
# dario: I think the device accept values from 8k to 96k. For the purpose of the assr, i think you could use 44.1 or 48k that should not matter as both are more than sufficient. I think what is critical is that you select correctly the sampling rate based on how you created your file
#############





# outdir should be in the same folder as this script
out_dir = Path(__file__).resolve().parent

click_ms = 1.0            # click duration in milliseconds
trial_duration_s = 0.5    # 500 ms click-train
period_ms = 25.0          # click-onset spacing in milliseconds

# amplitudes
max_int16 = np.iinfo(np.int16).max
click_amp = 0.9                # amplitude (0..1) of the impulse

# WHAT TO MAKE? frequencies to create (Hz) and filenames
freqs = {
   # 20: out_dir / "clicktrain_20Hz_500ms.wav",
   # 60: out_dir / "clicktrain_60Hz_500ms.wav",
   40: out_dir / "clicktrain_40Hz_500ms.wav"
}

# HELPER GENERATE IT! create single click waveform
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


# CREATE AND SAVE
for freq_hz, out_path in freqs.items():
    period_samples = int(round(fs * (period_ms / 1000.0)))  # samples between click onsets
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

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(out_path, fs, waveform_int16)
    print(f"Wrote {out_path} ({len(waveform_int16)} samples at {fs} Hz)")


print("All click trains written.")
