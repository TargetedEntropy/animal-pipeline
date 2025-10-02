"""Extract representative frames with animals from video."""
import os
import logging
from typing import Dict, List
import cv2

logger = logging.getLogger(__name__)


def extract_images(num_images: int = 3, **context) -> Dict[str, List[str]]:
    """
    Extract ~3 representative frames with clearly visible animals.

    Args:
        num_images: Number of images to extract (default: 3)

    Returns:
        Dictionary with list of image paths
    """
    # Get detection metadata from previous task
    ti = context['task_instance']
    detection_metadata = ti.xcom_pull(task_ids='detect_animals', key='detection_metadata')

    if not detection_metadata:
        raise ValueError("No detection metadata found from detect_animals task")

    clip_path = detection_metadata['clip_path']
    video_id = detection_metadata['video_id']
    top_detections = detection_metadata['top_detections']

    if not top_detections:
        logger.warning("No detections found, skipping image extraction")
        return {'video_id': video_id, 'image_paths': []}

    logger.info(f"Extracting {num_images} frames from video...")

    # Open video
    cap = cv2.VideoCapture(clip_path)

    # Select frames to extract (top N detections)
    frames_to_extract = top_detections[:num_images]

    image_paths = []
    output_dir = os.path.dirname(clip_path)

    for idx, detection in enumerate(frames_to_extract):
        frame_number = detection['frame']
        timestamp = detection['timestamp']
        animal_class = detection['class']

        # Seek to the frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if ret:
            # Save the frame
            image_filename = f"{video_id}_frame_{idx+1}_{animal_class}_{timestamp:.2f}s.jpg"
            image_path = os.path.join(output_dir, image_filename)

            cv2.imwrite(image_path, frame)
            image_paths.append(image_path)

            logger.info(f"Saved frame {idx+1}: {image_filename}")
        else:
            logger.warning(f"Could not read frame {frame_number}")

    cap.release()

    logger.info(f"Extracted {len(image_paths)} images")

    result = {
        'video_id': video_id,
        'image_paths': image_paths
    }

    # Push to XCom for next tasks
    ti.xcom_push(key='image_metadata', value=result)

    return result
