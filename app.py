from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from Utilities.until import load_accounts
from Api.Account import get_garena_token, get_major_login
from Api.InGame import get_player_personal_show


accounts = load_accounts()
app = Flask(__name__)
CORS(app)


@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    """
    Get Free Fire user basic info
    
    Query Parameters:
        uid (required): Player UID
    
    Server is always set to IND (Indian server)
    """
    try:
        # Get UID parameter
        uid = request.args.get('uid')
        
        # Always use Indian server
        server = 'IND'
        
        # Validate UID parameter - must be integer
        if not uid:
            response = {
                "status": "error",
                "error": "Missing UID",
                "message": "Empty 'uid' parameter. Please provide a valid 'uid'.",
                "code": "MISSING_UID"
            }
            return jsonify(response), 400
        
        # Check if UID is a valid integer
        try:
            uid_int = int(uid)
            # Additional validation for UID range
            if uid_int <= 0:
                response = {
                    "status": "error",
                    "error": "Invalid UID",
                    "message": "UID must be a positive integer.",
                    "code": "INVALID_UID_RANGE"
                }
                return jsonify(response), 400
        except (ValueError, TypeError):
            response = {
                "status": "error",
                "error": "Invalid UID",
                "message": "UID must be a valid integer.",
                "code": "INVALID_UID_FORMAT"
            }
            return jsonify(response), 400
        
        # Check if server account credentials exist
        if 'uid' not in accounts[server] or 'password' not in accounts[server]:
            response = {
                "status": "error",
                "error": "Server Configuration Error",
                "message": f"Server '{server}' is missing required credentials.",
                "code": "SERVER_CONFIG_ERROR"
            }
            return jsonify(response), 500
        
        # Step 1: Get Garena token
        garena_token_result = get_garena_token(accounts[server]['uid'], accounts[server]['password'])
        if not garena_token_result or 'access_token' not in garena_token_result or 'open_id' not in garena_token_result:
            response = {
                "status": "error",
                "error": "Authentication Failed",
                "message": "Failed to obtain Garena token. Invalid credentials or service unavailable.",
                "code": "GARENA_AUTH_FAILED"
            }
            return jsonify(response), 401
        
        # Step 2: Get major login
        major_login_result = get_major_login(garena_token_result["access_token"], garena_token_result["open_id"])
        if not major_login_result or 'serverUrl' not in major_login_result or 'token' not in major_login_result:
            response = {
                "status": "error",
                "error": "Login Failed",
                "message": "Failed to perform major login. Service unavailable.",
                "code": "MAJOR_LOGIN_FAILED"
            }
            return jsonify(response), 401
        
        # Step 3: Get player personal show data
        player_data = get_player_personal_show(
            major_login_result["serverUrl"], 
            major_login_result["token"], 
            uid_int, 
            need_gallery_info=False,
            call_sign_src=7
        )

        if not player_data:
            response = {
                "status": "error",
                "error": "Data Not Found",
                "message": f"No player data found for UID: {uid_int}",
                "code": "PLAYER_DATA_NOT_FOUND"
            }
            return jsonify(response), 404
        
        # Success response
        response = {
            "status": "success",
            "data": player_data,
            "server": server,
            "uid": uid_int
        }
        return jsonify(response), 200
    
    except Exception as e:
        # Log the unexpected error for debugging
        print(f"Unexpected error in get_user_info: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        response = {
            "status": "error",
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request.",
            "code": "INTERNAL_SERVER_ERROR"
        }
        return jsonify(response), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3001)
