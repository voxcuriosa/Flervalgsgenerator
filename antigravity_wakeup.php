<?php
// Antigravity Wakeup Script
// This script visits the Streamlit app URL to keep it alive or wake it up.
// Set this as a Cron Job in cPanel (e.g., once per day or every 12 hours).

$streamlit_url = "https://flervalg.streamlit.app"; // REPLACE THIS with your actual Streamlit URL!

echo "Waking up Antigravity at $streamlit_url ...<br>";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $streamlit_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true); // Follow redirects
curl_setopt($ch, CURLOPT_TIMEOUT, 30); // Wait max 30 seconds

// Fake a browser user agent (just in case)
curl_setopt($ch, CURLOPT_USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Antigravity-Wakeup-Bot/1.0");

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

if (curl_errno($ch)) {
    echo "Error: " . curl_error($ch);
} else {
    echo "Success! HTTP Status Code: $http_code<br>";
    echo "App successfully pinged.";
}

curl_close($ch);
?>
