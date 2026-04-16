"""
to do
- check if trial seq is correct

- interpolate=False . In your draw_pixel function, you have a comment: interpolate must be set to FALSE. This is crucial. If the GPU "blurs" (interpolates) your trigger pixel with the neighboring gray pixels, the color value will change, and the DataPixx will read the wrong trigger number. Ensure your visual.Rect or visual.Window has anti-aliasing/interpolation disabled for that specific area.

- move stuff to init

TINEKE:
- for now it sends triggers when correct response. can take out right?
"""

import random, csv, time, os
from psychopy import visual, core, event, sound

from ASSR_init import (SUB, CONDITION, MRS, SUB_DIR, STIM_DIR, SOA, ARROW_DUR,
                        # triggers
                        TRIG_START,
                        TRIG_SOUND_no_arr, TRIG_L_ARR, TRIG_R_ARR, 
                        TRIG_RESPONSE, 
                        # vpixx
                        device, buttonCodes, myLog, stim_monitor,
                        # preload
                        preload_stimuli, preload_txt)

from utils.pixel_mode           import pixel_time, trigger_to_RGB, draw_pixel, print_trigger_info
from utils.buttons              import collect_response, flush_buttons
from utils.escape_cleanup_abort import check_abort, cleanup

# -------------------- GENERAL --------------------
timestamp = time.strftime('%Y%m%d_%H%M%S')
psychopy_clock = core.Clock()

# -------------------- WINDOW --------------------------------
monitor_settings = stim_monitor()
# set fullscr to True in MSR
win = visual.Window(
    monitor=monitor_settings['monitor_name'], size=monitor_settings['monitor_size_pix'], 
    fullscr=True, 
    units="deg", 
    #color=[212, 212, 212],
    color= [160, 160, 160], # slightly darker gray to increase contrast with trigger pixel
    colorSpace='rgb255', 
    #colorSpace='rgb',
    #colorSpace='rgb1',
    screen=monitor_settings["screen_number"]
)
win.mouseVisible = False
mouse = event.Mouse(visible=False) 

# for frame rate timing (frameDur = 1.0 / win.getActualFrameRate())
monitor_rr = monitor_settings["refresh_rate"]
frameDur = 1.0 / monitor_rr # if monitor_rr else win.monitorFramePeriod    # use actual refresh rate if available, otherwise fallback to PsychoPy's estimate
TRIG_FRAMES = 2 # pixel should show for 2 frames

# -------------------- LOGGING SETUP --------------------
log_file = os.path.join(SUB_DIR, f"{SUB}_{CONDITION}_log_{timestamp}.csv")
log_f = open(log_file, "w", newline="", encoding="utf-8")
log_writer = csv.writer(log_f)
log_writer.writerow(["trial_index","arrow","sound_onset_psy","sound_onset_dev",
                     "arrow_onset_psy","arrow_onset_dev","response_key","rt_psy","rt_dev"])

# -------------------- PRELOAD TEXT & STIMULI --------------------
txt_dict = preload_txt(win)
instr = txt_dict["txt_intro_PAS"] if CONDITION == "PAS" else txt_dict["txt_intro_ATT"]
txt_finished = txt_dict["txt_finished"]

stim = preload_stimuli(win, STIM_DIR, SUB_DIR, device, dB_SL=60)
# audio
audio_reg = stim["Audio"]
# visual
fix = stim["fix_dot"]
arrow_stim = stim["arrow_stim"]

# -------------------- LOAD TRIALS ------------------------
def load_trials():
    master_sequence_file = os.path.join(SUB_DIR, f"{SUB}_ASSR_master_trial_sequence.csv")
    if not os.path.exists(master_sequence_file):
        raise FileNotFoundError(f"ERROR: Master sequence file not found for {SUB}!")
    with open(master_sequence_file, "r", encoding="utf-8") as f:
        trials = list(csv.DictReader(f))
    print(f"Successfully loaded {len(trials)} trials.")
    return trials

trials = load_trials()

# ============================================================================================
# -------------------- INSTRUCTIONS --------------------
instr.draw()
win.flip()
device.updateRegisterCache()

flush_buttons(device, myLog)

while True:
    button, _ = collect_response(device, myLog, buttonCodes) # read VPixx buttonbox
    
    if button in ["red"]:
    #if event.getKeys(keyList=['r']): # for keyboard testing
        break
    if check_abort(): 
        core.quit()

# -------------------- COUNTDOWN --------------------
# for number in ["3", "2", "1"]:
#     countdown_text = visual.TextStim(win, text=number, height=3, color='black')
#     countdown_text.draw()
#     win.flip()
#     core.wait(1.0) # Show each number for 1 second
print(f"Starting CONDITION {CONDITION}...")

