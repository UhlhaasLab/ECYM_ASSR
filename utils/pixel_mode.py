""" use following 2 like this: draw_pixel(trigger_to_RGB(TRIG_NUMBER))
1. TRIG nr to GB
2. draw pixel
3. debug
"""

from psychopy import visual

# ===================================== 1. CONVERT TRIGGER NUMBER TO RGB =====================================
def trigger_to_RGB(trigger: int):
    if not (0 <= trigger <= 65535):
        raise ValueError("Trigger must be between 0 and 65535.")

    G = trigger & 0xFF          # lower 8 bits
    B = (trigger >> 8) & 0xFF   # upper 8 bits

    return [0, G, B]

# worked as well:
# def trigger_to_RGB(trigger_number: int):
#     """
#     determines pixel mode GB 255 colour value based on 24-bit trigger (in decimal, base 10)  
#     return [green, blue]
#     red = R = always 0 (as the first 8 bits are for buttonbox)
#     """
#     return [ 0, (trigger_number)%256, (trigger_number>>8)%256]


# ===================================== 2. DRAW PIXEL =====================================
# line = exactly 1 pixel
# def draw_pixel(win, pixelValue): 
#     # draws pixel in topleft corner of window: window must cover top left of screen to work, interpolate must be set to FALSE before color is set, call this just before flip to ensure pixel is drawn over other stimuli
#     topLeftCorner = [-win.size[0]/2, win.size[1]/2]
#     line = visual.Line(
#         win=win,
#         units='pix',
#         start=topLeftCorner,
#         end=[topLeftCorner[0]+1, topLeftCorner[1]],
#         interpolate=False,
#         lineColor=pixelValue,
#         colorSpace='rgb255',
#         fillColor=None
#     )
#     line.draw()

# rectange = for debugging: visible size PLUS for back to trigger calculation debug
def draw_pixel(win, pixelValue): 
    # draws pixel in topleft corner of window: window must cover top left of screen to work, interpolate must be set to FALSE before color is set, call this just before flip to ensure pixel is drawn over other stimuli
    pixel_square_size = 500 # 500. For debugging, set a visible size. For the experiment, this can be 1.
    # The 'pos' of a Rect is its center. We calculate the center position. that places the square's top-left corner at the window's top-left corner.
    x_pos = -win.size[0]/2 + pixel_square_size/2
    y_pos =  win.size[1]/2 - pixel_square_size/2
    # Use visual.Rect for a filled square.
    pixel_square = visual.Rect(
        win=win,
        units='pix',
        width=pixel_square_size,
        height=pixel_square_size,
        pos=[x_pos, y_pos],
        interpolate=False,
        lineColor=pixelValue, # Set both line and fill for a solid color
        fillColor=pixelValue,
        colorSpace='rgb255'
        #colorSpace='rgb', # also changed in win
    )
    pixel_square.draw()
  

  

# ===================================== 3. DEBUGGING =====================================
# erfans debug:
def GB_to_trigger(color):
    """
    Converts RGB color values back to the trigger number.
    Inverse of trigger_to_RGB(): reconstructs the original trigger from [R, G, B].
    (on my laptop it will not be R=0, as it is not a vpixx screen)
    Args: color: [R, G, B] list where R=0, G=(trigger%256), B=(trigger>>8)%256
    Returns: int: The reconstructed trigger number from lower 8 bits (G) and upper 8 bits (B)
    """
    G = color[1]
    B = color[2]
    return (B << 8) + G

def print_trigger_info(device):
    line = device.getVideoLine()
    linevalue = GB_to_trigger([line[0][0], line[1][0], line[2][0]])
    print(f"Video line value: {linevalue}")  # Debugging output to check the video line value
    # linevalues are eg 55769, etc.. how do i convert it back to trigger number? i need to do the inverse of trigger_to_RGB, which is GB_to_trigger. i can then compare the reconstructed trigger number to the expected trigger number for debugging. this will help me confirm that the correct trigger is being sent and read by the device.:
    # for this i therefore need to print:
    print(f"Reconstructed trigger number from video line: {GB_to_trigger([line[0][0], line[1][0], line[2][0]])}")  # This should match the expected trigger number if everything is correct.


# # if above doesnt work try this:
# def print_trigger_info(device):
#     line = device.getVideoLine()

#     # top-left pixel (your trigger pixel)
#     R = int(line[0][0])
#     G = int(line[1][0])
#     B = int(line[2][0])

#     trig = (B << 8) + G
#     print(f"Trigger:{trig}.  Videoline: R={R}, G={G}, B={B}.")  # Debugging output to check the video line value and reconstructed trigger number



# # worked as well i think?
# def print_trigger_info(device, expected_trigger):
#     """
#     Prints the video line RGB values and the reconstructed trigger number.
#     Useful for debugging pixel mode trigger encoding.
#     """
#     line = device.getVideoLine()
#     rgb_values = [line[0][0], line[1][0], line[2][0]]
#     read_trigger = GB2trigger(rgb_values)

#     match = (read_trigger == expected_trigger)
    
#     print("=== Trigger Debug Info ===")
#     print(f"Video line RGB: {rgb_values}")  # Raw RGB values from video line
#     print(f"Expected RGB for trigger {expected_trigger}: {trigger_to_RGB(expected_trigger)}")  # What RGB should be for the expected trigger
#     print(f"Reconstructed trigger number: {read_trigger}")  # Trigger decoded from RGB
#     print(f"Match: {match}")  
