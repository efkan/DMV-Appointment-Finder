# DMV Appointment Finder - Easy User Guide

This guide will help you set up and run the DMV Appointment Finder.

---

## 1. Installation (Do This First)

Before you start, you need to install the necessary software.

1. **Install Python**: Make sure you have Python installed on your computer.
   - [Download Python Here](https://www.python.org/downloads/)
2. **Install Google Chrome**: This app uses the Chrome browser to work.
   - [Download Chrome Here](https://www.google.com/chrome/)
3. **Install Requirements**:
   - Open your terminal or command prompt.
   - Go to the project folder.
   - Type this command and press Enter:
     ```bash
     pip install -r requirements.txt
     ```
     _(If that doesn't work, try `pip3 install -r requirements.txt`)_

---

## 2. Setup Your Information

Open the file `Management/parameters.md` and fill in your details:

- **Zip Codes**: A list of zip codes where you want to search for appointments. Separate multiple zip codes with a comma.
  - Returns best results with 3-5 zip codes.
  - _Example_: `94568, 95304, 94401`
- **Driver's License or Permit Number**: Your DMV ID number.
  - _Example_: `U1234567`
- **Date of Birth**: Your birthday in MM/DD/YYYY format.
  - _Example_: `04/28/1982`

---

## 3. Get Phone Notifications (Ntfy.sh)

To receive alerts on your phone when an earlier appointment is found:

1. **Download the App**: Install the **Ntfy.sh** app on your iPhone or Android.
2. **Find Your Topic Name**:
   - Open the file `dmv_finder/config.py`.
   - Look for the line that says `NTFY_TOPIC = "..."`.
   - _Example_: `pinars_dmv_appointments`
3. **Subscribe in the App**:
   - Open the Ntfy app.
   - Click the **+** (plus) button to subscribe to a new topic.
   - Type the **exact** topic name found in step 2 (e.g., `pinars_dmv_appointments`).
   - Click **Subscribe**.

You will now get a notification whenever the bot finds a better date!

---

## 4. Run the App

1. Open your terminal or command prompt.
2. Go to the project folder.
3. Type the following command and press Enter:

```bash
python3 main.py
```

### What Happens Next?

- The app will open a browser and log in for you.
- It will check appointments for each zip code.
- If it finds an earlier date, it will **send you a notification**.
- After checking all zip codes, it will **wait for 10 minutes** and then start again automatically.
- It will keep running until you stop it.

### Running in Background (Headless Mode)

By default, the app runs in **Headless Mode** (no visible browser) to run quietly in the background.

If you want to **see the browser** (to debug or watch it working):

1. Open `dmv_finder/config.py`.
2. Change the line `HEADLESS_MODE = True` to `HEADLESS_MODE = False`.
3. Save and run the app again.

### How to Stop

To stop the app, click in the terminal window and press `Ctrl+C` on your keyboard.
