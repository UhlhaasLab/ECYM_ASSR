from psychopy import event, core

def escape_check(vpdevice=None, currentwindow=None):
    if event.getKeys(['escape', 'esc', 'entf']):
        print("Experiment terminated by user (ESC).")
        # --- Handle VPixx device if present ---
        if vpdevice is not None:
            # Stop DIN logging if running
            try:
                if hasattr(vpdevice, "din"):
                    vpdevice.din.stopDinLog()
            except Exception:
                pass  # ignore errors if not started / not available
                
            # Make sure registers are updated and device closed
            try:
                vpdevice.updateRegisterCache()
            except Exception:
                pass
            try:
                vpdevice.close()
            except Exception:
                pass
                
        # --- Close PsychoPy window and quit ---
        try:
            if currentwindow is not None:
                currentwindow.close()
        except Exception:
            pass
        core.quit()

def cleanup():
    try:
        log_f.close() # event_f is 
        core.quit()
        device.dout.disablePixelModeGB()
        # disable button box?
        device.close()
    except Exception:
        core.quit()

def check_abort():
    if event.getKeys(keyList=["escape", "esc", "entf"]):
        cleanup()



# for buttons
def check_din_state(device):
    device.updateRegisterCache()
    current_din_state = device.din.getValue() # this gets the current digital input (DIN) register state = value of the bits.
    print(f"current_din_state: {current_din_state}")

# for pixel mode
def check_dout_state(device):
    device.updateRegisterCache()
    current_dout_state = device.getVideoLine()
    print(f"current_dout_state: {current_dout_state}")