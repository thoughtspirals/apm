# MHT CET College Finder

This solution provides a complete system for parsing the MHT CET cutoff data PDF and creating an interactive Streamlit application to query and visualize the results.

## Components

1. **PDF Parser** (`mht_cet_parser.py`): Extracts structured data from the 2022ENGG_CAP3_CutOff.pdf file
2. **Streamlit Application** (`streamlit_app.py`): Provides an interactive interface for querying and visualizing the parsed data

## How to Use

### Step 1: Parse the PDF

Run the parser script to extract data from the PDF and save it in both JSON and CSV formats:

```bash
python mht_cet_parser.py
```

This will process the 1000+ page PDF and create:
- `mht_cet_cutoffs.json` - Structured JSON format
- `mht_cet_cutoffs.csv` - Flattened CSV format
- `mht_cet_parser.log` - Log file with parsing information

### Step 2: Run the Streamlit App

Once the data is parsed, run the Streamlit application:

```bash
streamlit run streamlit_app.py
```

This will launch a web interface where you can:

- Filter colleges by various parameters:
  - Category (GOPENS, GOBCS, etc.)
  - Courses
  - College status
  - Seat type
  - Rank range
- View the top colleges matching your criteria
- Explore multiple visualizations:
  - College Comparison - Compare top colleges by rank
  - Rank vs Percentage - Analyze correlation between ranks and percentages
  - Course Comparison - Compare different courses at the same college
  - Multi-Category Analysis - Compare colleges across different categories

## Features

### Parser Features
- Robust error handling and logging
- Progress tracking for long-running operations
- Extraction of detailed information:
  - College code and name
  - Course code and name
  - College status and university
  - Seat type (Home University/Other University/State Level)
  - Cutoff data with ranks and percentages for each category
- Outputs both JSON (hierarchical) and CSV (flat) formats

### Streamlit App Features
- Data caching for performance
- Comprehensive filtering options
- Responsive visualizations using Plotly
- Multiple analysis views:
  - Tabular data for direct comparison
  - Bar charts for rank comparison
  - Scatter plots for rank vs percentage analysis
  - Heatmaps for multi-category analysis
  - Grouped bar charts for detailed comparisons

## Requirements

- Python 3.x
- Required packages:
  - PyPDF2
  - pandas
  - streamlit
  - plotly
  - tqdm
  - regex
