# Industrial Vision Quality Control System (CV-System)

Automated industrial inspection system designed for verifying parts and screw presence on production lines. Built for distributed Raspberry Pi architecture and integration with Siemens S7 PLCs.

---

## 1. System Architecture

The system operates on a Master/Slave topology to distribute processing and image acquisition.

### 1.1 Components
*   **Master Unit (Raspberry Pi):** Central controller managing the HUI (Tkinter), image processing (OpenCV), SQLite database, and PLC industrial communication (S7 Protocol).
*   **Slave Units (Raspberry Pi):** Distributed camera nodes responsible for low-latency image capture.
*   **PLC (Siemens S7-1200/1500):** Production line controller providing vehicle presence signals and receiving inspection results.

### 1.2 Communication Protocol Stack
| Connection | Protocol | Port | Function |
| :--- | :--- | :--- | :--- |
| Master ↔ Slave | SSH / SFTP | 22 | Remote command execution / Image transfer |
| Master ↔ PLC | S7 Protocol | 102 | DataBlock (DB) read/write |
| Master ↔ Internal | Socket | 9000 | Keep-alive camera trigger |

---

## 2. Hardware Requirements

### 2.1 Computing Units
*   **Master:** Raspberry Pi 4 Model B (4GB+ RAM recommended).
*   **Slaves:** Raspberry Pi 4 or CM4.
*   **Storage:** Industrial-grade SD cards or SSD for Master (High TBW).

### 2.2 Vision Hardware
*   **Sensors:** Raspberry Pi Camera Module 3 or HQ Camera.
*   **Optics:** Fixed focal length lens (C-Mount/M12) calibrated for the specific inspection area.
*   **Illumination:** 24V Industrial LED bars (strobe or continuous) triggered via PLC or local relay.

---

## 3. Installation & Software Setup

### 3.1 Master Unit Setup
Ensure Raspberry Pi OS 64-bit is installed.
```bash
# Update and install system dependencies
sudo apt-get update && sudo apt-get install -y libsnap7-dev libatlas-base-dev

# Install Python requirements
pip install opencv-python-headless numpy paramiko python-snap7 Pillow
```

### 3.2 Slave Unit Setup
Install the `rasp_distant` scripts in the home directory.
```bash
# Enable Legacy Camera Support or Libcamera depending on OS version
sudo raspi-config
```
The `rasp_camera_keepalive.py` daemon must be configured to start on boot via `systemd` or `crontab`.

---

## 4. Site Deployment & Configuration

To deploy the system in a new production area, modify `config.py`.

### 4.1 Deployment Workflow
1.  **Network Mapping:** Assign static IPs to all units in the industrial VLAN.
2.  **Hardware Definition:** Update the `RASPBERRY` list with the new IPs and associated camera IDs.
3.  **PLC Integration:** Define `AUTOMATE_IP` and verify the offsets in `AUTOMATE_DB_LECTURE` match the TIA Portal DataBlock structure.
4.  **Area Calibration:** 
    *   Boot the system in Admin Mode.
    *   Capture a reference image.
    *   Define Regions of Interest (ROI) using the interactive canvas.
    *   Save references using the "Prendre Réf" command.

### 4.2 Configuration Parameters (`config.py`)
| Parameter | Description |
| :--- | :--- |
| `DATABASE_PATH` | Path to the SQLite history file. |
| `SCORE_SEUIL` | Acceptance threshold (default 85.0). |
| `MARGE_RECHERCHE` | Pixel margin for template matching search. |
| `AUTOMATE_DB` | ID of the DataBlock for vehicle information. |

---

## 5. Industrial PLC Interface

The system interacts with two main DataBlocks:

### 5.1 Input DB (PLC → Master)
*   **Vehicle Presence:** Bit for triggering the capture.
*   **VIS / VIN:** String (32 chars) for vehicle identification.
*   **Cycle Code:** Integers defining the current vehicle model and variant.

### 5.2 Output DB (Master → PLC)
*   **Result OK:** Boolean.
*   **Result NOK:** Boolean.
*   **Error System:** Boolean (Watchdog).
*   **Defect List:** Array of Strings identifying the failed zones.

---

## 6. Maintenance & Reliability

### 6.1 Checklists
*   **Weekly:** 
    *   Clean camera protective windows with microfiber.
    *   Verify structural rigidity of mounting brackets.
*   **Monthly:**
    *   Monitor `historique_production.db` size.
    *   Verify industrial lighting consistency.
    *   Check Master Unit temperature and CPU load.

### 6.2 Troubleshooting (Factual)
| Error Code | Detection | Remediation |
| :--- | :--- | :--- |
| **SSH_FAIL** | Log: "Echec de la connexion" | Check VLAN connectivity / Update SSH Host Keys. |
| **S7_COMM_ERR** | Log: "Automate hors ligne" | Verify IP, Rack, and Slot settings in `config.py`. |
| **LOW_SCORE** | Repeated NOK on valid parts | Recalibrate ROI or clean optics. |
| **STORAGE_FULL** | Red Header in UI | Purge `/HDD_PATH/` archives. |

---

## 7. Data Structure

### 7.1 Database Schema
*   `inspections`: Centralizes vehicle metadata (VIS, timestamp, model).
*   `zone_results`: Detailed scores for every ROI (linked via `inspection_id`).

### 7.2 Storage Convention
Images are archived using the following naming convention:
`[CAM_ID]_[MODEL]_[ENGINE]_[VARIANT]_[VIS]_[BINARY_RESULTS].jpg`
Example: `1_P51_ICE_DEF_VF12345_110.jpg`

---
**Technical Lead:** James DAY  
**Version:** 1.2.0 (June 2026)  
**License:** Industrial Proprietary
