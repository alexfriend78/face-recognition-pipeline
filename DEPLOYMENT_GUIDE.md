# Deployment Guide: Face Recognition Pipeline

This guide provides instructions on how to set up and run the complete Face Recognition Pipeline application on your local machine.

## 1. Prerequisites

Before you begin, ensure you have the following software installed and running on your system.

### For both macOS and Windows:

*   **Docker Desktop**: The application runs entirely within Docker containers. Docker Desktop must be installed and **running** before you start the application.
    *   [Download Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
    *   [Download Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
    *   **Important**: After installation, start Docker Desktop and wait for it to show a "running" status.

*   **Git**: You will need Git to clone the project repository.
    *   [Download Git](httpss://git-scm.com/downloads)

### For Windows Users Only:

*   **Windows Subsystem for Linux (WSL 2)**: The startup scripts are written in Bash (`.sh`) and require a Linux environment to run. WSL 2 provides the best integration with Docker Desktop.
    *   Follow the [Official Microsoft Guide to Install WSL](https://docs.microsoft.com/en-us/windows/wsl/install).
    *   Make sure your Docker Desktop is configured to use the WSL 2 backend. You can check this in **Docker Desktop > Settings > General**.

---

## 2. Installation and Setup

### Step 1: Clone the Repository

Open your terminal (on macOS) or your **WSL 2 terminal** (on Windows) and run the following command to clone the project from GitHub:

```bash
git clone https://github.com/alexfriend78/face-recognition-pipeline.git
```

### Step 2: Navigate to the Project Directory

Once the repository is cloned, navigate into the project folder:

```bash
cd face-recognition-pipeline
```

---

## 3. Running the Application

The following commands should be run from the `face-recognition-pipeline` directory inside your terminal (or WSL 2 terminal).

### For macOS Users:

**a. Make the Startup Script Executable:**

First, you need to grant execute permissions to the startup script.

```bash
chmod +x start-monitoring.sh
```

**b. Run the Application:**

Now, start the entire application stack using the script. This will build the Docker images and launch all services.

```bash
./start-monitoring.sh
```

> **Note:** The first time you run this, it will download all the necessary Docker images and build the application containers. This process can take **15-30 minutes**, depending on your internet connection and computer speed. Subsequent startups will be much faster.

### For Windows Users (inside WSL 2):

The process is the same as for macOS, but you must perform these steps inside your WSL 2 terminal.

**a. Open the Project in WSL:**

If you cloned the repository on your Windows file system, you can access it from WSL at a path like `/mnt/c/Users/YourUser/path/to/face-recognition-pipeline`.

**b. Make the Startup Script Executable:**

```bash
chmod +x start-monitoring.sh
```

**c. Run the Application:**

```bash
./start-monitoring.sh
```

> **Windows Line Endings Note**: If you get an error like `bad interpreter: no such file or directory` or `command not found`, it might be due to Windows-style line endings. You can fix this by running: `dos2unix start-monitoring.sh` and then running the script again. (You may need to install dos2unix with `sudo apt-get install dos2unix`).

---

## 4. Accessing the Application

Once the startup script is complete, the application and all monitoring services will be running. You can access them at the following URLs in your web browser:

*   **Main Application**: [http://localhost](http://localhost)
*   **Grafana Dashboards**: [http://localhost:3000](http://localhost:3000)
    *   **Login**: `admin` / **Password**: `admin123`
*   **Kibana (Logs)**: [http://localhost:5601](http://localhost:5601)
*   **Prometheus (Metrics)**: [http://localhost:9090](http://localhost:9090)
*   **Celery Monitor (Flower)**: [http://localhost/flower](http://localhost/flower)

---

## 5. How to Use

1.  Open the main application at [http://localhost](http://localhost).
2.  Click the "Upload" button and select an image or video file containing faces.
3.  The file will be processed in the background. You can see the progress on the main page.
4.  Once completed, the detected faces will appear in the gallery.

---

## 6. Stopping the Application

To stop all running services and containers, run the `stop-monitoring.sh` script from the project directory:

```bash
./stop-monitoring.sh
```

This will safely shut down the entire application stack.

---

## 7. Troubleshooting

*   **Error: `Cannot connect to the Docker daemon`**
    *   **Solution**: Make sure Docker Desktop is running.

*   **Error: `Permission denied` when running `./start-monitoring.sh`**
    *   **Solution**: You forgot to make the script executable. Run `chmod +x start-monitoring.sh`.

*   **Services Fail to Start (e.g., `web` or `celery`)**
    *   **Solution**: The initial build may have failed. Try rebuilding the containers manually: `docker-compose build` and then run the startup script again.

*   **Port Conflicts**
    *   **Solution**: If you have other services running on ports like `80`, `5432`, `5601`, or `9090`, they will conflict. Stop the other services or reconfigure the ports in the `docker-compose.yml` files.


