import matplotlib.pyplot as plt
import numpy as np
import random
import os
from datetime import datetime
from flask import Flask, render_template, send_file, redirect, url_for, request, jsonify
import logging

app = Flask(__name__)

GENERATED_MAPS_DIR = 'static/generated_maps'

if not os.path.exists(GENERATED_MAPS_DIR):
    os.makedirs(GENERATED_MAPS_DIR)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

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
    road_positions = []
    street_units = 0
    black_fields_count = 0

    # Generate streets
    for x in range(0, width, 2):
        for y in range(0, height, 2):
            if random.choice([True, False]):
                # Horizontal street
                length = random.randint(1, 2) * 2
                for i in range(length + 1):
                    pos_x, pos_y = x + i + 0.5, y + 0.5
                    if pos_x < width and pos_y < height:
                        road_positions.append((pos_x, pos_y))  # Center the position
                        black_fields_count += 1
                    street_units += 1
                ax.add_patch(plt.Rectangle((x, y), length, 1, color="black"))
            if random.choice([True, False]):
                # Vertical street
                length = random.randint(1, 2) * 2
                for i in range(length + 1):
                    pos_x, pos_y = x + 0.5, y + i + 0.5
                    if pos_x < width and pos_y < height:
                        road_positions.append((pos_x, pos_y))  # Center the position
                        black_fields_count += 1
                    street_units += 1
                ax.add_patch(plt.Rectangle((x, y), 1, length, color="black"))
    logging.debug(f"Streets generated with {street_units} units")
    logging.debug(f"Number of black fields: {black_fields_count}")

    # Place warehouse
    warehouse_x, warehouse_y = random.choice(road_positions)
    ax.scatter(warehouse_x, warehouse_y, color="red", s=100, label="Warehouse")
    logging.debug(f"Warehouse placed at: ({warehouse_x}, {warehouse_y})")

    # Remove warehouse location from possible scooter positions
    road_positions.remove((warehouse_x, warehouse_y))

    # Determine the number of scooters based on density
    if scooter_density == 'little':
        num_scooters = random.randint(5, 10)
    elif scooter_density == 'normal':
        num_scooters = random.randint(10, 20)
    else:
        num_scooters = random.randint(20, 30)
    logging.debug(f"Scooter density set to: {scooter_density}, number of scooters: {num_scooters}")

    # Determine the number of full batteries based on density
    if battery_density == 'little':
        num_batteries = random.randint(0, int(0.2 * num_scooters))
    elif battery_density == 'normal':
        num_batteries = random.randint(int(0.2 * num_scooters), int(0.4 * num_scooters))
    else:
        num_batteries = random.randint(int(0.4 * num_scooters), int(0.6 * num_scooters))
    logging.debug(f"Battery density set to: {battery_density}, number of full batteries: {num_batteries}")

    # Place scooters
    scooter_positions = random.sample(road_positions, num_scooters)
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
