import fitz
import cv2
import numpy as np
from PIL import Image
from doclayout_yolo import YOLOv10
import io
from huggingface_hub import hf_hub_download


def inference(model, pixmap, imgsz=1024, conf=0.2, device="cpu"):
    """
    Inference function that takes a PyMuPDF pixmap and runs YOLO prediction
    
    Args:
        pixmap: PyMuPDF pixmap object from page.get_pixmap()
        imgsz: Prediction image size (default: 1024)
        conf: Confidence threshold (default: 0.2)
        device: Device to use (default: "cuda:0")
    
    Returns:
        annotated_frame: The annotated image as numpy array
    """
    # Convert PyMuPDF pixmap to PIL Image
    img_data = pixmap.tobytes("ppm")
    pil_image = Image.open(io.BytesIO(img_data))
    
    # Alternative method using numpy array:
    # img_array = np.frombuffer(pixmap.samples, dtype=np.uint8)
    # img_array = img_array.reshape(pixmap.height, pixmap.width, pixmap.n)
    # pil_image = Image.fromarray(img_array)
    
    det_res = model.predict(
        pil_image,         # Pass PIL image directly
        imgsz=imgsz,       # Prediction image size
        conf=conf,         # Confidence threshold
        device=device      # Device to use
    )

    annotated_frame = det_res[0].plot(pil=True, line_width=5, font_size=20)
    
    annotated_array = np.array(annotated_frame)
    annotated_array = cv2.cvtColor(annotated_array, cv2.COLOR_RGB2BGR)
    
    return annotated_array, det_res
if __name__ == "__main__":
    filepath = hf_hub_download(repo_id="juliozhao/DocLayout-YOLO-DocStructBench", filename="doclayout_yolo_docstructbench_imgsz1024.pt")
    model = YOLOv10(filepath)

    doc = fitz.open("a-practical-guide-to-building-agents.pdf")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page2image = page.get_pixmap(dpi=300)
        
        annotated_image, detection_results = inference(model,page2image)
        
        cv2.imshow("Prediction Result", annotated_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        for detection in detection_results[0].boxes:
            print(f"Class: {detection.cls}, Confidence: {detection.conf}, Box: {detection.xyxy}")
        
        break 