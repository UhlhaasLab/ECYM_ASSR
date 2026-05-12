from psychopy import  core
from pypixxlib import _libdpx as dp
import numpy as np

MRS = 0

if MRS == 0:
    # Working codes in Lab maestro Simulator
    BUTTON_CODES_ALL = {65527:'blue', 65533:'yellow', 65534:'red', 65531:'green', 65519:'white', 65535:'button release'}
    exitButton  = 'white'

if MRS == 1:
    # Button codes in MSR
    BUTTON_CODES_ALL = { 65528: 'blue', 65522: 'yellow', 65521: 'red', 65524: 'green', 65520: 'button release' }


def stopButtons(startAndStopButtons):
    while True:
        dp.DPxUpdateRegCache()
        state = dp.DPxGetDinValue()
        # print(f"Current button state: {state}")
        
        if state  in startAndStopButtons:
            return state

def read_button_press(device, button_log):
    """
    Read button presses from VPixx device.
    Returns:
        tuple: (button_name, timestamp) or (None, None) if no button pressed
    """
    if device is None:
        return None, None
    
    try:
        device.updateRegisterCache()
        device.din.getDinLogStatus(button_log)
        new_events = button_log["newLogFrames"]
        
        if new_events > 0:
            event_list = device.din.readDinLog(button_log, new_events)
            for timestamp, code in event_list:
                if code in BUTTON_CODES_ALL:
                    button_name = BUTTON_CODES_ALL[code] 
                    # # Only return green or red button presses
                    if button_name in ("red", "green","blue"):
                        return button_name, timestamp
    except Exception as e:
        print(f"✗ Error reading button: {e}")
    
    return None, None

def read_button_press_fast(device, button_log, valid_buttons):
    device.din.getDinLogStatus(button_log)
    n = button_log["newLogFrames"]
    
    if not n:
        return None, None

    events = device.din.readDinLog(button_log, n)

    for ts, code in events:
        name = valid_buttons.get(code)
        if name:
            return name, ts

    return None, None


def flush_button_buffer(device, button_log):
    """Clear all pending button events from the buffer."""

    while True:
        # dp.DPxUpdateRegCache()
        # device.updateRegisterCache()
        device.din.getDinLogStatus(button_log)
        n = button_log.get("newLogFrames", 0)
        
        if not n:
            break
        device.din.readDinLog(button_log, n)
            
def cleanup_and_exit(device, win):
    """Proper cleanup before exiting."""
    try:
        if device:
            device.close()
        if win:
            win.close()
        core.quit()
    except Exception as e:
        print(f"✗ Error during cleanup: {e}")
        core.quit()

def enable_din_dout_passthrough_pixel_mode():
    # This function enables a 1-1 DIN to DOUT passthrough on the DATAPixx3 
    # This script only needs to be run once; it will persist on the device until a
    # disable command is passed.

    # Open Datapixx and clear any forwarding behaviours
    dp.DPxOpen()
    dp.DPxDisableDoutButtonSchedules()
    dp.DPxUpdateRegCache()

    trigger_length = 16  # ms
    # samples_per_second = 1000  # Hz
    dout_buffer_base_addr = 0  # Initial address for button waveforms
    dout_button_schedules_mode = 0  # Triggers start on a rising edge; 1 for MRI

    # Define bits for each button (0-9)
    bits = np.arange(4)

    # Simple loop to write waveforms into hardware.
    # Buffer address for each DIN channel for a rising edge behaviour is baseAddress + 4069*DIN
    for bit in bits:
        waveform = list(np.full(trigger_length, 2 ** bit, dtype=np.uint32))
        buffer_address = dout_buffer_base_addr + 4096 * bit
        dp.DPxWriteRam(buffer_address, waveform)

    

    dp.DPxSetDoutBuff(dout_buffer_base_addr + 4096 * 0, trigger_length * 2)
    dp.DPxSetDoutSched(0, 1, 'video', trigger_length + 1)

    dp.DPxUpdateRegCache()

    dp.DPxEnableDinDebounce()
    dp.DPxEnableDoutButtonSchedules()
    dp.DPxSetDoutButtonSchedulesMode(dout_button_schedules_mode)
    dp.DPxWriteRegCache()
 