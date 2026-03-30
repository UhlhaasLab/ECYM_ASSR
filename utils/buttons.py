""" collect responses using vpixx buttonpress """


def collect_response(device, buttonLog, buttonCodes):
    # Collect responses. Ignore if not red/green
    device.updateRegisterCache()
    device.din.getDinLogStatus(buttonLog)
    newEvents = buttonLog["newLogFrames"]
    # Check events
    if newEvents > 0:
        eventList = device.din.readDinLog(buttonLog, newEvents) # here i get the responses
        for t_event, code in eventList:
            # Check if code is known and corresponds to red/green only
            if code in buttonCodes:
                buttonID = buttonCodes[code]
                if buttonID not in ("red", "green"):
                    # Ignore any button that's not red or green
                    continue
                print(f"Button pressed: {buttonID.upper()}")
                return buttonID, t_event
    return None, None

def flush_buttons(device, buttonLog):
    # clears responses
    while True:
        device.updateRegisterCache()
        device.din.getDinLogStatus(buttonLog)
        n = buttonLog.get("newLogFrames", 0)
        if not n:
            break
        device.din.readDinLog(buttonLog, n)
    print("buttonpress flushed")