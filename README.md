# File Segmentation Processor

A Python application for processing files of unknown length, segmenting them into user-defined buckets, and storing the results in PostgreSQL. Built for deployment on Heroku.

## Features

- Process files of arbitrary length
- Custom segmentation based on user-defined parameters
- GUI interface for segment configuration
- PostgreSQL storage for segments
- Heroku deployment ready

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/file_segmentation.git
cd file_segmentation
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure PostgreSQL:
- Create a database
- Update database credentials in `src/config.py`

## Usage

1. Start the GUI:
```bash
python src/main.py
```

2. Through the GUI:
- Select input file
- Configure number of segments
- Define segmentation rules
- Process file
- View results

## Configuration

Update `src/config.py` with your settings:
- Database credentials
- File processing parameters
- Segmentation rules

## Development

### Project Structure
```
file_segmentation/
├── README.md
├── data/
│   ├── processed/    # Processed file outputs
│   └── raw/         # Raw input files
├── notebooks/       # Jupyter notebooks for analysis
├── requirements.txt # Project dependencies
├── setup.py        # Package setup
└── src/
    ├── config.py   # Configuration settings
    ├── database/   # Database operations
    ├── gui/        # User interface
    ├── main.py     # Application entry point
    ├── segmentation/ # Core segmentation logic
    ├── tests/      # Unit tests
    └── utils/      # Utility functions
```

### Testing

Run tests with:
```bash
python -m pytest src/tests/
```

## Deployment

### Heroku Deployment

1. Create Heroku app:
```bash
heroku create your-app-name
```

2. Add PostgreSQL addon:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

3. Configure environment variables:
```bash
heroku config:set PYTHON_VERSION=3.9.x
```

4. Deploy:
```bash
git push heroku main
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.