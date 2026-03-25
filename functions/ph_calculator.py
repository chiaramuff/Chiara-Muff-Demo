from datetime import datetime
import math

from matplotlib import category
import pytz

def calculate_ph(h3o_concentration):
    """Berechnet den pH-Wert aus der Konzentration."""
    if h3o_concentration <= 0:
        return None  # Mathematisch nicht möglich
    output = -math.log10(h3o_concentration)
    return {
        "timestamp": datetime.now(pytz.timezone('Europe/Zurich')),  # Current swiss time
        "h3o_concentration": output,
    } 
