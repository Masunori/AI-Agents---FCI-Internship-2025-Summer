import pymupdf
import fitz
import cv2
import numpy as np
from PIL import Image
from doclayout_yolo import YOLOv10
import io
from huggingface_hub import hf_hub_download
from DLA_example import inference
import torch
def get_text_blocks(doc_page):
    text_blocks = doc_page.get_text("blocks") # return (x0,y0,x1,y1, "text", block_n0, block_type)
    block_list = []
    for block in text_blocks:
        if len(block) > 5: # it is a text block
            block_list.append({
                "text": block[4].strip(),
                "bbox": (block[0], block[1], block[2], block[3])
            })
    return block_list

def get_page_size_for_inference(page, pixmap, base_size=1024):
    """
    Calculate appropriate inference size based on page dimensions
    
    Args:
        page: PyMuPDF page object
        pixmap: PyMuPDF pixmap object
        base_size: Base size for inference (default: 1024)
    
    Returns:
        Optimal image size for inference
    """
    # Get page dimensions in points
    page_rect = page.rect
    page_width = page_rect.width
    page_height = page_rect.height
    
    # Get pixmap dimensions (actual image size)
    img_width = pixmap.width
    img_height = pixmap.height
    
    aspect_ratio = img_width / img_height
    longer_dim = max(img_width, img_height)
    if longer_dim <= base_size:
        inference_size = base_size
    else:
        # Scale down proportionally
        inference_size = base_size
    inference_size = max(32, (inference_size // 32) * 32)
    
    return inference_size

# PyMuPDF returns coordinates in PDF points (1 point = 1/72 inch), 
# while DocLayout-YOLOv10 returns coordinates in pixels of the rendered image

def convert_pymupdf_to_pixel_coords(bbox, pixmap, page):
    """
    Convert PyMuPDF coordinates (in points) to pixel coordinates
    to match the coordinate system used by DocLayout-YOLOv10
    
    Args:
        bbox: PyMuPDF bounding box in points (x0, y0, x1, y1)
        pixmap: PyMuPDF pixmap object
        page: PyMuPDF page object
    
    Returns:
        Converted bounding box in pixel coordinates
    """
    # Get the scaling factors
    page_rect = page.rect
    scale_x = pixmap.width / page_rect.width
    scale_y = pixmap.height / page_rect.height
    
    x0, y0, x1, y1 = bbox
    
    # Convert to pixel coordinates
    pixel_x0 = x0 * scale_x
    pixel_y0 = y0 * scale_y
    pixel_x1 = x1 * scale_x
    pixel_y1 = y1 * scale_y
    
    return (pixel_x0, pixel_y0, pixel_x1, pixel_y1)

def get_class_label(class_tensor):
    CLASS_LABELS = {
        0: "text",
        1: "title", 
        2: "list",
        3: "table",
        4: "figure",
        5: "header",
        6: "footer",
        7: "reference",
        8: "equation",
        9: "caption",
        10: "footnote"
    }
    class_idx = int(class_tensor.item()) if hasattr(class_tensor, "item") else int(class_tensor)
    return CLASS_LABELS.get(class_idx, f"Unknown class {class_idx}")
def calculated_area(x1,y1,x2,y2):
    '''Given coordinate of 2 points of a rectangle in 2D space, return its area'''
    return abs(x2-x1)*abs(y2-y1)
def check_interval_overlap(a1, b1, x1, y1):
    '''Given 2 intervals in the form (a1,b1) and (x1,y1), check if they overlap'''
    min_a, max_a = min(a1, b1), max(a1, b1)
    min_x, max_x = min(x1, y1), max(x1, y1)
    
    # Two intervals overlap if: max(start1, start2) < min(end1, end2)
    return max(min_a, min_x) < min(max_a, max_x)

def calculate_overlap_interval(a1, b1, x1, y1):
    '''Given 2 overlapping intervals, calculate their overlap length'''
    min_a, max_a = min(a1, b1), max(a1, b1)
    min_x, max_x = min(x1, y1), max(x1, y1)
    
    overlap_start = max(min_a, min_x)
    overlap_end = min(max_a, max_x)
    return overlap_end - overlap_start

def calculate_iou(coordinate1, coordinate2):
    '''Given 2 numpy array with form of [x1,y1,x2,y2], calculate the Intersection over Union metric'''
    try:
        x1_1, y1_1, x2_1, y2_1 = coordinate1
        x1_2, y1_2, x2_2, y2_2 = coordinate2
        
        x_overlap = check_interval_overlap(x1_1, x2_1, x1_2, x2_2)
        y_overlap = check_interval_overlap(y1_1, y2_1, y1_2, y2_2)
        
        if x_overlap and y_overlap:
            width_overlap = calculate_overlap_interval(x1_1, x2_1, x1_2, x2_2)
            height_overlap = calculate_overlap_interval(y1_1, y2_1, y1_2, y2_2)
            intersection_area = width_overlap * height_overlap
            
            area1 = calculated_area(x1_1, y1_1, x2_1, y2_1)
            area2 = calculated_area(x1_2, y1_2, x2_2, y2_2)
            union_area = area1 + area2 - intersection_area
            
            if union_area == 0:
                return 0
                
            return intersection_area / union_area
        return 0
    except Exception as e:
        print(f"Error in IoU calculation: {e}")
        return 0

def get_closest_bbox(text_bbox, dla_bboxes, pixmap, page):
    '''Given a text bbox extracted from pymupdf, find the most overlap bbox from DLA inference result'''
    # Convert PyMuPDF coordinates to pixel coordinates
    pixel_text_bbox = convert_pymupdf_to_pixel_coords(text_bbox, pixmap, page)
    text_bbox_np = np.array(list(pixel_text_bbox))
    
    iou_max = 0
    text_bbox_class = None
    for detection in dla_bboxes:
        detection_class, detection_bbox = get_class_label(detection.cls), detection.xyxy.numpy()[0]
        iou = calculate_iou(text_bbox_np, detection_bbox)
        if iou > iou_max:
            iou_max = iou
            text_bbox_class = detection_class
    return iou_max, text_bbox_class
if __name__ == "__main__":
    filepath = hf_hub_download(repo_id="juliozhao/DocLayout-YOLO-DocStructBench", filename="doclayout_yolo_docstructbench_imgsz1024.pt")
    model = YOLOv10(filepath)
    doc = fitz.open('Group 10.pdf')
    for page_num in range(len(doc)):
        page = doc[page_num]
        pixmap = page.get_pixmap(dpi=300)
        
        text_elements_in_page = get_text_blocks(page)
        
        optimal_size = get_page_size_for_inference(page, pixmap, base_size=1024)
        
        _, dla_results = inference(model, pixmap, imgsz=optimal_size)
        
        dla_bboxes = dla_results[0].boxes
        for block in text_elements_in_page:
            text = block["text"]
            text_bbox = block["bbox"]
            iou, detection_class = get_closest_bbox(text_bbox, dla_bboxes, pixmap, page)
            print(f"{detection_class}: {text}\n", iou)

        # dla result contains those attributes: cls (class), conf (confidence), xyxy (location)
        
        
        break