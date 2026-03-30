"""
to do
- check if trial seq is correct
"""


import random, csv, time, os
from psychopy import visual, core, event, sound

from ASSR_init import (SUB, CONDITION, SUB_DIR, STIM_DIR, SOA, ARROW_DUR,
                        # triggers
                        TRIG_START,
                        TRIG_SOUND_no_arr, TRIG_L_ARR, TRIG_R_ARR, 
                        TRIG_RESPONSE, 
                        # vpixx
                        device, buttonCodes, myLog, stim_monitor,
                        # preload
                        preload_stimuli, preload_txt)

from utils.pixel_mode           import trigger_to_RGB, draw_pixel, print_trigger_info
from utils.buttons              import collect_response, flush_buttons
from utils.escape_cleanup_abort import check_abort, cleanup

# -------------------- GENERAL --------------------
timestamp = time.strftime('%Y%m%d_%H%M%S')
global_clock = core.Clock()

# -------------------- WINDOW --------------------------------
monitor_settings = stim_monitor()

# set fullscr to True in MSR
win = visual.Window(
    monitor=monitor_settings['monitor_name'], size=monitor_settings['monitor_size_pix'], 
    fullscr=True, 
    units="deg", 
    color=[211, 211, 211],
    colorSpace='rgb255', 
    #colorSpace='rgb',
    #colorSpace='rgb1',
    screen=monitor_settings["screen_number"]
)
win.mouseVisible = False
mouse = event.Mouse(visible=False) 

# -------------------- LOGGING SETUP --------------------
log_file = os.path.join(SUB_DIR, f"{SUB}_{CONDITION}_log_{timestamp}.csv")
log_f = open(log_file, "w", newline="", encoding="utf-8")
log_writer = csv.writer(log_f)
log_writer.writerow(["trial_index","arrow","sound_onset_psy","sound_onset_dev",
                     "arrow_onset_psy","arrow_onset_dev","response_key","rt_psy","rt_dev"])

# -------------------- PRELOAD STIMULI & TEXT --------------------
txt_dict = preload_txt(win)
instr = txt_dict["txt_intro_PAS"] if CONDITION == "PAS" else txt_dict["txt_intro_ATT"]
txt_finished = txt_dict["txt_finished"]

stim = preload_stimuli(win, STIM_DIR, SUB_DIR, device, dB_SL=60)
audio_reg = stim["Audio"]
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
# # instructions
# instr.draw()
# win.flip()

# flush_buttons(device, myLog)

# while True:
#     button, _ = collect_response(device, myLog, buttonCodes) # read VPixx buttonbox
    
#     if button in ["red"]: #, "green"]:
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

# -------------------- INITIAL FIXATION --------------------
# # 1. Show initial fixation + trigger and hold it
# fix.draw()
# draw_pixel(win, trigger_to_RGB(TRIG_START)) # Draw trigger pixel LAST

# win.flip()  # display frame with trigger
# core.wait(0.02) # to let trigger pixeel settle
# device.updateRegisterCache()    # sync DATAPixx
# print_trigger_info(device, TRIG_START) 

# # 2. Hold this state for the specified duration
# core.wait(1.0)

