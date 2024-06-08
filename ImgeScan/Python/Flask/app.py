import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import cv2
import easyocr

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Create uploads directory if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Get processing parameters from form
        threshold = int(request.form.get('threshold', 150))
        noise_reduction = bool(request.form.get('noise_reduction', False))
        morph_transform = request.form.get('morph_transform', 'none')

        # Process the image
        result = process_image(filepath, threshold, noise_reduction, morph_transform)
        return render_template('result.html', result=result, filename=filename, enumerate=enumerate)

    return redirect(request.url)

def process_image(image_path, threshold, noise_reduction, morph_transform):
    # Read the image using OpenCV
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding
    _, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY_INV)

    # Apply noise reduction if selected
    if noise_reduction:
        binary_image = cv2.medianBlur(binary_image, 3)

    # Apply morphological transformations if selected
    if morph_transform == 'dilation':
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary_image = cv2.dilate(binary_image, kernel, iterations=1)
    elif morph_transform == 'erosion':
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary_image = cv2.erode(binary_image, kernel, iterations=1)

    # Initialize EasyOCR reader
    reader = easyocr.Reader(['en'])
    results = reader.readtext(binary_image)

    # Initialize a list to store detected digit numbers and their coordinates
    digit_numbers = []

    # Iterate over the results to extract coordinates and digits
    for (bbox, text, prob) in results:
        if text.isdigit():
            (top_left, top_right, bottom_right, bottom_left) = bbox
            x1, y1 = int(top_left[0]), int(top_left[1])
            x2, y2 = int(bottom_right[0]), int(bottom_right[1])
            digit_numbers.append((text, x1, y1, x2, y2))

    # Draw rectangles around the detected numbers
    for number, x1, y1, x2, y2 in digit_numbers:
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        coordinates_text = f"({center_x}, {center_y})"
        cv2.putText(image, coordinates_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)

    # Save the output image
    output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_' + os.path.basename(image_path))
    cv2.imwrite(output_image_path, image)

    return {'numbers': digit_numbers, 'output_image_path': output_image_path}

if __name__ == '__main__':
    app.run(debug=True)