# -------------------- INITIAL FIXATION --------------------
# initial fixation + trigger
fix.draw()
draw_pixel(win, trigger_to_RGB(TRIG_START)) # Draw trigger pixel LAST

win.flip()  # display frame with trigger
# which comes first, the core wait or dev.update.reg.cache
device.updateRegisterCache()    # sync DATAPixx

core.wait(pixel_time) # to let trigger pixeel settle

# debug
print(f"TRIG START ON {TRIG_START} = {trigger_to_RGB(TRIG_START)}")
print_trigger_info(device)
print("")

# then only the fixation
fix.draw()
win.flip()
core.wait(1.0 - pixel_time)

# debug
print(f"TRIG START OFF")
print_trigger_info(device)
print("")

# -------------------- MAIN LOOP --------------------
for trial_data in trials:
    check_abort()
    flip_marks = {}

    # --------- Initialize variables and stimuli
    trial_onset_psy = psychopy_clock.getTime() # Records the planned start time

    arrow_type = trial_data["arrow"]
    arrow_onset_psy, arrow_onset_dev = None, None
    response_key, rt_psy, rt_dev = "NaN", "NaN", "NaN"

    # --------- Map condition
    if CONDITION == "ATT" and arrow_type == "right":
        response_key = False

    # --------- Visual stim selection and trigger mapping
    if arrow_type == "none":
        stim_to_draw = fix
        trigger_to_send = TRIG_SOUND_no_arr
    elif arrow_type == "left":
        arrow_stim.ori = 180  # Point left
        stim_to_draw = arrow_stim
        trigger_to_send = TRIG_L_ARR
    else:  # Right arrow
        arrow_stim.ori = 0  # Point right
        stim_to_draw = arrow_stim
        trigger_to_send = TRIG_R_ARR
    
    # --------- FRAME COUNTS ----------
    soa_frames = round(SOA / frameDur)
    arrow_frames = round(ARROW_DUR / frameDur) if arrow_type != "none" else 0

    # ========== SOUND + VISUAL + TRIGGER PRESENTATION
    frameN = 0
    response_collected = False

    while frameN < soa_frames:

        # ---- DRAW VISUAL ----
        if arrow_type != "none" and frameN >= arrow_frames:
            fix.draw()
        else:
            stim_to_draw.draw()

        # ---- TRIGGER (first 2 frames only) ----
        if frameN < TRIG_FRAMES:
            draw_pixel(win, trigger_to_RGB(trigger_to_send))

        # ---- ONSET TIMING ----
        if frameN == 0:
            if MRS == 0:
                win.callOnFlip(audio_reg.play)
            else:
                infoaud_fb = audio_reg
                device.audio.stopSchedule()
                device.audio.setAudioSchedule(0.0, infoaud_fb['fs'], infoaud_fb['n'], 'mono')
                device.audio.setReadAddress(infoaud_fb['addr'])
                device.audio.startSchedule()

            win.callOnFlip(lambda: flip_marks.update({
                "t_onset_dev": device.getTime(),
                "t_onset_psy": psychopy_clock.getTime()
            }))

            device.updateRegCacheAfterVideoSync()

        win.flip()

        # ---- STORE ONSETS ----
        if frameN == 0:
            sound_onset_dev = flip_marks.get("t_onset_dev")
            sound_onset_psy = flip_marks.get("t_onset_psy")

            if arrow_type != "none":
                arrow_onset_psy = sound_onset_psy
                arrow_onset_dev = sound_onset_dev

            flush_buttons(device, myLog)

        # ---- RESPONSE ----
        if CONDITION == "ATT" and not response_collected:
            response = collect_response(device, myLog, buttonCodes)

            if response is not None:
                button_pressed, t_dev = response

                if button_pressed == "red":
                    response_collected = True

                    # consistent RTs (same event base)
                    rt_dev = t_dev - sound_onset_dev
                    #rt_psy = t_dev - sound_onset_psy
                    rt_psy = psychopy_clock.getTime() - sound_onset_psy

                    if arrow_type == "right":
                        response_key = "red"

                        # response trigger (2 frames)
                        for _ in range(TRIG_FRAMES):
                            fix.draw()
                            draw_pixel(win, trigger_to_RGB(TRIG_RESPONSE))
                            win.flip()

                        # clear trigger
                        fix.draw()
                        win.flip()

                    elif arrow_type == "left":
                        response_key = False

        frameN += 1

    # ========== LOG ==========
    log_writer.writerow([
        trial_data["trial_index"], arrow_type,
        sound_onset_psy, sound_onset_dev,
        arrow_onset_psy, arrow_onset_dev,
        response_key, rt_psy, rt_dev
    ])
    log_f.flush()

# -------------------- FINISH --------------------
log_f.close()
txt_finished.draw()
win.flip()
core.wait(3)

cleanup()
device.din.stopDinLog()
device.updateRegisterCache()
device.close()
win.close()
core.quit()