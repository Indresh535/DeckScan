import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import cv2
import easyocr
import numpy as np
from selectinwindow import DragRectangle, dragrect
from PIL import Image, ImageSequence

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

@app.route('/process_area', methods=['POST'])
def process_area():
    data = request.json
    filename = data['filename']
    x1 = data['x1']
    y1 = data['y1']
    x2 = data['x2']
    y2 = data['y2']
    
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image = cv2.imread(image_path)
    hex_color = get_hex_color(image, x1, y1, x2, y2)
    
    return jsonify({'color': hex_color})



def get_hex_color(image, x1, y1, x2, y2):
    # Crop the area of the detected number
    region = image[y1:y2, x1:x2]
    # Calculate the average color in the cropped area
    average_color = region.mean(axis=0).mean(axis=0)
    # Convert the average color to hexadecimal format
    color_hex = "#{:02x}{:02x}{:02x}".format(int(average_color[2]), int(average_color[1]), int(average_color[0]))
    return color_hex



def overlay_gif(image, gif_path, x1, y1, x2, y2):
    # Open the GIF file
    gif = Image.open(gif_path)
    # Convert GIF frames to a format compatible with OpenCV
    gif_frames = [cv2.cvtColor(np.array(frame), cv2.COLOR_RGBA2BGRA) for frame in ImageSequence.Iterator(gif)]

    # Resize the GIF frames to fit the detected area
    for i in range(len(gif_frames)):
        gif_frames[i] = cv2.resize(gif_frames[i], (x2 - x1, y2 - y1))
        
    # Overlay the GIF frames on the image
    for frame in gif_frames:
        y1_frame, y2_frame, x1_frame, x2_frame = y1, y1 + frame.shape[0], x1, x1 + frame.shape[1]
        alpha_s = frame[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s
        for c in range(0, 3):
            image[y1_frame:y2_frame, x1_frame:x2_frame, c] = (
                alpha_s * frame[:, :, c] + alpha_l * image[y1_frame:y2_frame, x1_frame:x2_frame, c]
            )
    return image


def process_image(image_path, threshold, noise_reduction, morph_transform):
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
            hex_color = get_hex_color(image, x1, y1, x2, y2)
            digit_numbers.append((text, x1, y1, x2, y2, hex_color))

    gif_path = './static/RedBtn.gif'
    for number, x1, y1, x2, y2, hex_color in digit_numbers:
        image = overlay_gif(image, gif_path, x1, y1, x2, y2)
        
    # Draw rectangles around the detected numbers
    # for number, x1, y1, x2, y2 in digit_numbers:
    #     # image = overlay_gif(image, gif_path, x1, y1, x2, y2)
    #     cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #     center_x = (x1 + x2) // 2
    #     center_y = (y1 + y2) // 2
    #     coordinates_text = f"({center_x}, {center_y})"
    #     cv2.putText(image, coordinates_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)

    # Save the output image
    output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_' + os.path.basename(image_path))
    cv2.imwrite(output_image_path, image)

    return {'numbers': digit_numbers, 'output_image_path': output_image_path}
    print("process_image image_path", image_path)
    # Read the image using OpenCV
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print("gray_image ", gray_image)
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
            # digit_numbers.append((text, x1, y1, x2, y2, get_hex_color(image, x1, y1, x2, y2)))
            digit_numbers.append((text, x1, y1, x2, y2))

    gif_path = './static/RedBtn.gif'
    # Draw rectangles around the detected numbers
    for number, x1, y1, x2, y2 in digit_numbers:
        # image = overlay_gif(image, gif_path, x1, y1)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        coordinates_text = f"({center_x}, {center_y})"
        cv2.putText(image, coordinates_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)

    # Save the output image
    output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_' + os.path.basename(image_path))
    cv2.imwrite(output_image_path, image)

    return {'numbers': digit_numbers, 'output_image_path': output_image_path}

def process_image_area(image_path, x1, y1, x2, y2):
    # Read the image using OpenCV
    image = cv2.imread(image_path)
    print("image image_path", image_path)
    print("image process path selctd area", image)
    print(f"Selected area coordinates: ({x1}, {y1}) to ({x2}, {y2})")
    
    if image is None:
        return {'error': 'Image not found'}
    # Ensure the coordinates are within the image dimensions
    height, width = image.shape[:2]
    x1, x2 = sorted([max(0, x1), min(width, x2)])
    y1, y2 = sorted([max(0, y1), min(height, y2)])

    # Check if the selected area is valid and has a minimum size
    min_size = 10  # Minimum size for the selected area
    if (x2 - x1) < min_size or (y2 - y1) < min_size:
        return {'error': 'Selected area is too small'}

    area = image[y1:y2, x1:x2]
    print("Selected area shape:", area.shape)
    print("Selected area:", area)

    # Check if the area is not empty
    if area.size == 0:
        return {'error': 'Selected area is empty'}

    gray_area = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    _, binary_area = cv2.threshold(gray_area, 150, 255, cv2.THRESH_BINARY_INV)

    # Initialize EasyOCR reader
    reader = easyocr.Reader(['en'])
    results = reader.readtext(binary_area)

    # Initialize a list to store detected digit numbers and their coordinates
    digit_numbers = []

    # Iterate over the results to extract coordinates and digits
    for (bbox, text, prob) in results:
        if text.isdigit():
            (top_left, top_right, bottom_right, bottom_left) = bbox
            x1_area, y1_area = int(top_left[0]), int(top_left[1])
            x2_area, y2_area = int(bottom_right[0]), int(bottom_right[1])
            digit_numbers.append((text, x1 + x1_area, y1 + y1_area, x1 + x2_area, y1 + y2_area))

    return {'numbers': digit_numbers}

    # Read the image using OpenCV
    image = cv2.imread(image_path)
    area = image[y1:y2, x1:x2]
    gray_area = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    _, binary_area = cv2.threshold(gray_area, 150, 255, cv2.THRESH_BINARY_INV)

    # Initialize EasyOCR reader
    reader = easyocr.Reader(['en'])
    results = reader.readtext(binary_area)

    # Initialize a list to store detected digit numbers and their coordinates
    digit_numbers = []

    # Iterate over the results to extract coordinates and digits
    for (bbox, text, prob) in results:
        if text.isdigit():
            (top_left, top_right, bottom_right, bottom_left) = bbox
            x1_area, y1_area = int(top_left[0]), int(top_left[1])
            x2_area, y2_area = int(bottom_right[0]), int(bottom_right[1])
            digit_numbers.append((text, x1 + x1_area, y1 + y1_area, x1 + x2_area, y1 + y2_area))

    print("Digit numbers detected:", digit_numbers)
    return {'numbers': digit_numbers}


@app.route('/select_area', methods=['POST'])
def select_area():
    global rect, img

    data = request.get_json()
    startX, startY = data['startX'], data['startY']
    endX, endY = data['endX'], data['endY']

    x1 = min(startX, endX)
    y1 = min(startY, endY)
    x2 = max(startX, endX)
    y2 = max(startY, endY)

    # Read the image using OpenCV
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], request.json['filename'])
    img = cv2.imread(image_path)

    # Ensure coordinates are within image bounds
    img_height, img_width = img.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(img_width, x2), min(img_height, y2)

    # Check if area coordinates are valid
    if x1 >= x2 or y1 >= y2:
        return jsonify({'error': 'Invalid area selected.'})

    # Crop the selected area
    selected_area = img[y1:y2, x1:x2]

    # Convert to base64 for return
    retval, buffer = cv2.imencode('.jpg', selected_area)
    img_str = base64.b64encode(buffer).decode('utf-8')

    return jsonify({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'selected_area': img_str})

