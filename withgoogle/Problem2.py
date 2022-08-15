from __future__ import division

import math
import fractions

def solution(dimensions, your_position, trainer_position, distance):
    infinity = float('inf')
    width, height = dimensions
    you_x, you_y = your_position
    trainer_x, trainer_y = trainer_position
    d2 = distance * distance

    max_width = int(math.ceil(distance * 1.0 / width))
    max_height = int(math.ceil(distance * 1.0 / height))

    def get_position_dictionary(x, y):
        result = {}
        for x_box in range(-max_width - 3, max_width + 4):
            for y_box in range(-max_height - 3, max_height + 4):
                result_x = x_box * width + x if (x_box & 1 == 0) else (x_box + 1) * width - x
                result_y = y_box * height + y if (y_box & 1 == 0) else (y_box + 1) * height - y
                dx = result_x - you_x
                dy = result_y - you_y
                distance = dx * dx + dy * dy
                if distance > d2:
                    continue
                if dx == 0:
                    if dy == 0:
                        continue
                    direction = (0, dy // abs(dy))
                elif dy == 0:
                    direction = (dx // abs(dx), 0)
                else:
                    gcd = abs(fractions.gcd(dx, dy))
                    direction = (dx // gcd, dy // gcd)
                result[direction] = min(result.get(direction, infinity), distance)
        return result

    trainer_positions = get_position_dictionary(trainer_x, trainer_y)
    bunny_positions = get_position_dictionary(you_x, you_y)

    result = [direction for direction, distance in trainer_positions.items()
              if distance < bunny_positions.get(direction, infinity)]
    return len(result)



if __name__ == '__main__':
    print(solution([3, 2], [1, 1], [2, 1], 4))
    print(solution([300, 275], [150, 150], [185, 100], 500))
