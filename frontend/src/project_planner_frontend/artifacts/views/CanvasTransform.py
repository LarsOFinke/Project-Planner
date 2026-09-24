from dataclasses import dataclass


@dataclass(slots=True)
class CanvasTransform:
    """Map stable logical canvas coordinates to screen pixels."""

    x: float = 0.0
    y: float = 0.0
    density: float = 1.0
    zoom: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0

    @property
    def unit(self) -> float:
        return self.density * self.zoom

    def to_screen(self, x: float, y: float) -> tuple[float, float]:
        return self.x + self.pan_x + x * self.unit, self.y + self.pan_y + y * self.unit

    def to_world(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.x - self.pan_x) / self.unit, (y - self.y - self.pan_y) / self.unit
