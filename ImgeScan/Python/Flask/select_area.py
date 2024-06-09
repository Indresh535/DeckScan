import cv2

# Global variables
rect = (0, 0, 1, 1)
drawing = False
img = None

def select_area(event, x, y, flags, param):
    global rect, drawing, img

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        rect = (x, y, 1, 1)
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_copy = img.copy()
            cv2.rectangle(img_copy, (rect[0], rect[1]), (x, y), (0, 255, 0), 2)
            cv2.imshow("image", img_copy)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        rect = (rect[0], rect[1], x - rect[0], y - rect[1])
        cv2.rectangle(img, (rect[0], rect[1]), (x, y), (0, 255, 0), 2)
        cv2.imshow("image", img)

def main():
    global img
    img_path = 'path_to_your_image.png'
    img = cv2.imread(img_path)

    if img is None:
        print("Could not open or find the image")
        return

    cv2.imshow("image", img)
    cv2.setMouseCallback("image", select_area)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

    x, y, w, h = rect
    selected_area = img[y:y+h, x:x+w]

    # Process the selected area (e.g., save or further analysis)
    cv2.imshow("Selected Area", selected_area)
    cv2.imwrite("selected_area.png", selected_area)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
