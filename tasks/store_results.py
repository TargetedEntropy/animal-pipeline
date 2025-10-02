"""Organize and store pipeline results."""
import os
import shutil
import logging
import json
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def store_results(**context) -> Dict[str, str]:
    """
    Organize generated images/GIFs into a results directory.

    Returns:
        Dictionary with storage information
    """
    # Get all metadata from previous tasks
    ti = context['task_instance']
    video_metadata = ti.xcom_pull(task_ids='download_video', key='video_metadata')
    detection_metadata = ti.xcom_pull(task_ids='detect_animals', key='detection_metadata')
    image_metadata = ti.xcom_pull(task_ids='extract_images', key='image_metadata')
    gif_metadata = ti.xcom_pull(task_ids='create_gif', key='gif_metadata')

    video_id = video_metadata['video_id']

    # Create organized directory structure
    base_results_dir = "/opt/airflow/results"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_results_dir, f"{video_id}_{timestamp}")

    os.makedirs(run_dir, exist_ok=True)

    logger.info(f"Organizing results in: {run_dir}")

    # Copy/move images
    image_dir = os.path.join(run_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    stored_images = []
    if image_metadata and image_metadata.get('image_paths'):
        for img_path in image_metadata['image_paths']:
            if os.path.exists(img_path):
                dest_path = os.path.join(image_dir, os.path.basename(img_path))
                shutil.copy2(img_path, dest_path)
                stored_images.append(dest_path)
                logger.info(f"Copied image: {os.path.basename(img_path)}")

    # Copy GIF
    gif_path = None
    if gif_metadata and gif_metadata.get('gif_path') and os.path.exists(gif_metadata['gif_path']):
        gif_dest = os.path.join(run_dir, os.path.basename(gif_metadata['gif_path']))
        shutil.copy2(gif_metadata['gif_path'], gif_dest)
        gif_path = gif_dest
        logger.info(f"Copied GIF: {os.path.basename(gif_dest)}")

    # Create metadata summary
    summary = {
        'run_id': video_id,
        'timestamp': timestamp,
        'video_title': video_metadata.get('title', 'Unknown'),
        'video_duration': video_metadata.get('duration', 0),
        'total_detections': detection_metadata.get('total_detections', 0),
        'animals_detected': list(set([d['class'] for d in detection_metadata.get('all_detections', [])])),
        'num_images_extracted': len(stored_images),
        'gif_created': gif_path is not None,
        'results_directory': run_dir
    }

    # Save summary as JSON
    summary_path = os.path.join(run_dir, 'summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Results stored successfully")
    gif_status = "GIF created" if gif_path else "no GIF"
    logger.info(f"Summary: {summary['total_detections']} detections, "
                f"{len(stored_images)} images, {gif_status}")

    result = {
        'run_directory': run_dir,
        'summary': summary
    }

    return result
