import os
from dotenv import load_dotenv

# Always load .env from the same directory as this file, regardless of cwd
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(_ENV_PATH, override=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'telelearn-ai-secret-key-2024-change-in-production')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    GROQ_MODEL = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-20b')
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'database.db')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    MAX_RETRIEVAL_CHUNKS = 4
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

TELECOM_TOPICS = {
    "Wireless Communication": {
        "icon": "📡",
        "subtopics": ["Radio Waves", "Frequency Bands", "Propagation", "Fading", "Diversity Techniques"],
        "color": "blue"
    },
    "4G LTE": {
        "icon": "📶",
        "subtopics": ["LTE Architecture", "OFDMA", "MIMO in LTE", "EPC", "Handover"],
        "color": "green"
    },
    "5G": {
        "icon": "🚀",
        "subtopics": ["5G NR", "mmWave", "Massive MIMO", "Network Slicing", "Edge Computing"],
        "color": "purple"
    },
    "6G Basics": {
        "icon": "🌐",
        "subtopics": ["Terahertz Bands", "AI-Native Networks", "Holographic Communication", "6G Vision"],
        "color": "cyan"
    },
    "GSM": {
        "icon": "📱",
        "subtopics": ["GSM Architecture", "TDMA", "Channel Types", "Authentication", "Handoff"],
        "color": "orange"
    },
    "CDMA": {
        "icon": "🔗",
        "subtopics": ["Spread Spectrum", "Walsh Codes", "Power Control", "Soft Handoff", "CDMA2000"],
        "color": "red"
    },
    "OFDM": {
        "icon": "〰️",
        "subtopics": ["Orthogonal Subcarriers", "Cyclic Prefix", "FFT/IFFT", "Subcarrier Spacing", "OFDM vs SC-FDMA"],
        "color": "blue"
    },
    "MIMO": {
        "icon": "📻",
        "subtopics": ["Spatial Multiplexing", "Beamforming", "Space-Time Coding", "Capacity Gain", "Massive MIMO"],
        "color": "green"
    },
    "Modulation": {
        "icon": "〽️",
        "subtopics": ["AM/FM", "PSK", "QAM", "FSK", "BPSK/QPSK", "64-QAM"],
        "color": "purple"
    },
    "Antennas": {
        "icon": "🗼",
        "subtopics": ["Antenna Types", "Gain", "Directivity", "Radiation Pattern", "Array Antennas"],
        "color": "yellow"
    },
    "Signal Processing": {
        "icon": "📊",
        "subtopics": ["Fourier Transform", "Filtering", "Sampling", "Nyquist Theorem", "ADC/DAC"],
        "color": "teal"
    },
    "Computer Networks": {
        "icon": "💻",
        "subtopics": ["OSI Model", "Network Topologies", "LAN/WAN", "Network Devices", "Subnetting"],
        "color": "blue"
    },
    "TCP/IP": {
        "icon": "🌍",
        "subtopics": ["IP Addressing", "TCP vs UDP", "Three-Way Handshake", "Congestion Control", "IPv6"],
        "color": "green"
    },
    "Routing": {
        "icon": "🔀",
        "subtopics": ["Static Routing", "OSPF", "BGP", "RIP", "Routing Tables"],
        "color": "orange"
    },
    "Switching": {
        "icon": "🔄",
        "subtopics": ["Circuit Switching", "Packet Switching", "VLANs", "STP", "Layer 2 vs Layer 3"],
        "color": "red"
    },
    "Network Architecture": {
        "icon": "🏗️",
        "subtopics": ["Core Network", "Access Network", "Transport Network", "SDN", "NFV"],
        "color": "indigo"
    },
    "Protocols": {
        "icon": "📋",
        "subtopics": ["HTTP/HTTPS", "DNS", "DHCP", "SNMP", "FTP", "SSH"],
        "color": "cyan"
    },
    "IoT Communication": {
        "icon": "🔌",
        "subtopics": ["LoRaWAN", "Zigbee", "Bluetooth LE", "NB-IoT", "MQTT"],
        "color": "teal"
    },
    "Fiber Optics": {
        "icon": "💡",
        "subtopics": ["Optical Fiber Types", "Total Internal Reflection", "WDM", "DWDM", "Fiber Amplifiers"],
        "color": "yellow"
    },
    "Satellite Communication": {
        "icon": "🛸",
        "subtopics": ["Satellite Orbits", "Transponders", "Link Budget", "GEO vs LEO", "Starlink"],
        "color": "purple"
    }
}