if __name__ == '__main__':
    app.run(debug=True)



# import os
# from flask import Flask, render_template, request, redirect, url_for
# from werkzeug.utils import secure_filename
# import cv2
# import easyocr

# # Initialize Flask app
# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'static/uploads'
# app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# # Create uploads directory if not exists
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return redirect(request.url)
#     file = request.files['file']
#     if file.filename == '':
#         return redirect(request.url)
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)

#         # Get processing parameters from form
#         threshold = int(request.form.get('threshold', 150))
#         noise_reduction = bool(request.form.get('noise_reduction', False))
#         morph_transform = request.form.get('morph_transform', 'none')

#         # Process the image
#         result = process_image(filepath, threshold, noise_reduction, morph_transform)
#         return render_template('result.html', result=result, filename=filename, enumerate=enumerate)

#     return redirect(request.url)

# def process_image(image_path, threshold, noise_reduction, morph_transform):
#     # Read the image using OpenCV
#     image = cv2.imread(image_path)
#     gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
#     # Apply thresholding
#     _, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY_INV)

#     # Apply noise reduction if selected
#     if noise_reduction:
#         binary_image = cv2.medianBlur(binary_image, 3)

#     # Apply morphological transformations if selected
#     if morph_transform == 'dilation':
#         kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
#         binary_image = cv2.dilate(binary_image, kernel, iterations=1)
#     elif morph_transform == 'erosion':
#         kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
#         binary_image = cv2.erode(binary_image, kernel, iterations=1)

#     # Initialize EasyOCR reader
#     reader = easyocr.Reader(['en'])
#     results = reader.readtext(binary_image)

#     # Initialize a list to store detected digit numbers and their coordinates
#     digit_numbers = []

#     # Iterate over the results to extract coordinates and digits
#     for (bbox, text, prob) in results:
#         if text.isdigit():
#             (top_left, top_right, bottom_right, bottom_left) = bbox
#             x1, y1 = int(top_left[0]), int(top_left[1])
#             x2, y2 = int(bottom_right[0]), int(bottom_right[1])
#             digit_numbers.append((text, x1, y1, x2, y2))

#     # Draw rectangles around the detected numbers
#     for number, x1, y1, x2, y2 in digit_numbers:
#         cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
#         center_x = (x1 + x2) // 2
#         center_y = (y1 + y2) // 2
#         coordinates_text = f"({center_x}, {center_y})"
#         cv2.putText(image, coordinates_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)

#     # Save the output image
#     output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output_' + os.path.basename(image_path))
#     cv2.imwrite(output_image_path, image)

#     return {'numbers': digit_numbers, 'output_image_path': output_image_path}

# if __name__ == '__main__':
#     app.run(debug=True)
