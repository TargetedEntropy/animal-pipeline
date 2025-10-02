"""
Animal Video Processing Pipeline DAG

This DAG orchestrates the process of:
1. Finding and downloading Creative Commons YouTube videos
2. Trimming 30-second segments
3. Detecting animals in the video
4. Extracting representative still images
5. Creating short GIFs where animals are most visible
6. Storing the outputs
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add tasks directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tasks'))

from download_video import download_video
from trim_clip import trim_clip
from detect_animals import detect_animals
from extract_images import extract_images
from create_gif import create_gif
from store_results import store_results

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'animal_pipeline',
    default_args=default_args,
    description='Process YouTube videos to detect and extract animal footage',
    schedule_interval=None,  # Manual trigger only (can be changed to '@daily' for daily runs)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['video', 'animals', 'yolo', 'ml'],
)

# Task 1: Download video
download_task = PythonOperator(
    task_id='download_video',
    python_callable=download_video,
    op_kwargs={
        'search_query': '{{ dag_run.conf.get("search_query", "dog") }}',
        'output_dir': '/opt/airflow/results'
    },
    dag=dag,
)

# Task 2: Trim clip
trim_task = PythonOperator(
    task_id='trim_clip',
    python_callable=trim_clip,
    op_kwargs={
        'clip_duration': 30
    },
    dag=dag,
)

# Task 3: Detect animals
detect_task = PythonOperator(
    task_id='detect_animals',
    python_callable=detect_animals,
    op_kwargs={
        'confidence_threshold': 0.5
    },
    dag=dag,
)

# Task 4: Extract images
extract_task = PythonOperator(
    task_id='extract_images',
    python_callable=extract_images,
    op_kwargs={
        'num_images': 3
    },
    dag=dag,
)

# Task 5: Create GIF
gif_task = PythonOperator(
    task_id='create_gif',
    python_callable=create_gif,
    op_kwargs={
        'gif_duration': 5
    },
    dag=dag,
)

# Task 6: Store results
store_task = PythonOperator(
    task_id='store_results',
    python_callable=store_results,
    dag=dag,
)

# Define task dependencies
download_task >> trim_task >> detect_task >> extract_task >> gif_task >> store_task
