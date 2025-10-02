"""Download Creative Commons YouTube videos using yt-dlp."""
import os
import logging
from typing import Dict
import yt_dlp

logger = logging.getLogger(__name__)


def download_video(search_query: str, output_dir: str = "/opt/airflow/results", **context) -> Dict[str, str]:
    """
    Download a Creative Commons YouTube video based on search query.

    Args:
        search_query: Search term (e.g., "dog", "cat", "elephant")
        output_dir: Directory to save the downloaded video

    Returns:
        Dictionary with video_path and video_id
    """
    os.makedirs(output_dir, exist_ok=True)

    video_id = context['dag_run'].run_id
    output_path = os.path.join(output_dir, f"{video_id}_original.mp4")

    # Configure yt-dlp to search for Creative Commons videos
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        # Search for Creative Commons licensed videos
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'age_limit': None,
    }

    search_string = f"{search_query} creative commons"

    logger.info(f"Searching for: {search_string}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search and download
            info = ydl.extract_info(search_string, download=True)

            # Get video metadata
            if 'entries' in info:
                video_info = info['entries'][0]
            else:
                video_info = info

            logger.info(f"Downloaded: {video_info.get('title', 'Unknown title')}")
            logger.info(f"Duration: {video_info.get('duration', 'Unknown')} seconds")

            result = {
                'video_path': output_path,
                'video_id': video_id,
                'title': video_info.get('title', 'Unknown'),
                'duration': video_info.get('duration', 0)
            }

            # Push to XCom for next tasks
            context['task_instance'].xcom_push(key='video_metadata', value=result)

            return result

    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise
