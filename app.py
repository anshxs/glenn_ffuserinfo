from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
from Utilities.until import load_accounts
from Api.Account import get_garena_token, get_major_login
from Api.InGame import get_player_personal_show


accounts = load_accounts()
app = Flask(__name__)
CORS(app)

# Backend URL for updating database
GLENN_BACKEND_URL = "https://glenn-backend.vercel.app"


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


@app.route('/fetch_and_update', methods=['POST'])
def fetch_and_update():
    """
    Fetch FF user info and update database via backend API
    
    Request Body (JSON):
        user_id (required): User's Supabase ID
        ffuid (required): Free Fire UID
        jwt_token (required): User's JWT token for backend authentication
    
    This endpoint:
    1. Fetches FF data from Garena API
    2. Calls glenn-backend API to update database with JWT auth
    3. Returns success/error
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "error": "Invalid Request",
                "message": "Request body must be JSON",
                "code": "INVALID_REQUEST"
            }), 400
        
        user_id = data.get('user_id')
        ffuid = data.get('ffuid')
        jwt_token = data.get('jwt_token')
        
        # Validate required fields
        if not user_id or not ffuid or not jwt_token:
            return jsonify({
                "status": "error",
                "error": "Missing Parameters",
                "message": "user_id, ffuid, and jwt_token are required",
                "code": "MISSING_PARAMETERS"
            }), 400
        
        # Validate UID is integer
        try:
            uid_int = int(ffuid)
            if uid_int <= 0:
                return jsonify({
                    "status": "error",
                    "error": "Invalid UID",
                    "message": "UID must be a positive integer",
                    "code": "INVALID_UID_RANGE"
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "error": "Invalid UID",
                "message": "UID must be a valid integer",
                "code": "INVALID_UID_FORMAT"
            }), 400
        
        # Always use Indian server
        server = 'IND'
        
        # Check server credentials
        if 'uid' not in accounts[server] or 'password' not in accounts[server]:
            return jsonify({
                "status": "error",
                "error": "Server Configuration Error",
                "message": f"Server '{server}' is missing required credentials",
                "code": "SERVER_CONFIG_ERROR"
            }), 500
        
        # Step 1: Get Garena token
        garena_token_result = get_garena_token(accounts[server]['uid'], accounts[server]['password'])
        if not garena_token_result or 'access_token' not in garena_token_result or 'open_id' not in garena_token_result:
            return jsonify({
                "status": "error",
                "error": "Authentication Failed",
                "message": "Failed to obtain Garena token",
                "code": "GARENA_AUTH_FAILED"
            }), 401
        
        # Step 2: Get major login
        major_login_result = get_major_login(garena_token_result["access_token"], garena_token_result["open_id"])
        if not major_login_result or 'serverUrl' not in major_login_result or 'token' not in major_login_result:
            return jsonify({
                "status": "error",
                "error": "Login Failed",
                "message": "Failed to perform major login",
                "code": "MAJOR_LOGIN_FAILED"
            }), 401
        
        # Step 3: Get player personal show data
        player_data = get_player_personal_show(
            major_login_result["serverUrl"], 
            major_login_result["token"], 
            uid_int, 
            need_gallery_info=False,
            call_sign_src=7
        )

        if not player_data:
            return jsonify({
                "status": "error",
                "error": "Data Not Found",
                "message": f"No player data found for UID: {uid_int}",
                "code": "PLAYER_DATA_NOT_FOUND"
            }), 404
        
        # Extract required data
        ff_name = player_data.get('nickname', '')
        ff_creation_date = str(player_data.get('created_at', ''))
        ff_level = player_data.get('level', 0)
        
        if not ff_name or not ff_creation_date:
            return jsonify({
                "status": "error",
                "error": "Incomplete Data",
                "message": "Could not extract nickname or creation date from player data",
                "code": "INCOMPLETE_PLAYER_DATA"
            }), 500
        
        # Step 4: Call glenn-backend API to update database
        backend_url = f"{GLENN_BACKEND_URL}/api/ff-update"
        backend_payload = {
            "user_id": user_id,
            "ffuid": str(uid_int),
            "ff_name": ff_name,
            "ff_creation_date": ff_creation_date,
            "level": ff_level
        }
        backend_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}"
        }
        
        try:
            backend_response = requests.post(
                backend_url,
                json=backend_payload,
                headers=backend_headers,
                timeout=10
            )
            
            if backend_response.status_code != 200:
                error_detail = backend_response.text
                try:
                    error_json = backend_response.json()
                    error_detail = error_json.get('error', error_detail)
                except:
                    pass
                
                return jsonify({
                    "status": "error",
                    "error": "Backend Update Failed",
                    "message": f"Failed to update database: {error_detail}",
                    "code": "BACKEND_UPDATE_FAILED",
                    "backend_status": backend_response.status_code
                }), 500
            
            # Success!
            return jsonify({
                "status": "success",
                "message": "FF data fetched and updated successfully",
                "data": {
                    "ffuid": str(uid_int),
                    "ff_name": ff_name,
                    "ff_creation_date": ff_creation_date,
                    "level": ff_level
                }
            }), 200
            
        except requests.exceptions.RequestException as e:
            print(f"Backend request error: {str(e)}")
            return jsonify({
                "status": "error",
                "error": "Backend Connection Failed",
                "message": f"Could not connect to backend API: {str(e)}",
                "code": "BACKEND_CONNECTION_FAILED"
            }), 500
    
    except Exception as e:
        # Log the unexpected error for debugging
        print(f"Unexpected error in fetch_and_update: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            "status": "error",
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3001)