# -------------------- MAIN LOOP --------------------
for trial_data in trials:
    check_abort()

    # --- 1. Initialize variables and stimuli ---
    flip_marks = {}    
    rt_psy, rt_dev = "NaN", "NaN"
    arrow_onset_psy, arrow_onset_dev = None, None
    arrow_type = trial_data["arrow"]
    trial_onset_psy = global_clock.getTime() # Record the planned start time for precise SOA control

    response_key = "NaN"
    if CONDITION == "ATT" and arrow_type in ["right"]:
        response_key = False

    # --- 2. Map trial type to trigger ---
    if arrow_type == "none":
        stimulus_to_draw = fix
        trigger_to_send = TRIG_SOUND_no_arr
    elif arrow_type == "left":
        arrow_stim.ori = 180  # Point left
        stimulus_to_draw = arrow_stim
        trigger_to_send = TRIG_L_ARR
    else:  # Right arrow
        arrow_stim.ori = 0  # Point right
        stimulus_to_draw = arrow_stim
        trigger_to_send = TRIG_R_ARR
    

    # --- 3. PRESENTATION Sound + Visual + Trigger ---
    stimulus_to_draw.draw() # Draw the visual stimulus (either fixation or arrow)
    draw_pixel(win, trigger_to_RGB(trigger_to_send)) # Draw trigger pixel
 
    win.callOnFlip(lambda: flip_marks.setdefault("t_onset_dev", device.getTime()))
    win.callOnFlip(lambda: flip_marks.setdefault("t_onset_psy", global_clock.getTime()))
    win.callOnFlip(audio_reg.play)  # audio exactly on flip -> THIS WORKS IN PSYCHOPY


    

    # infoaud_fb = stimuli['Audio']['Aud_FB']
    # infoaud_fb = audio_reg
    # device.audio.stopSchedule()
    # device.audio.setAudioSchedule(0.0, infoaud_fb['fs'], infoaud_fb['n'], 'mono')
    # device.audio.setReadAddress(infoaud_fb['addr'])
    # device.audio.startSchedule()
    # device.updateRegisterCache()

    win.flip() # this single flip executes stimulus, trigger and time logging simultaneously
    core.wait(0.02) # to let trigger pixeel settle (ADAPT IN MRS)
    device.updateRegisterCache()
    print_trigger_info(device, trigger_to_send) # comment out after debugging

    # Store the precise onset times
    sound_onset_psy = flip_marks.get("t_onset_psy")
    sound_onset_dev = flip_marks.get("t_onset_dev")
    # If an arrow was shown, its onset is the same as the sound's
    if arrow_type != "none":
        arrow_onset_psy = sound_onset_psy
        arrow_onset_dev = sound_onset_dev
    

    # --- 4. POST-STIMULUS and RESPONSE WINDOW ---
    # First, clear the trigger pixel immediately on the next frame
    fix.draw()
    win.flip()
    device.updateRegisterCache()
    
    # If an arrow was shown, wait for its duration to pass
    if arrow_type != "none":
        core.wait(ARROW_DUR) # wait 200ms
        fix.draw() # After the duration, replace arrow with fixation dot
        win.flip()
    
    response_collected = False # Use a simple flag to ensure we only log one press
    flush_buttons(device, myLog)

    # Now, wait for the rest of the SOA while collecting responses
    while global_clock.getTime() < trial_onset_psy + SOA:        
        # Only check for responses in the ATTEND condition and if one hasn't been logged yet
        if CONDITION == "ATT" and not response_collected:
                response = collect_response(device, myLog, buttonCodes)
                
                if response is not None:
                    button_pressed, t_dev = response #for vpixx
                    # ##### if not vpixx, use keyboard for testing: r=red, g=green. so 'r' = right button and 'g' = left button for Group A, and reversed for Group B
                    # button_pressed = None
                    # keys = event.getKeys(keyList=['r'])
                    # if keys:
                    #     button_pressed = 'red'
                    #     t_dev = global_clock.getTime()
                    # ##### comment above out

                    # We only care about the "red" button, but now we check what it means
                    if button_pressed == "red":
                        
                        # A response was made, so stop looking for more.
                        response_collected = True
                        
                        # Log the reaction times regardless of correctness
                        rt_dev = t_dev - sound_onset_dev
                        rt_psy = global_clock.getTime() - sound_onset_psy
                        
                        # Now, evaluate the response based on the arrow type
                        if arrow_type == "right":
                            # This is a correct response (a "hit")
                            response_key = "red"
                            # Send the specific response trigger
                            fix.draw()
                            draw_pixel(win, trigger_to_RGB(TRIG_RESPONSE))
                            win.flip()
                            core.wait(0.02) # to let trigger pixeel settle (ADAPT IN MRS)
                            device.updateRegisterCache()
                            print_trigger_info(device, TRIG_RESPONSE) 

                            # Go back to the "off" state immediately
                            fix.draw()
                            win.flip()
                            core.wait(0.02) # to let trigger pixel settle (ADAPT IN MRS)
                            device.updateRegisterCache()

                        elif arrow_type == "left":
                            # This is an incorrect response (a "false alarm")
                            response_key = False
                            # We do NOT send a trigger for an incorrect response.
            
        core.wait(0.001) # wait a tiny bit to prevent CPU overload

    # --- 5. LOG DATA for the completed trial ---
    log_writer.writerow([
        trial_data["trial_index"], trial_data["arrow"],
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
