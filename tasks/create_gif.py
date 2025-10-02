"""Create animated GIF from video segments with detected animals."""
import os
import logging
from typing import Dict
from moviepy import VideoFileClip

logger = logging.getLogger(__name__)


def create_gif(gif_duration: int = 5, **context) -> Dict[str, str]:
    """
    Generate a 5-10s animated GIF around timestamps with detected animals.

    Args:
        gif_duration: Duration of GIF in seconds (default: 5)

    Returns:
        Dictionary with gif_path
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
        logger.warning("No detections found, skipping GIF creation")
        return {'video_id': video_id, 'gif_path': None}

    # Use the timestamp of the best detection
    best_detection = top_detections[0]
    center_timestamp = best_detection['timestamp']

    logger.info(f"Creating GIF centered at {center_timestamp:.2f}s")

    # Load video
    video = VideoFileClip(clip_path)
    video_duration = video.duration

    # Calculate start and end times for GIF
    start_time = max(0, center_timestamp - gif_duration / 2)
    end_time = min(video_duration, center_timestamp + gif_duration / 2)

    # Adjust if we're at the boundaries
    actual_duration = end_time - start_time
    if actual_duration < gif_duration and start_time == 0:
        end_time = min(video_duration, gif_duration)
    elif actual_duration < gif_duration and end_time == video_duration:
        start_time = max(0, video_duration - gif_duration)

    logger.info(f"GIF segment: {start_time:.2f}s to {end_time:.2f}s")

    # Create GIF clip
    gif_clip = video.subclipped(start_time, end_time)

    # Resize for smaller file size (width=480px)
    gif_clip_resized = gif_clip.resized(width=480)

    # Save as GIF
    output_dir = os.path.dirname(clip_path)
    gif_path = os.path.join(output_dir, f"{video_id}_{best_detection['class']}.gif")

    gif_clip_resized.write_gif(
        gif_path,
        fps=15,  # Lower FPS for smaller file size
        logger=None  # Suppress verbose output
    )

    # Close video files
    gif_clip_resized.close()
    gif_clip.close()
    video.close()

    logger.info(f"GIF saved to: {gif_path}")

    result = {
        'video_id': video_id,
        'gif_path': gif_path,
        'animal_class': best_detection['class']
    }

    # Push to XCom for next tasks
    ti.xcom_push(key='gif_metadata', value=result)

    return result
