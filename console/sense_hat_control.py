from sense_hat import SenseHat
from pixels import status_pixels
sense = SenseHat()

def show_status(status, matrix, color):
     #display the first digit
    for x, y in status_pixels[status]:
        index = y * 8 + x
        matrix[index] = color
    sense.set_pixels(matrix)

def clear_display():
    """Clear the Sense AT display."""
    sense.clear()