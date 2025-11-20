# Troubleshooting Guide

This guide helps you resolve common issues when setting up and running the scrapers benchmark.

## Common Issues

### Missing Dependencies Error
**Error**: `ModuleNotFoundError: No module named 'typer'` (or other missing modules)

**Solution**: 
1. Ensure you're in the correct virtual environment:
   ```bash
   # If using venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate      # Windows
   ```

2. Install requirements in the correct environment:
   ```bash
   pip install -r requirements.txt
   ```

3. If using a virtual environment, make sure it's activated before running commands:
   ```bash
   # Check if you're in a virtual environment
   which python  # Should show path to your venv
   pip list      # Should show installed packages
   ```

### Selenium WebDriver Issues
**Error**: `WebDriverException: 'chromedriver' executable needs to be in PATH`

**Solution**:
```bash
# Install ChromeDriver
# On macOS with Homebrew:
brew install chromedriver

# On Ubuntu/Debian:
sudo apt-get install chromium-chromedriver

# Or download manually from: https://chromedriver.chromium.org/
```

### Playwright Browser Issues
**Error**: `Browser not found` or `Target page, context or browser has been closed`

**Solution**:
```bash
# Install Playwright browsers
python -m playwright install chromium
python -m playwright install firefox  # if using Firefox
python -m playwright install webkit    # if using WebKit
```

### Permission Errors
**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
1. Check file/directory permissions:
   ```bash
   ls -la runs/  # Check if directory is writable
   ```

2. Run with appropriate permissions:
   ```bash
   # On Linux/Mac, you might need:
   chmod +x run_eval.py
   ```

### Memory Issues
**Error**: `MemoryError` or process killed due to memory usage

**Solution**:
1. Reduce concurrency:
   ```bash
   python run_eval.py --max-workers 2  # Reduce from default 10
   ```

2. Use dry-run for testing:
   ```bash
   python run_eval.py --dry-run  # Test with limited data
   ```

### Network/API Issues
**Error**: `ConnectionError`, `TimeoutError`, or API rate limits

**Solution**:
1. Check internet connection
2. Verify API keys are set correctly:
   ```bash
   echo $FIRECRAWL_API_KEY  # Example for Firecrawl
   echo $SCRAPINGBEE_API_KEY  # Example for ScrapingBee
   ```

3. Increase timeout values in engine configurations

### Dataset Issues
**Error**: `FileNotFoundError: datasets/1-0-0.csv`

**Solution**:
1. Ensure dataset file exists:
   ```bash
   ls -la datasets/
   ```

2. Use absolute path if needed:
   ```bash
   python run_eval.py --dataset /full/path/to/datasets/1-0-0.csv
   ```

## Environment Setup

### Using Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run evaluation
python run_eval.py --help
```

### Using Conda
```bash
# Create conda environment
conda create -n scrapers-benchmark python=3.9

# Activate it
conda activate scrapers-benchmark

# Install dependencies
pip install -r requirements.txt
```

## Dry Run Testing

Use the `--dry-run` option to test your setup without processing the full dataset:

```bash
# Test single engine with dry run
python run_eval.py \
  --scrape_engine selenium_scraper \
  --suite quality \
  --output-dir runs \
  --dataset datasets/1-0-0.csv \
  --dry-run

# Test all engines with dry run
python run_all.py run-all \
  --dataset datasets/1-0-0.csv \
  --dry-run
```

The dry-run option:
- Uses a temporary directory (automatically cleaned up)
- Limits to first 5 tasks for quick testing
- Verifies all engines can run without errors
- Perfect for testing environment setup

## Getting Help

If you encounter issues not covered here:

1. Check the logs for specific error messages
2. Try running with `--dry-run` first to isolate issues
3. Verify your environment setup with `pip list`
4. Check that all required system dependencies are installed (ChromeDriver, etc.)
