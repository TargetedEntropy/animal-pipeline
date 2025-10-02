"""Detect animals in video using YOLOv8."""
import os
import logging
from typing import Dict, List
import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)

# COCO dataset animal classes
ANIMAL_CLASSES = [
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant',
    'bear', 'zebra', 'giraffe'
]


def detect_animals(confidence_threshold: float = 0.5, **context) -> Dict:
    """
    Detect animals in the trimmed video clip using YOLOv8.

    Args:
        confidence_threshold: Minimum confidence for detections (default: 0.5)

    Returns:
        Dictionary with detection metadata including timestamps, boxes, and labels
    """
    # Get clip metadata from previous task
    ti = context['task_instance']
    clip_metadata = ti.xcom_pull(task_ids='trim_clip', key='clip_metadata')

    if not clip_metadata:
        raise ValueError("No clip metadata found from trim_clip task")

    clip_path = clip_metadata['clip_path']
    video_id = clip_metadata['video_id']

    logger.info(f"Loading YOLOv8 model...")
    model = YOLO('yolov8n.pt')  # Use nano model for speed

    logger.info(f"Detecting animals in: {clip_path}")

    # Open video
    cap = cv2.VideoCapture(clip_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    detections = []
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Run detection every frame
        results = model(frame, verbose=False)

        # Process results
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get class name
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])

                # Only keep animal detections above threshold
                if class_name in ANIMAL_CLASSES and confidence >= confidence_threshold:
                    timestamp = frame_idx / fps

                    detection = {
                        'frame': frame_idx,
                        'timestamp': timestamp,
                        'class': class_name,
                        'confidence': confidence,
                        'bbox': box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    }
                    detections.append(detection)

                    logger.info(
                        f"Frame {frame_idx} ({timestamp:.2f}s): "
                        f"{class_name} ({confidence:.2f})"
                    )

        frame_idx += 1

    cap.release()

    logger.info(f"Total detections: {len(detections)}")

    # Find frames with highest confidence detections
    if detections:
        # Sort by confidence and get top detections
        sorted_detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        top_detections = sorted_detections[:5]  # Top 5 detections

        logger.info(f"Top detection: {top_detections[0]['class']} at {top_detections[0]['timestamp']:.2f}s")
    else:
        logger.warning("No animals detected in video!")
        top_detections = []

    result = {
        'video_id': video_id,
        'clip_path': clip_path,
        'total_detections': len(detections),
        'all_detections': detections,
        'top_detections': top_detections,
        'fps': fps,
        'total_frames': total_frames
    }

    # Push to XCom for next tasks
    ti.xcom_push(key='detection_metadata', value=result)

    return result
