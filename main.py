import pandas as pd
import requests
from datetime import datetime

# Telegram Bot credentials (replace with your own)
TELEGRAM_BOT_TOKEN = 'your bot token '
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Path to your Excel file
import os
EXCEL_FILE_PATH = os.path.join(os.getcwd(), 'daily_energy_data.xlsx')


# Load the Excel file
df = pd.read_excel(EXCEL_FILE_PATH)

# Function to retrieve new Chat IDs with offset
def get_new_chat_ids():
    new_chat_ids = []
    offset = None  # Start from the most recent messages

    while True:
        params = {"offset": offset, "timeout": 5}
        response = requests.get(f"{TELEGRAM_API_URL}/getUpdates", params=params)
        updates = response.json()

        if not updates.get("ok") or not updates.get("result"):
            break  # No more updates, stop fetching

        for update in updates["result"]:
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                if chat_id not in new_chat_ids:
                    new_chat_ids.append(chat_id)

            offset = update["update_id"] + 1  # Move to the next message

    return new_chat_ids

# Function to update Chat IDs in Excel
def update_chat_ids_and_save(new_chat_ids):
    updated = False
    existing_chat_ids = df["Chat ID"].dropna().tolist()

    for chat_id in new_chat_ids:
        if chat_id not in existing_chat_ids:  # Only assign if it's a new chat ID
            empty_rows = df[df["Chat ID"].isna()]
            if not empty_rows.empty:
                first_empty_index = empty_rows.index[0]
                df.at[first_empty_index, "Chat ID"] = chat_id
                updated = True
                print(f"Assigned Chat ID {chat_id} to Customer {df.at[first_empty_index, 'Customer ID']}")

    if updated:
        df.to_excel(EXCEL_FILE_PATH, index=False)  # Save back to the same file
        print("Chat IDs updated successfully!")

        # Make the file available for download in Colab
       # files.download(EXCEL_FILE_PATH)
    else:
        print("No new Chat IDs assigned.")

# Function to send Telegram messages
def send_telegram_message(chat_id, message):
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
    if response.status_code == 200:
        print(f"Message sent to chat ID {chat_id}")
    else:
        print(f"Failed to send message to chat ID {chat_id}: {response.text}")

# Main function to automate everything
def automate_notifications():
    # Step 1: Retrieve new Chat IDs
    new_chat_ids = get_new_chat_ids()
    print("New Chat IDs retrieved:", new_chat_ids)

    # Step 2: Update Chat IDs and save to the same Excel file
    if new_chat_ids:
        update_chat_ids_and_save(new_chat_ids)

    # Step 3: Send daily notifications to all customers with Chat IDs
    today = datetime.today().strftime('%Y-%m-%d')
    today_data = df[df['Date'] == today]

    for index, row in today_data.iterrows():
        customer_id = row['Customer ID']
        consumption = row['Daily Energy Consumption (kWh)']
        bill = row['Daily Bill']
        chat_id = row['Chat ID']

        if pd.notna(chat_id):  # Check if Chat ID is available
            message = (
                f"Hello Customer {customer_id},\n"
                f"Your daily energy consumption for {today} is {consumption} kWh.\n"
                f"Your daily bill is ₹{bill:.2f}.\n"
                "Thank you for using our services!"
            )
            send_telegram_message(chat_id, message)
        else:
            print(f"No Chat ID found for Customer {customer_id}. Skipping notification.")

# Run the automation
if __name__ == "__main__":
    automate_notifications()

