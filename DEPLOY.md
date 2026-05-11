# Deploying Flervalgsgenerator to VoxCuriosa.no

Since your server (`voxcuriosa.no`) is a shared cPanel host, you have two main options for deployment.

## Option 1: Hybrid Hosting (Recommended)

Keep the application running on **Streamlit Cloud** (or another Python host), but use your **Private Database** on `voxcuriosa.no`.

### Steps:

1.  **Configure Database (Server Side)**
    *   Log in to **cPanel**.
    *   Go to **Remote MySQL**.
    *   Add the IP address of your Streamlit Cloud instance (or add `%` for testing to allow all IPs, but remove it later for security).
    *   Ensure user `cpjvfkip_fler` is added to database `cpjvfkip_voxcuriosa` with ALL PRIVILEGES.

2.  **Configure Application (Streamlit Cloud)**
    *   Go to your Streamlit Cloud Dashboard.
    *   Open your App Settings -> **Secrets**.
    *   Paste the following configuration:

```toml
[mysql]
host = "voxcuriosa.no"
dbname = "cpjvfkip_voxcuriosa"
user = "cpjvfkip_fler"
password = "YOUR_PASSWORD_HERE"
port = 3306

[google]
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
redirect_uri = "https://your-app-url.streamlit.app"

[microsoft]
client_id = "YOUR_MICROSOFT_CLIENT_ID"
client_secret = "YOUR_MICROSOFT_CLIENT_SECRET"
tenant_id = "common"
redirect_uri = "https://your-app-url.streamlit.app"
```

## Option 2: VPS / Docker Hosting (Advanced)

If you upgrade `voxcuriosa.no` to a VPS or use a DigitalOcean Droplet:

1.  **Install Docker & Docker Compose** on the server.
2.  **Upload Files**: Upload the entire project folder to the server.
3.  **Create .env File**: Create a file named `.env` in the folder:

```bash
# Database
MYSQL_HOST=voxcuriosa.no
MYSQL_DB=cpjvfkip_voxcuriosa
MYSQL_USER=cpjvfkip_fler
MYSQL_PASSWORD=YOUR_PASSWORD_HERE

# OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://voxcuriosa.no/flervalg

MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_REDIRECT_URI=https://voxcuriosa.no/flervalg
```

4.  **Run**:
    ```bash
    docker-compose up -d --build
    ```
5.  **Reverse Proxy**: Configure Nginx/Apache to proxy `https://voxcuriosa.no/flervalg` to `http://localhost:8501`.

## Important Config Changes
*   **Redirect URIs**: You MUST update your Google Cloud Console and Microsoft Entra ID (Azure) to add the new Redirect URIs (e.g., `https://voxcuriosa.no/flervalg` or your Streamlit Cloud URL).
