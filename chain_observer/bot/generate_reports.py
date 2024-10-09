import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_report(title, success, details, time_stamp):
    """
    Generates a report based on the extrinsic success and details provided.
    """
    try:
        fields = [{
            "name": "🧱 **CURRENT BLOCK** 🧱",
            "value": f"{details['current_block_number']}\n\n",
            "inline": False
        }]
        for key, value in details.items():
            if key == 'identifier':
                print(value)
                fields.append({
                    "name": f"\n\n🔑 ** COLDKEY ** \n\n\n",
                    "value": f"{value}\n\n",
                    "inline": False
                })
            
        if success:
            for key, value in details.items():
                if key != 'current_block_number' and key != 'identifier':
                    fields.append({
                        "name": f"\n\n🔑 **{key.upper()}** \n\n\n",
                        "value": f"{value}\n\n",
                        "inline": False
                    })
        else:
            fields.append({
                "name": "🔴 **Extrinsic Failed** 🔴",
                "value": "The extrinsic failed to execute.",
                "inline": False
            })
        fields.append({
            "name": "\n\n🕙  **CURRENT BLOCK TIMESTAMP** \n\n\n",
            "value": f"{time_stamp}\n\n",
            "inline": False
        })
        return {
            "title": title,
            "description": "",
            "color": 16776960 if "COLDKEY" in title else 12910592,  # Different colors for different reports
            "fields": fields,
        }
    except Exception as e:
        logging.exception(f"Exception in generate_report : {e}")
        return {
            "title": title,
            "description": "An error occurred while generating the report.",
            "color": 16711680, 
            "fields": [{
                "name": "Error",
                "value": "An error occurred while generating the report.",
                "inline": False
            }]
        }
    
def generate_vote_report(title, success, details, time_stamp):
    """
    Generates a report based on the extrinsic success and details provided.
    """
    try:
        fields = [{
            "name": "🧱 **CURRENT BLOCK** 🧱",
            "value": f"{details['current_block_number']}\n\n",
            "inline": False
        }]
        for key, value in details.items():
            if key != 'current_block_number':
                fields.append({
                    "name": f"\n\n🔑 **{key.upper()}** \n\n\n",
                    "value": f"{value}\n\n",
                    "inline": False
                })
        if success:
            fields.append({
                "name": "🍏 **Extrinsic Successful** 🍏",
                "value": "The extrinsic executed successfully.",
                "inline": False
            })
        else:
            fields.append({
                "name": "🍎 **Extrinsic Failed** 🍎",
                "value": "The extrinsic failed to execute.",
                "inline": False
            })
        fields.append({
            "name": "\n\n🕙  **CURRENT BLOCK TIMESTAMP** \n\n\n",
            "value": f"{time_stamp}\n\n",
            "inline": False
        })
        
        return {
            "title": title,
            "description": "",
            "color": 14776960,
            "fields": fields,
        }
    except Exception as e:
        logging.exception(f"Exception in generate_vote_report : {e}")
        return {
            "title": title,
            "description": "An error occurred while generating the report.",
            "color": 16711680,  
            "fields": [{
                "name": "Error",
                "value": "An error occurred while generating the report.",
                "inline": False
            }]
        }
        
def generate_dissolved_netword(title, details, time_stamp):
    """
    Generates a report based on the extrinsic success and details provided.
    """
    try:
        fields = []
        for key, value in details.items():
            fields.append({
                "name": f"\n\n🔑 **{key.upper()}** \n\n\n",
                "value": f"{value}\n\n",
                "inline": False
            })  
        fields.append({
            "name": "\n\n🕙  **CURRENT BLOCK TIMESTAMP** \n\n\n",
            "value": f"{time_stamp}\n\n",
            "inline": False
        })
        
        return {
            "title": title,
            "description": "",
            "color": 16273827,
            "fields": fields,
        }
    except Exception as e:
        logging.exception(f"Exception in generate_dissolved_netword : {e}")
        return {
            "title": title,
            "description": "An error occurred while generating the report.",
            "color": 16711680,  
            "fields": [{
                "name": "Error",
                "value": "An error occurred while generating the report.",
                "inline": False
            }]
        }