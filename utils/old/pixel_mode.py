""" use following 2 like this: draw_pixel(trigger_to_RGB(TRIG_NUMBER))
1. TRIG nr to GB
2. draw pixel
3. debug
"""

from psychopy import visual

# ===================================== 1. CONVERT TRIGGER NUMBER TO RGB =====================================
def trigger_to_RGB(trigger_number: int):
    """
    determines pixel mode GB 255 colour value based on 24-bit trigger (in decimal, base 10)  
    return [green, blue]
    red = R = always 0 (as the first 8 bits are for buttonbox)
    """
    return [ 0, (trigger_number)%256, (trigger_number>>8)%256]

# ===================================== 2. DRAW PIXEL =====================================
def draw_pixel(win, pixelValue):
    #takes a pixel colour and draws it as a single pixel in the top left corner of the window
    #window must cover top left of screen to work
    #interpolate must be set to FALSE before color is set
    #call this just before flip to ensure pixel is drawn over other stimuli
    # For debugging, set a visible size. For the experiment, this can be 1.
    pixel_square_size = 400 

    # The 'pos' of a Rect is its center. We calculate the center position
    # that places the square's top-left corner at the window's top-left corner.
    x_pos = -win.size[0] / 2 + pixel_square_size / 2
    y_pos =  win.size[1] / 2 - pixel_square_size / 2
    
    # Use visual.Rect for a filled square.
    pixel_square = visual.Rect(
        win=win,
        units='pix',
        width=pixel_square_size,
        height=pixel_square_size,
        pos=[x_pos, y_pos],
        colorSpace='rgb255',
        lineColor=pixelValue, # Set both line and fill for a solid color
        fillColor=pixelValue,
    )
    
    pixel_square.draw()

# ===================================== 3. DEBUGGING =====================================
def GB2trigger(color):
    """
    Converts RGB color values back to the trigger number.
    Inverse of trigger_to_RGB(): reconstructs the original trigger from [R, G, B].
    (on my laptop it will not be R=0, as it is not a vpixx screen)
    Args: color: [R, G, B] list where R=0, G=(trigger%256), B=(trigger>>8)%256
    Returns: int: The reconstructed trigger number from lower 8 bits (G) and upper 8 bits (B)
    """
    return int((color[2] << 8) + color[1])

def print_trigger_info(device):
    """
    Prints the video line RGB values and the reconstructed trigger number.
    Useful for debugging pixel mode trigger encoding.
    """
    line = device.getVideoLine()
    rgb_values = [line[0][0], line[1][0], line[2][0]]
    trigger_number = GB2trigger(rgb_values)
    
    print(f"Video line RGB: {rgb_values}")  # Raw RGB values from video line
    print(f"Reconstructed trigger number: {trigger_number}")  # Trigger decoded from RGB
    







# ==================================== OLD

# new, 225 or so numbers possible new:
# def trigger_to_RGB(trigger_number: int):
#     """
#     Converts a trigger number (0-255) into a VPixx-compatible RGB value.
#     The trigger number is placed directly into the green channel.
#     """
#     if not 0 <= trigger_number <= 255:
#         print(f"WARNING: Trigger number {trigger_number} is outside the valid range of 0-255.") # then comment this print out
#         trigger_number = max(0, min(trigger_number, 255)) 
        
#     return [0, trigger_number, 0]

#def trigger_to_RGB(out_num: int):
#    """
#    Converts a trigger number into an 8-bit RGB value suitable for VPixx Pixel Mode.
#    IN: 8 (trigger), OUT: [0, g, b] = (RGB_color)
#    IN: Trigger number (e.g., 8), 
#    OUT: [R, G, B] list (e.g., [0, 1, 0]).
#    e.g.: trigger_to_RGB(8) = [0, 1, 0]
#    The values G and B will be powers of 2 (1, 2, 4, 8, 16, 32, 64, 128).
#    """
#    # This maps trigger numbers to the specific green/blue channel bits
#    if out_num < 8:
#        out_num = 8 + (out_num % 16)
#    elif out_num > 23:
#        out_num = 8 + (out_num % 16)
#    
#    bit = out_num - 8
#    if bit < 8:
#        # bits 8–15 → green channel
#        G = 1 << bit
#        B = 0
#    else:
#        # bits 16–23 → blue channel
#        G = 0
#        B = 1 << (bit - 8)
#    return [0, G, B]





# new, draws rectangle instead of line:
# def draw_pixel(current_window, RGB_color):
#     """
#     Draws a square in the top-left corner of the window for VPixx Pixel Mode.
#     Includes a DEBUG_MODE to make the pixel visible to the human eye.
#     """
#     # --- For debugging, uncomment the next line to see a bright green square ---
#     RGB_color = [0, 255, 0] 
#     # ------------------------------------------------------------------------

#     # For a visible square during testing, set a size in pixels.
#     # For the actual experiment, this can be as small as 1x1.
#     pixel_square_size = 100 # Let's use a 50x50 pixel square for visibility # ADAPT here to make bigger for visualization

#     # The 'pos' of a Rect is its center. We calculate the center position
#     # that places the square snugly in the top-left corner.
#     x_pos = -current_window.size[0] / 2 + pixel_square_size / 2
#     y_pos =  current_window.size[1] / 2 - pixel_square_size / 2
    
#     # Use visual.Rect for a filled square, which is more reliable.
#     pixel_square = visual.Rect(
#         win=current_window,
#         units='pix',
#         width=pixel_square_size,
#         height=pixel_square_size,
#         pos=[x_pos, y_pos],
#         colorSpace='rgb255',
#         lineColor=RGB_color,
#         fillColor=RGB_color,
#     )
    
#     pixel_square.draw()



#     """
#     Draws a square in the top-left corner of the window for VPixx Pixel Mode.
    
#     This function now uses visual.Rect for a proper filled square and handles
#     coordinates correctly. It also includes a "debug" mode to make the pixel
#     visible to the human eye for testing.
#     """

#     # use 1 = 1x1 size pixel. but for testing/visibility use bigger e.g. 100
#     pixel_square_size = 100

#     # The 'pos' of a Rect is its center. We calculate the center position
#     # that places the square snugly in the top-left corner.
#     x_pos = -current_window.size[0] / 2 + pixel_square_size / 2
#     y_pos =  current_window.size[1] / 2 - pixel_square_size / 2
    
#     # Use visual.Rect for a filled square, which is more reliable.
#     pixel_square = visual.Rect(
#         win=current_window,
#         units='pix',
#         width=pixel_square_size,
#         height=pixel_square_size,
#         pos=[x_pos, y_pos],
#         colorSpace='rgb255',
#         lineColor=RGB_color,
#         fillColor=RGB_color,
#     )
    
#     pixel_square.draw()


# form dario:
#def draw_pixel(current_window, RGB_color):
#    # Top-left pixel (in pix units)
#    x0 = -current_window.size[0] / 2
#    y0 =  current_window.size[1] / 2
#    # Draw a 1-pixel horizontal line (length=1 px)
#    line_ = visual.Line(
#        win=current_window,
#        units='pix',
#        start=[x0, y0],
#        #end=[x0 + 1, y0],
#        end=[x0 + 1000, y0 + 1000],  # 3cm big so i can see it on the screen. (delete later)
#        interpolate=False,
#        colorSpace='rgb255',
#        lineColor=RGB_color,
#        fillColor=RGB_color,  # 3cm big so i can see it on the screen. (delete later)
#        #fillColor=None
#    )
#    line_.draw()
#    return x0, y0  # return coords so we can reuse them for e.g rectangle but else not used

