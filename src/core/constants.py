"""
EBU/SMPTE Constants and Color Codes
"""

# DBFS Color Zones (EBU/SMPTE Standard)
DBFS_COLORS = {
    "danger":   {"range": (-6, 0),   "color": "#ff0000", "name": "Danger"},
    "warning":  {"range": (-9, -6),  "color": "#ff6600", "name": "Warning"},
    "caution":  {"range": (-18, -9), "color": "#cccc00", "name": "Caution"},
    "safe":     {"range": (-60, -18),"color": "#00cc00", "name": "Safe"},
    "quiet":    {"range": (-70, -60),"color": "#0066ff", "name": "Quiet"},
    "silence":  {"range": (-999, -70),"color": "#444444", "name": "Silence"},
}

# LUFS Color Zones (EBU R128)
LUFS_COLORS = {
    "danger": {"range": (-14, 999), "color": "#ff0000"},
    "target": {"range": (-24, -22), "color": "#00cc00"},
    "safe":   {"range": (-30, -24), "color": "#cccc00"},
    "quiet":  {"range": (-40, -30), "color": "#0066ff"},
    "silence": {"range": (-999, -70), "color": "#444444"},
}

# DBFS Scale Configuration
DBFS_SCALE = {
    "top": 0,
    "bottom": -70,
    "step_coarse": 5,   # -60 to -40
    "step_fine": 2,     # -40 to 0
    "coarse_range": (-60, -40),
    "fine_range": (-40, 0),
}

# Alignment Levels
ALIGNMENT_LEVEL_EBU = -18   # dBFS
ALIGNMENT_LEVEL_SMPTE = -20 # dBFS
LUFS_TARGET = -23           # LUFS
LUFS_TOLERANCE = 1          # LU

# SRT Defaults
SRT_DEFAULT_LATENCY = 120      # ms
SRT_DEFAULT_MSS = 1500       # bytes
SRT_DEFAULT_RCVBUF = 8192    # packets
SRT_DEFAULT_SNDBUF = 8192    # packets

# Update Rates
METER_UPDATE_RATE = 50       # fps (20ms)
CHART_UPDATE_RATE = 1        # sec
SPECTRUM_UPDATE_RATE = 50    # fps
SRT_STATS_INTERVAL = 1       # sec

# Time Windows (seconds)
TIME_WINDOWS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "60m": 3600,
}

# FFT Configuration
FFT_SIZE = 1024
FFT_WINDOW = "hann"
FFT_OVERLAP = 0.5
FFT_BANDS = 64
