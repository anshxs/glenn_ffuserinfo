import requests
import Proto.compiled.PlayerPersonalShow_pb2
from Utilities.until import encode_protobuf, decode_protobuf
import json
from Configuration.APIConfiguration import RELEASEVERSION, DEBUG


def get_player_personal_show(serverurl, authorization, account_id, need_gallery_info=False, call_sign_src=7):
    """
    Get player personal show data
    
    Args:
        serverurl (str): Server URL
        authorization (str): Bearer token for authentication
        account_id (int): Player account ID
        need_gallery_info (bool): Whether to include gallery info, default False
        call_sign_src (int): Call sign source, default 7
    
    Returns:
        dict: JSON response data
    """
    url = f"{serverurl}/GetPlayerPersonalShow"

    encrypted_payload = encode_protobuf({
        "accountId": account_id,
        "callSignSrc": call_sign_src,
        "needGalleryInfo": need_gallery_info,
    }, Proto.compiled.PlayerPersonalShow_pb2.request())

    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/octet-stream",
        'Expect': "100-continue",
        'Authorization': f"Bearer {authorization}",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': RELEASEVERSION,
        'Content-Type': "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=encrypted_payload, headers=headers)
    if DEBUG:
        print("[I] RES:", response.content, "\n")
    try:
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Decode protobuf response
        message = decode_protobuf(response.content, Proto.compiled.PlayerPersonalShow_pb2.response)
        
        # Convert to JSON
        json_data = json.loads(json.dumps(message, default=str))
        return json_data
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {response.text}")
        return None
    except Exception as e:
        print(f"Error processing response: {e}")
        return None
