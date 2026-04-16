import os, csv, random, ctypes
import numpy as np
import soundfile as sf
from pathlib import Path
from psychopy import visual, core, event, monitors, logging, sound

from pypixxlib.datapixx import DATAPixx3

# =================================================================
# TO BE CHANGED BY EXPERIMENTER
# 
# change/run this script ONLY once for frist run,
# for second run only change PAS to ATT and just SAVE
# =================================================================
SUB = "framerate_test"
CONDITION = "ATT"   # "PAS", then "ATT" (ATT=attVIS=attend to visual stim)
# =================================================================






MRS = 0     # 0=no, 1=yes

# -------------------------- PATHS -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # script location
STIM_DIR = os.path.join(BASE_DIR, "ASSR-stimuli", "sounds") 
SUB_DIR  = os.path.join(BASE_DIR, "ASSR-data", SUB)
os.makedirs(SUB_DIR, exist_ok=True) # make the folder if doesn't exist already

# -------------------------- TRIGGERS (161-254) -----------------------
# use trigger numbers below 255 so it stays onyl in the G channel
# and use trigger numbers above 160 so it actually goes UP. To make the signal go UP (to a higher voltage or a higher integer value in analysis), you must use numbers strictly greater than 160.
TRIG_START        = 162 # maybe leave out after testing phase

TRIG_SOUND_no_arr = 200  # Sound presented with only fixation dot
TRIG_L_ARR        = 220  # Sound presented simultaneously with a LEFT arrow
TRIG_R_ARR        = 240  # Sound presented simultaneously with a RIGHT arrow

TRIG_RESPONSE     = 250  # Participant response (red/right button press)

# ------------------- TRIAL STRUCTURE ----------------------------
SOA = 1.5           # sec
ARROW_DUR = 0.150     # or 200ms?

N_NO_ARROW = 145    # number of no arrow trials 
N_LEFT = 29         # number of left arrows
N_RIGHT = 29        # number of right arrows

