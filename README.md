# Animal Video Processing Pipeline

An Apache Airflow pipeline that automatically discovers, downloads, and processes Creative Commons YouTube videos to detect animals, extract images, and create GIFs.

## Features

- 🎥 Downloads Creative Commons YouTube videos using yt-dlp
- ✂️ Trims 30-second segments from videos
- 🤖 Detects animals using YOLOv8 object detection
- 📸 Extracts representative frames with clearly visible animals
- 🎞️ Creates animated GIFs centered on animal detections
- 📁 Organizes results with metadata summaries

## Pipeline Flow

```
download_video → trim_clip → detect_animals → extract_images → create_gif → store_results
```

## Quick Start

### 1. Set up environment

```bash
# Create .env file
cp .env.example .env

# Note: AIRFLOW_UID is already set to 50000 in .env.example (default airflow user)
# No need to change it unless you have specific requirements
```

### 2. Start Airflow

```bash
docker compose up -d
```

This will:
- Start PostgreSQL database
- Initialize Airflow database
- Create admin user (username: `admin`, password: `admin`)
- Install Python dependencies from `requirements.txt`
- Start Airflow webserver on http://localhost:8080
- Start Airflow scheduler

### 3. Access Airflow UI

Open http://localhost:8080 in your browser and log in with:
- Username: `admin`
- Password: `admin`

### 4. Trigger the DAG

**Option 1: Via UI**
1. Navigate to the DAGs page
2. Find `animal_pipeline`
3. Click the play button to trigger
4. (Optional) Click "Trigger DAG w/ config" to specify a search query:
   ```json
   {"search_query": "cat"}
   ```

**Option 2: Via CLI**
```bash
# Trigger with default search query ("dog")
docker compose exec airflow-webserver airflow dags trigger animal_pipeline

# Trigger with custom search query
docker compose exec airflow-webserver airflow dags trigger animal_pipeline --conf '{"search_query": "elephant"}'
```

### 5. View Results

Results are organized in `results/` directory:
```
results/
└── {run_id}_{timestamp}/
    ├── images/
    │   ├── frame_1_dog_3.45s.jpg
    │   ├── frame_2_dog_5.12s.jpg
    │   └── frame_3_dog_8.76s.jpg
    ├── {run_id}_dog.gif
    └── summary.json
```

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f airflow-scheduler
docker compose logs -f airflow-webserver
```

### Check DAG Status

```bash
docker compose exec airflow-webserver airflow dags list
docker compose exec airflow-webserver airflow dags state animal_pipeline
```

### Test Individual Tasks

```bash
docker compose exec airflow-webserver airflow tasks test animal_pipeline download_video 2024-01-01
```

## Configuration

### Adjust Pipeline Parameters

Edit `dags/animal_pipeline_dag.py` to modify:
- `clip_duration`: Length of trimmed clip (default: 30 seconds)
- `confidence_threshold`: Minimum confidence for animal detection (default: 0.5)
- `num_images`: Number of frames to extract (default: 3)
- `gif_duration`: Length of GIF (default: 5 seconds)

### Schedule the DAG

By default, the DAG runs on manual trigger. To schedule it:

```python
# In dags/animal_pipeline_dag.py
schedule_interval='@daily',  # Run daily at midnight
```

## Stopping Airflow

```bash
# Stop services
docker compose down

# Stop and remove volumes (WARNING: deletes database)
docker compose down -v
```

## Troubleshooting

### Permission Issues

If you encounter permission errors:
```bash
mkdir -p logs plugins results
chmod -R 777 logs plugins results
```

### Dependencies Not Installing

If Python packages fail to install, rebuild the containers:
```bash
docker compose down
docker compose build
docker compose up -d
```

### YOLOv8 Model Download

The first run will download the YOLOv8 model (~6MB). This is normal and only happens once.

## Project Structure

```
animal-pipeline/
├── dags/                      # Airflow DAG definitions
│   └── animal_pipeline_dag.py
├── tasks/                     # Pipeline task implementations
│   ├── download_video.py
│   ├── trim_clip.py
│   ├── detect_animals.py
│   ├── extract_images.py
│   ├── create_gif.py
│   └── store_results.py
├── results/                   # Pipeline outputs
├── logs/                      # Airflow logs
├── plugins/                   # Airflow plugins (optional)
├── docker-compose.yml         # Docker services configuration
├── requirements.txt           # Python dependencies
└── README.md
```

## Detected Animals

The pipeline can detect these animals (COCO dataset classes):
- bird
- cat
- dog
- horse
- sheep
- cow
- elephant
- bear
- zebra
- giraffe

## License

This project processes Creative Commons licensed videos from YouTube.
