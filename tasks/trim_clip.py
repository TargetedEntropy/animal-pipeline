"""Trim video to 30-second clip using moviepy."""
import os
import logging
from typing import Dict
from moviepy import VideoFileClip

logger = logging.getLogger(__name__)


def trim_clip(clip_duration: int = 30, **context) -> Dict[str, str]:
    """
    Extract a 30-second clip from the downloaded video.

    Args:
        clip_duration: Length of clip in seconds (default: 30)

    Returns:
        Dictionary with clip_path and metadata
    """
    # Get video metadata from previous task
    ti = context['task_instance']
    video_metadata = ti.xcom_pull(task_ids='download_video', key='video_metadata')

    if not video_metadata:
        raise ValueError("No video metadata found from download_video task")

    video_path = video_metadata['video_path']
    video_id = video_metadata['video_id']
    duration = video_metadata.get('duration', 0)

    logger.info(f"Trimming video: {video_path}")
    logger.info(f"Total duration: {duration} seconds")

    # Load the video
    video = VideoFileClip(video_path)
    actual_duration = video.duration

    # Calculate start time (middle of video)
    if actual_duration <= clip_duration:
        # If video is shorter than clip_duration, use entire video
        start_time = 0
        end_time = actual_duration
        logger.info(f"Video is {actual_duration}s, using entire duration")
    else:
        # Start from middle of video
        start_time = (actual_duration - clip_duration) / 2
        end_time = start_time + clip_duration
        logger.info(f"Extracting {clip_duration}s clip from {start_time}s to {end_time}s")

    # Create the clip
    clip = video.subclipped(start_time, end_time)

    # Save the trimmed clip
    output_dir = os.path.dirname(video_path)
    clip_path = os.path.join(output_dir, f"{video_id}_clip.mp4")

    clip.write_videofile(
        clip_path,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        logger=None  # Suppress moviepy's verbose output
    )

    # Close the video files
    clip.close()
    video.close()

    result = {
        'clip_path': clip_path,
        'video_id': video_id,
        'clip_duration': end_time - start_time,
        'start_time': start_time,
        'end_time': end_time
    }

    logger.info(f"Clip saved to: {clip_path}")

    # Push to XCom for next tasks
    ti.xcom_push(key='clip_metadata', value=result)

    return result
