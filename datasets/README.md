---
license: mit
language:
- en
tags:
- scrape
---
# Scrape Content Dataset v1

A human-curated benchmark dataset for evaluating web scraping engines on content quality.

## Overview

This dataset contains 1,000 web pages with human-annotated ground truth for evaluating how well web scraping engines capture core content while avoiding noise (navigation, ads, footers, etc.). The dataset was created in 2025-10-21 and may become outdated over time.

## Dataset Structure

CSV format with columns:
- `id`: Sequential identifier
- `url`: Full URL of the web page  
- `truth_text`: ~100-word core snippet (main content)
- `lie_text`: ~10-word non-core snippet (navigation/footer/ads)
- `error`: Optional error message if page retrieval failed

## Limitations

**Created**: 2025-10-21

This dataset contains real-world web pages that may become outdated over time. Known issues include:

- URLs may become unavailable
- Content may be updated or removed
- Some pages may require JavaScript to load properly

For reproducible research, consider using this as a snapshot benchmark for the time period.

## Contributing

We welcome contributions to improve this dataset:

- **Bug Reports**: Report issues with specific entries
- **Updated Annotations**: Improve ground truth for existing pages
- **New Content**: Suggest additional web pages for evaluation
- **Dataset Maintenance**: Help keep URLs and content current

## License

MIT License - This dataset is provided for research and benchmarking purposes. Please respect website terms of service and use appropriate rate limiting.