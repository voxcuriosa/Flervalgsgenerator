---
description: How to add a new NDLA subject to the application
---

# Add New NDLA Subject

This workflow describes how to add a new NDLA subject to the application.

## Prerequisites
- You need the name of the subject.
- You need the URL to the subject page on NDLA.

## Steps

1.  **Find the Node ID**
    - Use `curl` or a browser to inspect the subject page and find the `urn:subject` or `urn:topic` ID.
    - Example: `curl -s "https://ndla.no/subject/..." | grep "urn:subject"`
    - Note: Ensure you have the root Subject ID (usually starts with `urn:subject`), not just a topic ID.

2.  **Update `scrape_ndla.py`**
    - Add the new subject name and ID to the `SUBJECTS` dictionary in `scrape_ndla.py`.
    - Example:
      ```python
      SUBJECTS = {
          ...,
          "New Subject Name": "urn:subject:..."
      }
      ```

3.  **Run Scraping**
    - Run the scraping script with the subject name and ID.
    - This will automatically update the database and regenerate the HTML viewer.
    ```bash
    python3 scrape_ndla.py "New Subject Name" "urn:subject:..."
    ```

4.  **Verify**
    - Check if the subject appears in the application (NDLA Fagstoff).
    - Check if `ndla_content_viewer.html` contains the new subject.
