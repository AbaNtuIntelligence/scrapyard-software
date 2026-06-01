import serial
import re
from config import Config

def get_current_weight():
    """
    Reads weight from the serial scale.
    Returns weight in kg as float, or None if error.
    """
    try:
        ser = serial.Serial(
            port=Config.SCALE_PORT,
            baudrate=Config.SCALE_BAUDRATE,
            timeout=Config.SCALE_TIMEOUT
        )
        # Read line (adjust encoding and parsing to match your scale's output)
        line = ser.readline().decode('ascii', errors='ignore').strip()
        ser.close()
        
        # Example: scale sends "      12.50 kg"
        # Extract number using regex
        match = re.search(r"(\d+\.?\d*)", line)
        if match:
            weight = float(match.group(1))
            return weight
        else:
            return None
    except Exception as e:
        print(f"Scale error: {e}")
        return None