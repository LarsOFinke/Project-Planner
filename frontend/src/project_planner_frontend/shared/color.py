def hex_color(value: str) -> tuple[float, float, float, float]:
    cleaned = value.lstrip("#")
    return tuple(int(cleaned[index : index + 2], 16) / 255 for index in (0, 2, 4)) + (1,)
