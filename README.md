# 💧 DeFi Concentrated Liquidity Monitor & Alert System

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)
![Firebase](https://img.shields.io/badge/Database-Firebase-FFCA28?logo=firebase&logoColor=white)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)

## 📌 Overview
Providing concentrated liquidity on Decentralized Exchanges (DEXs) like Aerodrome requires constant monitoring to mitigate **Impermanent Loss (IL)**. When the asset price exits the user-defined range, the position stops earning fees and is fully exposed to negative market action.

This project is an automated, end-to-end monitoring pipeline that tracks on-chain pool data, computes real-time impermanent loss, and alerts the user via Telegram when critical thresholds are breached. 

## 🏗 System Architecture
The system is designed with a decoupled architecture, separating the backend automation from the frontend visualization and data storage.

| Component | Technology | Function |
| :--- | :--- | :--- |
| **Data Fetching** | `requests` / `web3` | Reads live price data and pool metrics from the blockchain. |
| **Logic & Math** | `pandas` / Core Python | Computes IL, asset ratios, and earned fees based on entry parameters. |
| **Database** | Firebase (REST API) | Stores user position data, limits, and alarm states (anti-spam logic). |
| **Automation** | GitHub Actions | Cron job scheduler executing the control script autonomously. |
| **Notifications** | Telegram API | Delivers real-time pushed alerts directly to the user's mobile device. |
| **Dashboard** | Streamlit | Web interface for interacting with the database and adjusting pool ranges. |

## 🚀 Key Features
- **Real-Time IL Calculation:** Uses standard concentrated liquidity AMM mathematical models to determine actual net balance.
- **Anti-Spam State Machine:** Implements a state-tracking flag in Firebase to ensure the user receives exactly one alert when exiting a range, and resets only upon re-entry.
- **Zero-Cost CI/CD Pipeline:** Fully deployed using GitHub Actions for scheduled continuous execution without external server costs.
- **Interactive UI:** Streamlit dashboard allows for seamless updates of capital, entry price, and upper/lower bounds.

---

## ⚙️ Installation & Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/antonioder/defi-liquidity-sim.git
cd defi-liquidity-sim
```

### 2. Set up the virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (or export them in your terminal) with your Telegram credentials:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 5. Run the components

**Launch the Streamlit Dashboard:**
```bash
streamlit run app.py
```

**Test the Telegram Bot Trigger manually:**
```bash
python telegram_bot.py
```

---

## 🧮 Mathematical Model

The core logic calculates liquidity ($L$) and Impermanent Loss based on the entry price ($P_0$) and the upper/lower bounds ($P_a$, $P_b$).
The algorithm evaluates the current price ($P_c$) to determine the shift in the asset ratio (Token0 / Token1) and subtracts the accumulated fees (AERO emissions) to provide the actual **Net Balance** of the position.

---

> *Developed as a system integration and automation project to demonstrate backend Python proficiency and cloud-based architecture.*
