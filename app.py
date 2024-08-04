from flask import Flask, render_template, send_file, redirect, url_for
import map_generator
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_map')
def generate_map():
    map_file = map_generator.generate_city_map()
    return redirect(url_for('download_map', filename=map_file))

@app.route('/download/<filename>')
def download_map(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
