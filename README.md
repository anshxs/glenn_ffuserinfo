# Glenn FF User Info API

Simple Free Fire User Info API that fetches player personal show data from Indian server.

## Features

- Get Free Fire user basic information
- Always uses Indian (IND) server
- Returns all player personal show details
- Simple single endpoint API

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start the API server

```bash
python app.py
```

Server will run on `http://localhost:3001`

### API Endpoint

**GET** `/get_user_info`

Query Parameters:
- `uid` (required): Free Fire player UID

Example:
```bash
curl "http://localhost:3001/get_user_info?uid=123456789"
```

### Response Format

Success response:
```json
{
  "status": "success",
  "data": {
    // Player personal show data
  },
  "server": "IND",
  "uid": 123456789
}
```

Error response:
```json
{
  "status": "error",
  "error": "Error Type",
  "message": "Error message",
  "code": "ERROR_CODE"
}
```

## Configuration

- Server: Always set to IND (Indian server)
- Port: 3001
- Account credentials: Configured in `Configuration/AccountConfiguration.json`

## Project Structure

```
glenn_ffuserinfo/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── Api/
│   ├── Account.py                  # Garena authentication
│   └── InGame.py                   # Player data fetching
├── Configuration/
│   ├── AccountConfiguration.json   # Server credentials
│   ├── AESConfiguration.py         # AES encryption keys
│   └── APIConfiguration.py         # API version config
├── Utilities/
│   └── until.py                    # Helper functions
└── Proto/
    └── compiled/                   # Compiled protobuf files
```
