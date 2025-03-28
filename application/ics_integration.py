import requests
import xml.etree.ElementTree as ET
import json
import base64

class ICSIntegration:
    def __init__(self):
        self.vin_url = 'http://192.168.102.93/icsQueryService/api/Query/Results/?format=xml&query_name=GET_VIN&SERVICE_KEY=68R82WSPO199XW1VE6LX4V8'
        self.defect_url = "http://192.168.102.93/icsexternalinterface/vehicledataservice.svc/AddDeviceDefectsWithImage"
        
    def request_vin(self, body_num):
        """Request VIN from ICS system"""
        try:
            api_url = self.vin_url + f'&BODY_NUM={body_num}'
            response = requests.get(api_url)
            if response.status_code != 200:
                print(f"Error getting VIN: {response.status_code}")
                return None
                
            # Parse XML response
            root = ET.fromstring(response.text)
            xml_vin = root.find('DATA/VIN')
            if xml_vin is None:
                print("VIN not found in response")
                return None
                
            return xml_vin.text
        except Exception as e:
            print(f"Error requesting VIN: {e}")
            return None

    def send_defect_data(self, vin, image_base64, expected_part, actual_part):
        """Send defect data to ICS system"""
        try:
            # If image_base64 is a URL, fetch the image content
            if isinstance(image_base64, str) and image_base64.startswith('http'):
                try:
                    response = requests.get(image_base64)
                    response.raise_for_status()
                    image_base64 = base64.b64encode(response.content).decode('utf-8')
                except Exception as e:
                    print(f"Error fetching image from URL: {e}")
                    return False
            
            # Ensure image_base64 doesn't include the data:image prefix
            if isinstance(image_base64, str) and ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            defect_data = {
                "DeviceId": "EI_CAMARITA",
                "CardId": "00.00.00.00.87.92.B4.1A",
                "Vin": vin,
                "ToolDefectsWithImage": [
                    {
                        "ToolId": "Capot",
                        "Discrepancy": "EQUIVOCADO/A",
                        "Comment": f"es un capot tipo {actual_part[-1] if actual_part else 'N/A'}, debería ser tipo {expected_part[-1] if expected_part else 'N/A'}",
                        "DefectImageString": image_base64
                    }
                ],
                "InspectedTools": [
                    "..."
                ]
            }

            print(f"Sending defect data to ICS for VIN: {vin}")
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.defect_url,
                data=json.dumps(defect_data),
                headers=headers,
                timeout=30  # Add timeout
            )

            if response.status_code != 200:
                print(f"Error sending defect data: {response.status_code}")
                print(f"Response content: {response.text}")
                return False

            return True
        except Exception as e:
            print(f"Error sending defect data: {str(e)}")
            return False 