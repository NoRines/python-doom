from pygame.math import Vector2

def line_intersection(p0 : Vector2, p1 : Vector2, p2 : Vector2, p3 : Vector2) -> Vector2:
    A1 = p1.y - p0.y
    B1 = p0.x - p1.x
    C1 = A1 * p0.x + B1 * p0.y
    A2 = p3.y - p2.y
    B2 = p2.x - p3.x
    C2 = A2 * p2.x + B2 * p2.y
    denominator = A1 * B2 - A2 * B1
    return Vector2(
        (B2 * C1 - B1 * C2) / denominator,
        (A1 * C2 - A2 * C1) / denominator
    )