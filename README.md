# ElderCare Companion 🏥

ElderCare Companion is a comprehensive, professional-grade healthcare management application designed for elderly users and their caretakers. Built with **Streamlit** and **SQLite**, it provides a seamless interface for tracking medications, vitals, appointments, and symptoms.

## ✨ Key Features

- **Personalized Dashboard**: Real-time greeting, daily medication summary, and latest vital stats.
- **Medication Manager**: Log daily doses, track compliance, and manage prescriptions.
- **Vital Signs Logger**: Monitor Blood Pressure, Heart Rate, Sugar levels, and BMI with visual gauges.
- **Health Reporting**: Generate detailed **PDF reports** (ReportLab) and visual analytics (Seaborn/Matplotlib).
- **Symptom Journal**: Track daily health status with a persistent symptom diary.
- **Appointment Tracker**: Never miss a doctor's visit with scheduled reminders.
- **Emergency Contacts**: One-click access to critical contact information.
- **Visual Motivation**: Interactive Turtle Graphics for tracking weekly and monthly progress.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/eldercare-companion.git
   cd eldercare-companion
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run main.py
   ```

## 🛠️ Technology Stack
- **Frontend/App Framework**: Streamlit
- **Database**: SQLite3
- **Visualization**: Matplotlib, Seaborn, Turtle
- **Reporting**: ReportLab (PDF Generation)
- **Data Analysis**: Pandas, NumPy

## 🔒 Security & Privacy
The app uses a **Secure PIN Authentication** system for caretakers and isolates user data within a local SQLite database, ensuring health records remain private and local to your device.

## 📄 License
This project is for educational purposes. Feel free to use and modify it for your own personal or academic needs.
