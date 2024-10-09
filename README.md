# Bittensor Chain Observer

This project is designed to observe and report on specific events and transactions occurring on the Bittensor blockchain network. It focuses on monitoring scheduled coldkey swaps, network dissolves, voting activities, and other critical network events.

## Features

- **Block Monitoring**: Observes current blocks for specific extrinsics and events.
- **Event Detection**: Identifies key events such as scheduled coldkey swaps, network dissolves, and voting activities.
- **Data Extraction**: Extracts relevant information from extrinsics and events.
- **Report Generation**: Creates detailed reports for each detected event.
- **Validator Information**: Retrieves and includes validator names and links in reports when available.
- **Database Integration**: Uses SQLite to store and retrieve validator and owner information.
- **Discord Notifications**: Sends event reports to specified Discord channels using webhooks.
- **Data Collection**: Fetches and stores owner and validator information from the TaoStats API.

## Key Components

1. **Substrate Interface**: Connects to the Bittensor network using the SubstrateInterface.
2. **Block Data Retrieval**: Fetches block data and associated events from the blockchain.
3. **Extrinsic Processing**: Analyzes extrinsics for specific function calls related to coldkey swaps, network dissolves, and voting.
4. **Event Processing**: Processes events to extract relevant information and confirm transaction success.
5. **Report Generation**: Creates formatted reports for each detected event, including relevant details and timestamps.
6. **Database Queries**: Retrieves validator and owner information from a local SQLite database.
7. **Discord Integration**: Sends reports to Discord channels using webhooks.
8. **Data Collection**: Fetches owner and validator data from TaoStats API and stores it in the SQLite database.

## Running bot

### Make sure dataset is prepared

For running bot correctly, you have to make sure the `db.sqlite3` file is prepared in DB directory.
if nothing, you should copy it from `observing/scripts/db(original).sqlite3`, then rename it

### Environment Setup

Before running the script, you need to set up the following environment variables:

```
COLDKEY_SWAP_DISCORD_WEBHOOK_URL=""
DISSOLVE_NETWORK_DISCORD_WEBHOOK_URL=""
TAOSTATS_API_KEY = ""
SENTRY_DSN = ""
SUBTENSOR_ENDPOINT = "wss://archive.chain.opentensor.ai:443/"
```

These environment variables are used for:
- Sending notifications to specific Discord channels for coldkey swaps and network dissolves.
- Authenticating with the TaoStats API for additional network information.

You can set these variables in your system environment or use a `.env` file with a library like `python-dotenv` to load them.

## Usage

To use this script:
1. Ensure you have the necessary dependencies installed.
2. Set up the required environment variables.
3. Run the script to populate the SQLite database with owner and validator information.
4. Once the database is populated, the BtChainObsever class can be used to start monitoring the Bittensor network for events.

## Scheduler Overview in `main.py`

This script utilizes a scheduling mechanism to run the bot and update the dataset at specified intervals. Below are the key components of the scheduling system:

### Bot Scheduling

- **Function:** `schedule_bot(scheduler, interval)`
- **Purpose:** Runs the bot script (`run.py`) at regular intervals.
- **Interval:** Set to 12 seconds by default.
- **Implementation:** 
  - A new thread is created to run the bot using the `run_bot()` function.
  - The scheduler re-enters itself after the specified interval, ensuring continuous execution.

### Dataset Update Scheduling

- **Implementation:**
  - A new thread is created to execute the `update_coldkeys()` function.
  - The scheduler re-enters itself after the specified interval, ensuring the dataset is updated regularly.

## Note

This script is designed for monitoring and reporting purposes. Ensure you have the necessary permissions and comply with all relevant regulations when using this tool to observe blockchain activities. Keep your webhook URLs and API keys secure and do not share them publicly.

The data collection process may take some time due to API rate limits and the amount of data being fetched. Ensure you have a stable internet connection when running the data collection functions.

## Contact

### email : cs.eros111@gmail.com
### github : https://github.com/nesta-onur111