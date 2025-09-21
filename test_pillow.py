from flask import Flask, render_template, request, send_file
from PIL import Image
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_message(image_path, message, output_path):
    img = Image.open(image_path)
    pixels = img.load()
    width, height = img.size

    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '00000000'  # Null byte as a message terminator

    if len(binary_message) > width * height * 3:
        raise ValueError("Message too long for this image")

    bit_index = 0
    for y in range(height):
        for x in range(width):
            pixel = list(pixels[x, y])
            for channel in range(3):
                if bit_index < len(binary_message):
                    pixel[channel] = (pixel[channel] & 0xFE) | int(binary_message[bit_index])
                    bit_index += 1
            pixels[x, y] = tuple(pixel)
            if bit_index >= len(binary_message):
                break
        else:
            continue
        break

    img.save(output_path)

def decode_message(image_path):
    img = Image.open(image_path)
    pixels = img.load()
    width, height = img.size

    binary_message = []
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            for channel in range(3):
                binary_message.append(str(pixel[channel] & 1))

    message = ""
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i+8]
        if byte == ['0']*8:  # Null byte found
            break
        message += chr(int(''.join(byte), 2))
    
    if not message:
        return "No hidden message in the given image"
    return message 

def calculate_capacity(image_path):
    img = Image.open(image_path)
    width, height = img.size
    max_bits = width * height * 3
    max_bytes = max_bits // 8
    return {
        'width': width,
        'height': height,
        'pixels': width * height,
        'max_bits': max_bits,
        'max_bytes': max_bytes,
        'max_chars': max_bytes - 1  # Reserve 1 byte for terminator
    }

# ✅ Add home route to fix the 404 on "/"
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index')
def index_page():
    return render_template('index.html')

@app.route('/encode')
def encode_page():
    return render_template('encode.html')

@app.route('/decode')
def decode_page():
    return render_template('decode.html')

@app.route('/capacity')
def capacity_page():
    return render_template('capacity.html')

@app.route('/encode_message', methods=['POST'])
def encode():
    if 'image' not in request.files or 'message' not in request.form:
        return "Invalid request", 400

    image = request.files['image']
    if not allowed_file(image.filename):
        return "Invalid file type", 400

    message = request.form['message']
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'encoded_' + image.filename)

    image.save(image_path)
    encode_message(image_path, message, output_path)

    return send_file(output_path, as_attachment=True)

@app.route('/decode_message', methods=['POST'])
def decode():
    if 'image' not in request.files:
        return "Invalid request", 400

    image = request.files['image']
    if not allowed_file(image.filename):
        return "Invalid file type", 400

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(image_path)

    message = decode_message(image_path)
    return render_template('decode_result.html', message=message)

@app.route('/calculate_capacity', methods=['POST'])
def calculate():
    if 'image' not in request.files:
        return "Invalid request", 400

    image = request.files['image']
    if not allowed_file(image.filename):
        return "Invalid file type", 400

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(image_path)
    
    capacity = calculate_capacity(image_path)
    return render_template('capacity_result.html', capacity=capacity)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
