"""
TINEKE:
- for now it sends triggers when correct response. can take out right?
- should i reset the psychopy clock at beginning?

DARIO:
- updateReg cache use after trigger pres???

end:
- check if trial seq is correct
"""

import random, csv, time, os
from psychopy import visual, core, event, sound

from ASSR_init import (SUB, CONDITION, MRS, SUB_DIR, STIM_DIR, SOA, ARROW_DUR,
                        # triggers
                        TRIG_START, TRIG_END,
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

# number of frames = duration in sec * refresh rate in Hz (frames per second)
monitor_rr = monitor_settings["refresh_rate"] # 120 in MSR.     60 on laptop
frameDur = 1.0 / monitor_rr     # 0.008333s, 8.33ms in MSR.     0.016666s, 16.67ms on laptop.       1 frame last 8.33ms, then next..
TRIG_FRAMES = 2 # pixel should show for 2 frames, = 16.66ms in MSR, 33.32ms on laptop
soa_frames = round(SOA / frameDur) # in MSR: round(1.5s / 0.008333) = 180 frames for one SOA.

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
# instr.draw()
# win.flip()
# device.updateRegisterCache()

# flush_buttons(device, myLog)
# while True:
#     button, _ = collect_response(device, myLog, buttonCodes) # read VPixx buttonbox
#     if button in ["red"]:
#     #if event.getKeys(keyList=['r']): # for keyboard testing
#         break
#     if check_abort(): 
#         core.quit()

# -------------------- COUNTDOWN --------------------
# for number in ["3", "2", "1"]:
#     countdown_text = visual.TextStim(win, text=number, height=3, color='black')
#     countdown_text.draw()
#     win.flip()
#     core.wait(1.0) # Show each number for 1 second
print(f"Starting ASSR CONDITION {CONDITION}...")

# -------------------- INITIAL FIXATION --------------------
for f in range(TRIG_FRAMES):
    fix.draw()
    draw_pixel(win, trigger_to_RGB(TRIG_START))
    win.flip()

# debug
print(f"TRIG START ON {TRIG_START}, RGB: {trigger_to_RGB(TRIG_START)}")
print_trigger_info(device)
print("")

for f in range(round(1.0 / frameDur) - TRIG_FRAMES):
    fix.draw()
    win.flip()

# debug
print(f"gray")
print_trigger_info(device)
print("")

# -------------------- MAIN LOOP --------------------
"""
# ADAPT -------------> should i reset the psychopy clock? 
win.callOnFlip(psychopy_clock.reset) # set clock=0
win.flip()
"""

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
    arrow_frames = round(ARROW_DUR / frameDur) if arrow_type != "none" else 0


    # ============= SOUND + VISUAL + TRIGGER PRESENTATION
    """ each trial starts with frame number 0, and we present the sound and visual stimulus for a total of SOA (e.g., 1.5s), which corresponds to a certain number of frames (e.g., 180 frames at 120Hz). The trigger is presented only for the first few frames (e.g., 2 frames = 16.66ms in MSR) to ensure it is registered by the DataPixx, while the visual stimulus can be presented for the entire SOA duration. the arrows are presented for a certain duration (e.g., 500ms), which corresponds to a certain number of frames (e.g., 60 frames at 120Hz). So the sequence within each trial is:
            - Frame 0: Present sound, visual stimulus (fixation or arrow), and trigger (for 2 frames)
            - Frames 1 to 59: Continue presenting sound and visual stimulus, but no trigger (to ensure trigger is only for the first 2 frames) """
    frameN = 0
    response_collected = False

    while frameN < soa_frames:

        # ---- DRAW VISUAL ----
        if arrow_type != "none" and frameN >= arrow_frames:
            fix.draw()
        else:
            stim_to_draw.draw()

        # ---- TRIGGER (first 2 frames only) ----
        if frameN < TRIG_FRAMES: # use < for presenting the trig for frame 0 and 1 (two frames), and use <= for presenting the trig for frame 0, 1, and 2 (three frames)
            draw_pixel(win, trigger_to_RGB(trigger_to_send))
        
            # debug only once per trial, after pixel settling, to check trigger values:
            if frameN == TRIG_FRAMES - 1:
                print(f"trig_to_send: {trigger_to_send}, RGB: {trigger_to_RGB(trigger_to_send)}")
                print_trigger_info(device)
                print("")

        # debug gray 
        if frameN == TRIG_FRAMES + 1:
            print(f"gray")
            print_trigger_info(device)
            print("")

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
                button_pressed, t_dev_pressed = response

                if button_pressed == "red":
                    response_collected = True

                    # consistent RTs (same event base)
                    rt_dev = t_dev_pressed - sound_onset_dev
                    rt_psy = psychopy_clock.getTime() - sound_onset_psy

                    if arrow_type == "right":
                        response_key = "red"

                        # response trigger (2 frames)
                        for f in range(TRIG_FRAMES):
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

# wait one soa
for f in range(soa_frames):
    win.flip()

# RUN END trigger (2 frames)
for f in range(TRIG_FRAMES):
    draw_pixel(win, trigger_to_RGB(TRIG_END))
    win.flip()
win.flip() # clear trig
print(f"Condition {CONDITION} finished.")


txt_finished.draw()
win.flip()
core.wait(3)

cleanup()
device.din.stopDinLog()
device.updateRegisterCache()
device.close()
win.close()
core.quit()