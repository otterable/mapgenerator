import matplotlib.pyplot as plt
import numpy as np
import random
import os
from datetime import datetime
from flask import Flask, render_template, send_file, redirect, url_for, request, jsonify
import logging
from collections import deque

app = Flask(__name__)

GENERATED_MAPS_DIR = 'static/generated_maps'

if not os.path.exists(GENERATED_MAPS_DIR):
    os.makedirs(GENERATED_MAPS_DIR)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Suppress Matplotlib debug logs
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)

def generate_city_map(output_dir, scooter_density='normal', battery_density='normal'):
    logging.debug("Starting map generation")
    width = 20  # units (20 cm)
    height = 20  # units (20 cm)
    street_width = 1

    # Create the figure and axis for the A4 size
    fig, ax = plt.subplots(figsize=(21/2.54, 29.7/2.54))  # A4 size in inches
    ax.set_aspect('equal', adjustable='box')
    logging.debug("Figure and axis created")

    # Adjust the position of the map within the A4 page
    left_margin = (21 - 20) / 2 / 2.54  # left margin in inches
    bottom_margin = (29.7 - 20) / 2 / 2.54  # bottom margin in inches
    ax.set_position([left_margin / (21 / 2.54), bottom_margin / (29.7 / 2.54), 20 / 21, 20 / 29.7])  # [left, bottom, width, height]

    # Track road positions for scooter placement and count black fields
    road_positions = set()
    street_units = 0
    black_fields_count = 0
    street_number = 1

    # Initialize grid for street connectivity check
    grid = np.zeros((width, height), dtype=int)

    def add_street(x, y, length, orientation):
        nonlocal street_units, black_fields_count, street_number
        if orientation == 'horizontal':
            if x + length > width:
                return False  # Out of bounds
            for i in range(length):
                pos_x, pos_y = x + i, y
                if grid[pos_x, pos_y] != 0:
                    return False  # Overlapping street
            for i in range(length):
                pos_x, pos_y = x + i, y
                road_positions.add((pos_x + 0.5, pos_y + 0.5))  # Center the position
                black_fields_count += 1
                grid[pos_x, pos_y] = 1
            ax.add_patch(plt.Rectangle((x, y), length, 1, color="black"))
            ax.text(x + length/2, y + 0.5, str(street_number), color="white", ha='center', va='center')
            logging.debug(f"Street {street_number} (horizontal) at ({x}, {y}) with length {length}")
            street_number += 1
            street_units += length
            return True
        elif orientation == 'vertical':
            if y + length > height:
                return False  # Out of bounds
            for i in range(length):
                pos_x, pos_y = x, y + i
                if grid[pos_x, pos_y] != 0:
                    return False  # Overlapping street
            for i in range(length):
                pos_x, pos_y = x, y + i
                road_positions.add((pos_x + 0.5, pos_y + 0.5))  # Center the position
                black_fields_count += 1
                grid[pos_x, pos_y] = 1
            ax.add_patch(plt.Rectangle((x, y), 1, length, color="black"))
            ax.text(x + 0.5, y + length/2, str(street_number), color="white", ha='center', va='center')
            logging.debug(f"Street {street_number} (vertical) at ({x}, {y}) with length {length}")
            street_number += 1
            street_units += length
            return True
        return False

    # Generate at least one street in every row and column
    for y in range(0, height, 2):
        length = random.choice([2, 4])
        x = random.randint(0, width - length)
        add_street(x, y, length, 'horizontal')

    for x in range(0, width, 2):
        length = random.choice([2, 4])
        y = random.randint(0, height - length)
        add_street(x, y, length, 'vertical')

    # Ensure 50% to 80% of streets are connected from both ends
    connection_probability = random.uniform(0.5, 0.8)
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            if random.random() < connection_probability:
                if random.random() < 0.5:
                    # Try to connect horizontally
                    length = random.choice([2, 4])
                    add_street(x, y, length, 'horizontal')
                else:
                    # Try to connect vertically
                    length = random.choice([2, 4])
                    add_street(x, y, length, 'vertical')

    logging.debug(f"Streets generated with {street_units} units")
    logging.debug(f"Number of black fields: {black_fields_count}")

    # Ensure there are valid road positions for the warehouse
    if not road_positions:
        logging.error("No roads generated. Cannot place the warehouse.")
        return None, 0, 0, 0, 0, ""

    # Place warehouse
    warehouse_x, warehouse_y = random.choice(list(road_positions))
    ax.scatter(warehouse_x, warehouse_y, color="red", s=100, label="Warehouse")
    logging.debug(f"Warehouse placed at: ({warehouse_x}, {warehouse_y})")

    # Remove warehouse location from possible scooter positions
    road_positions.remove((warehouse_x, warehouse_y))

    # Ensure all streets are accessible from the warehouse using BFS
    def bfs_connectivity_check(start_x, start_y):
        visited = set()
        queue = deque([(start_x, start_y)])
        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and grid[nx, ny] == 1:
                    queue.append((nx, ny))
        return visited

    warehouse_grid_x, warehouse_grid_y = int(warehouse_x - 0.5), int(warehouse_y - 0.5)
    connected_streets = bfs_connectivity_check(warehouse_grid_x, warehouse_grid_y)
    disconnected_streets = set((x, y) for x in range(width) for y in range(height) if grid[x, y] == 1 and (x, y) not in connected_streets)

    for x, y in disconnected_streets:
        grid[x, y] = 0
        ax.add_patch(plt.Rectangle((x, y), 1, 1, color="white"))

    road_positions = set((x + 0.5, y + 0.5) for x, y in connected_streets)
    black_fields_count = len(connected_streets)
    logging.debug(f"Connected black fields count: {black_fields_count}")

    # Determine the number of scooters based on density
    if scooter_density == 'little':
        num_scooters = random.randint(5, 10)
    elif scooter_density == 'normal':
        num_scooters = random.randint(10, 20)
    else:
        num_scooters = random.randint(20, 30)
    logging.debug(f"Scooter density set to: {scooter_density}, number of scooters: {num_scooters}")

    # Ensure the number of scooters does not exceed the available road positions
    num_scooters = min(num_scooters, len(road_positions))

    # Determine the number of full batteries based on density
    if battery_density == 'little':
        num_batteries = random.randint(0, int(0.2 * num_scooters))
    elif battery_density == 'normal':
        num_batteries = random.randint(int(0.2 * num_scooters), int(0.4 * num_scooters))
    else:
        num_batteries = random.randint(int(0.4 * num_scooters), int(0.6 * num_scooters))
    logging.debug(f"Battery density set to: {battery_density}, number of full batteries: {num_batteries}")

    # Place scooters
    scooter_positions = random.sample(list(road_positions), num_scooters)
    for x, y in scooter_positions:
        ax.scatter(x, y, color="blue", s=50, label="Scooter" if (x, y) == scooter_positions[0] else "")
    logging.debug("Scooters placed")

    # Add combined information box above the map
    info_text = f'Warehouse: {warehouse_x:.1f}, {warehouse_y:.1f}\nScooters: {num_scooters}\nFull Batteries: {num_batteries}\nStreet Units: {street_units}\nBlack Fields: {black_fields_count}'
    ax.text(0.5, 1.05, info_text, transform=ax.transAxes, fontsize=12, bbox=dict(facecolor='white', alpha=0.5), ha='center')
    logging.debug("Information box added above the map")

    # Formatting
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_xticks(np.arange(0, width + 1, 1))
    ax.set_yticks(np.arange(0, height + 1, 1))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True)
    ax.legend()
    logging.debug("Map formatting completed")

    # Add dotted lines
    ax.plot([0, 0], [0, -bottom_margin * 2.54], linestyle=':', color='black')
    ax.plot([width, width], [0, -bottom_margin * 2.54], linestyle=':', color='black')
    ax.plot([0, -left_margin * 2.54], [0, 0], linestyle=':', color='black')
    ax.plot([0, -left_margin * 2.54], [height, height], linestyle=':', color='black')
    ax.plot([width, width + left_margin * 2.54], [0, 0], linestyle=':', color='black')
    ax.plot([width, width + left_margin * 2.54], [height, height], linestyle=':', color='black')
    ax.plot([0, 0], [height, height + bottom_margin * 2.54], linestyle=':', color='black')
    ax.plot([width, width], [height, height + bottom_margin * 2.54], linestyle=':', color='black')

    # Add instructions in the empty space
    fig.text(0.5, 0.01, "Print this map on A4 paper with 100% scale to ensure each unit is exactly 1cm.", ha='center', fontsize=12)

    # Save the map to a file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_dir, f"city_map_{timestamp}.pdf")
    plt.savefig(filename, format='pdf', bbox_inches='tight')
    plt.close()
    logging.debug(f"Map saved as: {filename}")

    return filename, num_scooters, num_batteries, street_units, black_fields_count, timestamp

@app.route('/')
def index():
    files = os.listdir(GENERATED_MAPS_DIR)
    files = [f for f in files if f.endswith('.pdf')]
    logging.debug("Displaying index with generated maps history")
    return render_template('index.html', files=files)

@app.route('/generate_map', methods=['POST'])
def generate_map():
    scooter_density = request.form.get('scooter_density')
    battery_density = request.form.get('battery_density')
    map_file, num_scooters, num_batteries, street_units, black_fields_count, timestamp = generate_city_map(GENERATED_MAPS_DIR, scooter_density, battery_density)
    if map_file is None:
        return jsonify({"error": "Map generation failed. No streets were generated."}), 500
    map_details = {
        "filename": os.path.basename(map_file),
        "num_scooters": num_scooters,
        "num_batteries": num_batteries,
        "street_units": street_units,
        "black_fields_count": black_fields_count,
        "timestamp": timestamp
    }
    logging.debug("Map generation completed")
    return jsonify(map_details)

@app.route('/download/<filename>')
def download_map(filename):
    file_path = os.path.join(GENERATED_MAPS_DIR, filename)
    logging.debug(f"Downloading file: {file_path}")
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
