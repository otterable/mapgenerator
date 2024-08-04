import matplotlib.pyplot as plt
import numpy as np
import random

def generate_city_map():
    width = 20
    height = 20
    street_width = 1

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 10))

    # Track road positions for scooter placement
    road_positions = []

    # Generate streets
    for x in range(0, width, 2):
        for y in range(0, height, 2):
            if random.choice([True, False]):
                # Horizontal street
                length = random.randint(1, 2) * 2
                for i in range(length + 1):
                    road_positions.append((x + i, y))
                ax.plot([x, x + length], [y, y], color="black", linewidth=street_width)
            if random.choice([True, False]):
                # Vertical street
                length = random.randint(1, 2) * 2
                for i in range(length + 1):
                    road_positions.append((x, y + i))
                ax.plot([x, x], [y, y + length], color="black", linewidth=street_width)

    # Place warehouse
    warehouse_x, warehouse_y = random.choice(road_positions)
    ax.scatter(warehouse_x, warehouse_y, color="red", s=100, label="Warehouse")

    # Remove warehouse location from possible scooter positions
    road_positions.remove((warehouse_x, warehouse_y))

    # Place scooters
    num_scooters = random.randint(10, 20)
    scooter_positions = random.sample(road_positions, num_scooters)
    for x, y in scooter_positions:
        ax.scatter(x, y, color="blue", s=50, label="Scooter" if (x, y) == scooter_positions[0] else "")

    # Formatting
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_xticks(np.arange(0, width, 1))
    ax.set_yticks(np.arange(0, height, 1))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True)
    ax.legend()

    # Save the map to a file
    filename = "city_map.png"
    plt.savefig(filename)
    plt.close()

    return filename
