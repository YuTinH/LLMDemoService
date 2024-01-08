# A Simple LLM DEMO Service for Deployment

## Installation

```bash
./install.sh
```

## Start DEMO

### Quick Startup
```bash
./run.sh
```

### Development Mode

#### Backend: LLM & embedding Layer
```bash
./run.sh model stop (Optional)
./run.sh model dev
```

#### Backend: View Layer
```bash
./run.sh view stop (Optional)
./run.sh view dev
```

#### Frontend
```bash
./run.sh frontend dev
```

## Configuration

[Revise]configs/global.yml

### LLM service
- Default port: 10080

### MongoDB
- Revise `/etc/mongodb.conf`,and startup mongodb service by `systemctl`|`service`
- **（Mandatory）** Fill the `host`&`port` in `mongo` section of `configs/global.yml`

## Maintance

### Restart Service

**Backend: LLM & embedding Layer**
```bash
./run.sh model restart
```

**Backend: View Layer**
```bash
./run.sh view restart
```

### Processing Feedback

**Export**
```bash
python -m scripts.history_data_process --operation export --output_dir $EXPORT_DIR --output_name $EXPORT_NAME --split_size $SPLIT_SIZE
```

- EXPORT_DIR: The output dir of export feedback data
- EXPORT_NAME: The output filename（filename suffix `.jsonl`）
- SPLIT_SIZE: Data number of a single export file，default 0
    - 0: Export into a file `{EXPORT_NAME}.jsonl`
    - \>0: Export into chunk files named `{EXPORT_NAME}_{idx}.jsonl`, each chunk file contains $SPLIT_SIZE data

**Clear**
```bash
python -m scripts.history_data_process --operation delete
```
