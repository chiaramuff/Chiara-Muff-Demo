import math

def calculate_ph(h3o_concentration):
    """Berechnet den pH-Wert aus der Konzentration."""
    if h3o_concentration <= 0:
        return None  # Mathematisch nicht möglich
    return -math.log10(h3o_concentration)

def calculate_concentration(ph_value):
    """Berechnet die Konzentration aus dem pH-Wert."""
    return 10**(-ph_value)