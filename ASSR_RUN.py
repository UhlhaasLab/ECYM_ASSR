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

    # --------- Initialize variables and stimuli
    flip_marks = {}
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
    

    # ========== SOUND + VISUAL + TRIGGER PRESENTATION
    stim_to_draw.draw() # Draw the visual stimulus (either fixation or arrow)
     
    if MRS == 0:
        # AUDIO PSYCHOPY
        win.callOnFlip(audio_reg.play)  # audio exactly on flip -> THIS WORKS IN PSYCHOPY
        
    if MRS == 1:
        # AUDIO VPIXX  -----------> ADAPT? make wihtout "if"?
        # prepare audio, not execute yet
        infoaud_fb = audio_reg # here we only have 1 clicktrain. thus audio_reg = clicktrain
        device.audio.stopSchedule()
        device.audio.setAudioSchedule(0.0, infoaud_fb['fs'], infoaud_fb['n'], 'mono')
        device.audio.setReadAddress(infoaud_fb['addr'])
        device.audio.startSchedule()
        
    draw_pixel(win, trigger_to_RGB(trigger_to_send)) # Draw trigger pixel (latched at flip)

    # timestamps at flip
    win.callOnFlip(lambda: flip_marks.setdefault("t_onset_dev", device.getTime()))
    win.callOnFlip(lambda: flip_marks.setdefault("t_onset_psy", psychopy_clock.getTime()))

    # execute all device commands at VSync
    device.updateRegCacheAfterVideoSync() # if doesnt work use: device.updateRegisterCache()
    win.flip()  # FLIP = visual + trigger + audio start aligned

    # store sound onset times
    sound_onset_dev = flip_marks["t_onset_dev"]
    sound_onset_psy = flip_marks["t_onset_psy"]
    # arrow onset: if shown, its onset is the same as the sound's
    if arrow_type != "none":
        arrow_onset_psy = sound_onset_psy
        arrow_onset_dev = sound_onset_dev

    core.wait(pixel_time) # Let trigger pixel settle for 2 frames

    # debug
    print(f"TRIG ON {trigger_to_send} = {trigger_to_RGB(trigger_to_send)}")
    print_trigger_info(device)
    print("")
    
    # ========== clear trigger. present visual for remaining time (sound continues and trigger turned off)
    stim_to_draw.draw() # only visual, no trigger
    win.flip() # This flip is less critical, so no cache update needed unless i need its timestamp.

    # wait remaining arrow duration (if there is an arrow)
    if arrow_type != "none":
        core.wait(ARROW_DUR - pixel_time) # wait 200ms minus the time we already waited with the trigger pixel on
        fix.draw() # After the duration, replace arrow with fixation dot
        win.flip()

    # ========== RESPONSE WINDOW + FIXATION
    fix.draw()
    flush_buttons(device, myLog)
    win.flip()

    # debug
    print(f"TRIG OFF")
    print_trigger_info(device)
    print("")

    response_collected = False # Use a simple flag to ensure we only log one press

    # Now, wait for the rest of the SOA while collecting responses
    while psychopy_clock.getTime() < trial_onset_psy + SOA:        
        
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
                    #     t_dev = psychopy_clock.getTime()
                    # ##### comment above out

                    # We only care about the "red" button, but now we check what it means
                    if button_pressed == "red":
                        
                        # A response was made, so stop looking for more.
                        response_collected = True
                        
                        # Log the reaction times regardless of correctness
                        rt_dev = t_dev - sound_onset_dev
                        rt_psy = psychopy_clock.getTime() - sound_onset_psy
                        
                        # Now, evaluate the response based on the arrow type
                        if arrow_type == "right":
                            # This is a correct response (a "hit")
                            response_key = "red"

                            # send response trigger
                            fix.draw()
                            draw_pixel(win, trigger_to_RGB(TRIG_RESPONSE))
                            
                            # device.updateRegCacheAfterVideoSync()
                            win.flip() 
                            core.wait(pixel_time) # to let trigger pixeel settle (ADAPT IN MRS)
                            
                            # clear response trigger
                            fix.draw()
                            # win.callOnFlip(device.updateRegCacheAfterVideoSync)
                            win.flip()

                        elif arrow_type == "left":
                            # This is an incorrect response (a "false alarm")
                            response_key = False
                            # We do NOT send a trigger for an incorrect response.

    # ========== 4. LOG DATA for the completed trial
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
