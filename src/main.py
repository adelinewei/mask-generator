import cv2
from datetime import datetime
import numpy as np
import os
from typing import Any


def merge_similar_lines(lines: list[np.ndarray], threshold_rho: int, threshold_theta: int) -> list[np.ndarray]:
    merged_lines = []
    for line in lines:
        rho, theta = line[0]
        merged = False
        for merged_line in merged_lines:
            merged_rho, merged_theta = merged_line[0]
            if abs(rho - merged_rho) < threshold_rho and abs(theta - merged_theta) < threshold_theta:
                # TODO: which way to generate rho and theta is making more sense?
                # merged_line[0] = [(rho + merged_rho) / 2, (theta + merged_theta) / 2]
                # merged_line[0] = [merged_rho, merged_theta]
                merged = True
                break
        if not merged:
            merged_lines.append(line)
    return merged_lines
 

def draw_lines(img: type[np.ndarray], lines: list[np.ndarray], color: list[int]=[0, 255, 0], thickness: int=2) -> None:
    for line in lines:
        for rho,theta in line:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))

        cv2.line(img,(x1,y1),(x2,y2),color,thickness)


def empty(_value: int) -> None:
    # This callback function is continously called for every MOUSEMOVE (from MOUSEDOWN to mouse MOUSEUP)
    pass


def save_file(filename: str, img: np.ndarray, extension: str='jpg') -> None:
    root_directory = os.path.dirname(os.path.dirname(__file__))
    output_directory = f'{root_directory}/output'
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
    file_path = f'{output_directory}/{filename}.{extension}'
    cv2.imwrite(file_path, img)
    print(f'File is saved! Path to the file: {file_path}')


def draw_mask(merged_lines: list[np.ndarray]) -> None:
    # print(f'[DRAW_MASK] merged_lines: {merged_lines}, len of merged_lines: {len(merged_lines)}')
    # Create a blank image with the same size as the original image
    mask = np.full_like(image, 255) # (255, 255, 255)
    draw_lines(mask, merged_lines, color=[0, 0, 0], thickness=3)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'mask_{now}'
    save_file(filename, mask)
    cv2.imshow('mask', mask)


def mouse_clicked_handler(event:int, x:int, y:int, flags:int, params:Any) -> None:
    global p0, p1
    global merged_lines
    if event == cv2.EVENT_RBUTTONDOWN:
        for i, line in enumerate(merged_lines):
            rho, theta = line[0]
            dist = np.abs(x * np.cos(theta) + y * np.sin(theta) - rho)
            if dist < 5:  # Adjust the threshold for hover sensitivity
                del merged_lines[i]
        print(f'[AFTER EVENT_RBUTTONDOWN] length of merged_lines: {len(merged_lines)}')


def process_image() -> None:
    global merged_lines
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    # https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html#gaabe8c836e97159a9193fb0b11ac52cf1
    blurred_image = cv2.GaussianBlur(gray_image, (9, 9), 0)
    # https://docs.opencv.org/3.4/d7/de1/tutorial_js_canny.html
    edges_image = cv2.Canny(blurred_image, 50, 120)
    
    rho_resolution = 1
    theta_resolution = np.pi/180
    threshold = 155
    hough_lines = cv2.HoughLines(edges_image, rho_resolution , theta_resolution , threshold)
    merged_lines = merge_similar_lines(hough_lines, threshold_rho, threshold_theta)


def merge_line_threshold_changed() -> None:
    global threshold_rho, new_threshold_rho
    global threshold_theta, new_threshold_theta

    threshold_rho = new_threshold_rho
    threshold_theta = new_threshold_theta


if __name__ == '__main__':
    cv2.namedWindow('demo')
    cv2.resizeWindow('demo', 640, 240)
    cv2.createTrackbar('Rho', 'demo', 10, 100, empty)
    cv2.createTrackbar('Theta', 'demo', 50, 180, empty)
    cv2.setMouseCallback('demo', mouse_clicked_handler)

    threshold_rho = 0
    threshold_theta = 0
    merged_lines = []
    p0, p1 = (0, 0), (0, 0)

    while True:
        image = cv2.imread('car_parking_img.png')   # TODO: read image name from configuration
        new_threshold_rho = cv2.getTrackbarPos('Rho', 'demo')
        new_threshold_theta = cv2.getTrackbarPos('Theta', 'demo')
        if (new_threshold_rho != threshold_rho) or (new_threshold_theta != threshold_theta):
            merge_line_threshold_changed()
            process_image()

        draw_lines(image, merged_lines)
        cv2.imshow('demo', image)
        
        key = cv2.waitKey(100)
        if key == ord('m'):
            draw_mask(merged_lines)
        if key == ord('q'):
            cv2.destroyAllWindows()  # TODO: is it needed?
            break