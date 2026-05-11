# Cron Job Setup Guide

To keep your Streamlit app from sleeping, we have created a script (`antigravity_wakeup.php`) on your server. Follow these steps to automate it.

## 1. Edit the Script
1.  Open `antigravity_wakeup.php` and changing the `$streamlit_url` to your actual app URL (e.g., `https://your-app.streamlit.app`).

## 2. Upload to Server
1.  Upload `antigravity_wakeup.php` to your `public_html` folder on `voxcuriosa.no`.

## 3. Set up Cron Job in cPanel
1.  Log in to **cPanel** on `voxcuriosa.no`.
2.  Search for **"Cron Jobs"**.
3.  Under **"Add New Cron Job"**:
    *   **Common Settings**: Choose "Once Per Day" (or "Twice Per Day" if it sleeps faster).
    *   **Command**:
        ```bash
        /usr/local/bin/php /home/cpjvfkip/public_html/antigravity_wakeup.php
        ```
        *(Note: The path `/home/cpjvfkip/public_html/` might vary slightly. You can usually see the correct "Home Directory" path on the right side of the main cPanel dashboard).*

4.  Click **"Add New Cron Job"**.

## Done!
Your server will now automatically visit your Streamlit app every day to check if it's awake, which usually prevents it from going into deep sleep or wakes it up before you need it.
