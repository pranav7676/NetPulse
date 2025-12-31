# NetPulse – Network Dashboard

A real-time network monitoring dashboard built with Streamlit and Scapy.

## Features

- Real-time network packet capture and analysis
- Network traffic visualization with Plotly
- System resource monitoring (CPU, Memory, Network usage)
- Interactive dashboard interface

## Requirements

- Python 3.7+
- Administrator/root privileges (required for packet capture)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/YOUR_USERNAME/net_monitor.git
cd net_monitor
```

2. Install the required packages:

```bash
pip install streamlit pandas plotly psutil scapy
```

## Usage

Run the application with administrator/root privileges:

```bash
# Windows (Run as Administrator)
streamlit run net_monitor.py

# Linux/Mac
sudo streamlit run net_monitor.py
```

## Note

This application requires elevated privileges to capture network packets. Make sure to run it as administrator on Windows or with sudo on Linux/Mac.

## License

MIT License