# -------------------------- GENERATE TRIAL SEQUENCE --------------------------
def create_participant_sequences(sub_dir, sub_id, n_no_arrow, n_left, n_right):
    """
    Generates the ASSR trial sequence for the participant and saves it to a master CSV.
    This is run only once per participant.

    Pseudorandomization logic:
        - Total trials: 203 (145 no-arrow, 29 left-arrow, 29 right-arrow)
        - First 4 trials are always no-arrow (to avoid early arrows)
        - The remaining 199 trials are shuffled with the constraint that 
                - no two arrow trials can be consecutive
                - there can only be a maximum of 3 consecutive same-direction arrows across the entire experiment
    
    The final sequence is saved as a CSV with columns: "trial_index", "arrow". "arrow" can be "none", "left", or "right".
    """
    master_sequence_file = os.path.join(sub_dir, f"{sub_id}_ASSR_master_trial_sequence.csv")
    
    if os.path.exists(master_sequence_file):
        print(f"INFO: Master sequence for {sub_id} already exists. No action taken.")
        return

    print(f"GENERATING: New master sequence file for participant {sub_id}...")

    base = ["none"] * n_no_arrow
    slots = list(range(3, len(base) + 1)) # Start at 3 to ensure first 3 trials are "none"
    arrow_slots = random.sample(slots, n_left + n_right)
    arrows = (["left"] * n_left) + (["right"] * n_right)

    # Enforce max 3 consecutive same-direction arrows
    valid = False
    while not valid:
        random.shuffle(arrows)
        valid = True
        run_length = 1
        for i in range(1, len(arrows)):
            if arrows[i] == arrows[i-1]:
                run_length += 1
                if run_length > 3:
                    valid = False
                    break
            else:
                run_length = 1

    sequence = base.copy()
    offset = 0
    for slot, arrow in sorted(zip(arrow_slots, arrows)):
        sequence.insert(slot + offset, arrow)
        offset += 1

    # Convert to list of dictionaries for saving
    all_trials = [{"trial_index": i+1, "arrow": stim_type} for i, stim_type in enumerate(sequence)]
    
    with open(master_sequence_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["trial_index", "arrow"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_trials)
    
    print(f"SUCCESS: Master sequence file created at '{master_sequence_file}'")

# -------------------------- INITIALIZE VPIXX DEVICE --------------------------
device = DATAPixx3()

## PIXEL MODE
device.dout.enablePixelModeGB() # enable once
device.updateRegisterCache() 

## BUTTONBOX
# Initialize buttons
if MRS == 0:
    # Working codes in Lab maestro Simulator
    buttonCodes = {65527:'blue', 65533:'yellow', 65534:'red', 65531:'green', 65519:'white', 65535:'button release'}
    exitButton  = 'white'

if MRS == 1:
    # Button codes in MSR
    buttonCodes = { 65528: 'blue', 65522: 'yellow', 65521: 'red', 65524: 'green', 65520: 'button release' }

myLog = device.din.setDinLog(12e6, 1000) # uses the first 8 DIN slots for buttonbox
device.din.startDinLog()
device.updateRegisterCache()

## MONITOR
def stim_monitor():
    if MRS == 0:
        # "Laptop": {"width_cm": 34.5, "dist_cm": 40, "res_pix": [1920, 1080], "name": "Laptop", "refresh_rate": 60, "screen_idx": 0},
        viewing_distance_cm 	= 40
        monitor_width_cm    	= 34.5
        monitor_size_pix    	= [1920, 1080] 
        monitor_name        	= "Laptop"
        refresh_rate        	= 60
        screen_number           = 1 # 0 or 2 for this screen, 1 for external screen

        # Set Monitor
        monitor = monitors.Monitor(monitor_name) 
        monitor.setWidth(monitor_width_cm)  
        monitor.setDistance(viewing_distance_cm)  
        monitor.setSizePix(monitor_size_pix)
        monitor.save()

        # Set monitor and return information
        return {
            "monitor_size_pix":     monitor_size_pix,
            "monitor_name":         monitor_name,
            "refresh_rate":         refresh_rate,
            "viewing_distance_cm":  viewing_distance_cm,
            "monitor_width_cm":     monitor_width_cm,
            "screen_number":        screen_number
        }

    if MRS == 1:
        # "OPM": {"width_cm": 78, "dist_cm": 122, "res_pix": [1920, 1080], "name": "OPM_Monitor", "refresh_rate": 120, "screen_idx": 2}

        # Monitor/Experiment settings 
        viewing_distance_cm 	= 122
        monitor_width_cm    	= 78
        monitor_size_pix    	= [1920, 1080] 
        monitor_name        	= "OPM_Monitor"
        refresh_rate        	= 120
        screen_number           = 2 # 01.22.2026

        # Set Monitor
        monitor = monitors.Monitor(monitor_name) 
        monitor.setWidth(monitor_width_cm)  
        monitor.setDistance(viewing_distance_cm)  
        monitor.setSizePix(monitor_size_pix)
        monitor.save()

        # Set monitor and return information
        return {
            "monitor_size_pix":     monitor_size_pix,
            "monitor_name":         monitor_name,
            "refresh_rate":         refresh_rate,
            "viewing_distance_cm":  viewing_distance_cm,
            "monitor_width_cm":     monitor_width_cm,
            "screen_number":        screen_number
        }


# -------------------------- AUDIO SETTINGS --------------------------
FS = 48000 # audio sample rate. audio_sampling_frequency # chage to new one, 44000 i think

AUDIO_BASE_ADDR = int(16e6) # adress in vpixx device (where the audio gets stored)

## 1. LOAD AUDIO FILES AS FLOAT32 INTO VPixx AUDIO BUFFER
#  needed for preload_tones one below (load .wav files as float32 as vpixx audio buffer expects that. also convert to mono if needed, and get the peak value for later gain calculations)
def _load_wav_float32(audiofilespath):
    # Load .wav tone files
    audiofile, samplingfreq = sf.read(audiofilespath, dtype='float32')
    if audiofile.ndim > 1:  # convert to mono if needed
        audiofile   = audiofile.mean(axis=1).astype('float32')
    # create array
    audiofile = np.ascontiguousarray(audiofile, dtype=np.float32)
    peak = float(np.max(np.abs(audiofile))) or 1.0 # get max value

    return audiofile, int(samplingfreq), peak
    
#  this actually loads them into buffer + creates registry for all samples 
def preload_tones(vpdevice, paths):
    # preload tones into buffer
    reg = {}
    vpdevice.audio.stopSchedule()

    # check length
    loaded          = {}
    total_samples   = 0
    common_fs       = None # assume same samling freq ---------------> dario ADAPT: is this ok? or 44100hz ? change also for MMN???????????????????????????????? o

    for name, p in paths.items():
        x, fs, peak = _load_wav_float32(p)
        x = np.asarray(x, dtype=np.float32).squeeze()
        
        if x.ndim != 1:
            raise ValueError(f"Tone '{name}' is not mono (shape {x.shape})")
            
        if common_fs is None:
            common_fs = fs
        elif fs != common_fs:
            raise ValueError(
                f"All tones must have same fs; '{name}' has {fs}, expected {common_fs}"
            )
            
        n_samples       = len(x)
        loaded[name]    = (x, fs, peak, n_samples)
        total_samples   += n_samples
        
    base_addr = AUDIO_BASE_ADDR  # start address to be written
    buf_bytes = int(vpdevice.audio.getBufferSize())
    
    print(f"[AUDIO] base address (bytes): {base_addr}")
    print(f"[AUDIO] buffer size (bytes): {buf_bytes}")
    print(f"[AUDIO] total samples to write: {total_samples} -> {total_samples * 2} bytes")
    
    bytes_needed = total_samples * 2 # why this line?

    # build one big bank
    all_arrays = [loaded[name][0] for name in paths.keys()]
    audio_bank = np.concatenate(all_arrays).astype(np.float32)

    # writes at 16e6 internally; passing base_addr keeps intent consistent
    vpdevice.audio.writeAudioBuffer(audio_bank, bufferAddress=base_addr)
    vpdevice.updateRegisterCache()

    # offsets + registry
    offset_samples = 0
    for name in paths.keys():
        x, fs, peak, n_samples = loaded[name]
        
        addr_bytes = base_addr + offset_samples * 2
        
        reg[name] = {
            "addr": addr_bytes,
            "offset_samples": offset_samples,
            "n": n_samples,
            "fs": fs,
            "peak": peak,
            "gain": None,
        }
        
        print(
            f"[AUDIO] tone '{name}': addr={addr_bytes}, "
            f"n={n_samples}, offset_samples={offset_samples}"
        )
        
        offset_samples += n_samples
    return reg


## 2. MAKES VOLUME SAME FOR EACH PARTICIPANT
#  just loads csv
def load_threshold_csv(subjectpath):
    # Load Subject-Specific Hearing Threshold
    with open(subjectpath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
    return {
        "subject_id": row["subject_id"],
        "threshold_db": float(row["threshold_db"]),
        "threshold_amplitude": float(row["threshold_amplitude"]),
        }

#  then adds gains to regsitry
def assign_subject_gains(in_audio_reg, threshold_linear, per_tone_dBSL, master=1.0):
    # include gain in the register
    for name, info in in_audio_reg.items():
        peak            = info.get('peak', 1.0)
        this_dBSL       = per_tone_dBSL.get(name)
        gain            = master * threshold_linear * (10.0 ** (this_dBSL / 20.0)) / max(peak, 1e-12)
        info['gain']    = float(max(0.0, min(1.0, gain)))  # clamp to [0,1]

    return in_audio_reg

# --------------------------PRELOAD STIMULI AND TEXT ---------------
# dB_SL=60 or 65 or 50
def preload_stimuli(win, stimulipath, subjectpath, vpdevice, dB_SL=60):
    fixation_angle = 1 # 0.5 # 0.5 looks good, maybe a bit too small? ----> ADAPT

    if MRS == 0:
        # ======= AUDITORY
        FS = 48000 
        HEARING_THRESHOLD = 0.0007

        DB_ABOVE_THRESHOLD = 60
        attenuation_factor = 10 ** (DB_ABOVE_THRESHOLD / 20)
        SOUND_VOLUME = HEARING_THRESHOLD * attenuation_factor
        SOUND_VOLUME = min(SOUND_VOLUME, 1.0)

        if SOUND_VOLUME > 1.0:
            print(f"WARNING: volume {SOUND_VOLUME:.2f} too high, capping at 1.0")
            SOUND_VOLUME = 1.0
        else:
            print(f"Sound volume set to {SOUND_VOLUME:.4f}")

        clicktrain_file = os.path.join(STIM_DIR, "clicktrain_40Hz_500ms.wav")
        Audio = sound.Sound(str(clicktrain_file), sampleRate=FS, volume=SOUND_VOLUME)

        # ======= VISUAL
        fix_dot = visual.Circle(win, radius=fixation_angle/2, fillColor="black", lineColor="black", pos=(0, 0), units="deg")
        arrow_vertices = [(-0.5, 0.8), (0.5, 0.0), (-0.5, -0.8)]
        arrow_stim = visual.ShapeStim(win, vertices=arrow_vertices, closeShape=True, fillColor="black", lineColor="black")
        
        return {"Audio": Audio, "fix_dot": fix_dot, "arrow_stim": arrow_stim}
    
    if MRS == 1:
        # ======= AUDITORY
        # create tone registers
        audio_reg = preload_tones(vpdevice, {
           'clicktrain': os.path.join(stimulipath, 'sounds', 'clicktrain_40Hz_500ms.wav')
        })

        # load threshold & add gains
        thr_info  = load_threshold_csv(os.path.join(subjectpath, "round_2_hearing_threshold_1000.csv"))
        thr_lin   = thr_info["threshold_amplitude"]
        audio_reg = assign_subject_gains(audio_reg, threshold_linear=thr_lin, per_tone_dBSL={'Aud_X': dB_SL, 'Aud_Y': dB_SL, 'Aud_FB': dB_SL-10})
        print(audio_reg)        

        # ======= VISUAL
        fix_dot = visual.Circle(win, radius=fixation_angle/2, fillColor="black", lineColor="black", pos=(0, 0), units="deg")
        arrow_vertices = [(-0.5, 0.8), (0.5, 0.0), (-0.5, -0.8)]
        arrow_stim = visual.ShapeStim(win, vertices=arrow_vertices, closeShape=True, fillColor="black", lineColor="black")
        
        return {"Audio": audio_reg, "fix_dot": fix_dot, "arrow_stim": arrow_stim}
    

# preload text
def preload_txt(win):   
   txt_intro_PAS = visual.TextStim(win, text="Schauen Sie während des Experiments auf die Mitte des Bildschirms. \n\n Drücken Sie den roten/rechten Knopf um zu starten.", height=1, pos=(0, 0), units='deg', color='black')
   txt_intro_ATT = visual.TextStim(win, text="Drücken Sie rechten/roten Knopf, wenn Sie einen Pfeil sehen, der nach rechts zeigt: ▶ \n\n Drücken Sie den roten/rechten Knopf um zu starten.", height=1, pos=(0, 0), units='deg', color='black')
   txt_finished = visual.TextStim(win, text="Dieser Durchgang ist beendet.\n Vielen Dank. \n\n Bitte warten Sie auf Anweisungen.", height=1, pos=(0, 0), units='deg', color='black')
   
   return {"txt_intro_PAS": txt_intro_PAS, "txt_intro_ATT": txt_intro_ATT, "txt_finished": txt_finished}


# =================================================================
# This block makes the script executable for one-time setup
# =================================================================
if __name__ == "__main__":
    print("=====================================================")
    print(f"RUNNING ONE-TIME SETUP FOR PARTICIPANT: {SUB}")
    print("=====================================================")
    # Ensure the subject's directory exists
    os.makedirs(SUB_DIR, exist_ok=True)
    # should check if the file exists already
    if os.path.exists(os.path.join(SUB_DIR, f"{SUB}_ASSR_master_trial_sequence.csv")):
        print(f"WARNING: Master sequence file for {SUB} already exists! No action taken.")
        # does the script close anyway or do i need to close it with a line here?
        # exit()
    else:
        # Create the master sequence file using constants from the top of the script
        create_participant_sequences(SUB_DIR, SUB, N_NO_ARROW, N_LEFT, N_RIGHT)
        print(f"\nSetup complete. File created: {SUB}_ASSR_master_trial_sequence.csv. You can now run the ASSR_RUN paradigm script.")