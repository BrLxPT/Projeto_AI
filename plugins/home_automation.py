import requests

def toggle_lights(device_id, state):
    # Home Assistant API
    url = f"http://homeassistant.local:8123/api/services/switch/turn_{state}"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    requests.post(url, headers=headers, json={"entity_id": device_id})
    return f"Luzes {device_id} {state}"

def register():
    return {
        "name": "home_automation",
        "description": "Controle de dispositivos IoT",
        "actions": {
            "lights_toggle": {
                "description": "Controlar luzes inteligentes",
                "parameters": {"device_id": "string", "state": "'on' ou 'off'"},
                "execute": lambda p: toggle_lights(p["device_id"], p["state"])
            }
        }
    }