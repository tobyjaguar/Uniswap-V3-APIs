def format_float(value):
    if value is None:
        return None

    float_value = float(value)

    if abs(float_value) >= 0.1:
        # For numbers >= 0.1 or <= -0.1, round to one decimal place
        return round(float_value, 1)
    elif float_value == 0:
        # If the value is exactly zero
        return 0.0
    else:
        # For very small numbers, use scientific notation
        # # with 4 significant digits
        return f"{float_value:.4e}"
