import os

chrome_cdm_1610_l3 = {
    "name": "chrome_cdm_1610_l3",
    "description": "chromecdm 1610 x64",
    "security_level": 3,
    "session_id_type": "chrome",
    "private_key_available": True,
    "vmp": True,
    "send_key_control_nonce": False,
}

android_s905x_l3 = {
    "name": "android_s905x_l3",
    "description": "android 6 amlogic_s905x_lvl3 lvl3 security level",
    "security_level": 3,
    "session_id_type": "android",
    "private_key_available": True,
    "vmp": False,
    "send_key_control_nonce": True,
}

android_phone8162_l3 = {
    "name": "android_phone8162_l3",
    "description": "android 6 lvl3 security level",
    "security_level": 3,
    "session_id_type": "android",
    "private_key_available": True,
    "vmp": False,
    "send_key_control_nonce": True,
}

devices_available = [
    chrome_cdm_1610_l3
]

FILES_FOLDER = "devices"

class DeviceConfig:
    def __init__(self, device):
        self.device_name = device["name"]
        self.description = device["description"]
        self.security_level = device["security_level"]
        self.session_id_type = device["session_id_type"]
        self.private_key_available = device["private_key_available"]
        self.vmp = device["vmp"]
        self.send_key_control_nonce = device["send_key_control_nonce"]
        if "keybox_filename" in device:
            self.keybox_filename = os.path.join(
                os.path.dirname(__file__),
                FILES_FOLDER,
                device["name"],
                device["keybox_filename"],
            )
        else:
            self.keybox_filename = os.path.join(
                os.path.dirname(__file__), FILES_FOLDER, device["name"], "keybox"
            )
        if "device_cert_filename" in device:
            self.device_cert_filename = os.path.join(
                os.path.dirname(__file__),
                FILES_FOLDER,
                device["name"],
                device["device_cert_filename"],
            )
        else:
            self.device_cert_filename = os.path.join(
                os.path.dirname(__file__), FILES_FOLDER, device["name"], "device_cert"
            )
        if "device_private_key_filename" in device:
            self.device_private_key_filename = os.path.join(
                os.path.dirname(__file__),
                FILES_FOLDER,
                device["name"],
                device["device_private_key_filename"],
            )
        else:
            self.device_private_key_filename = os.path.join(
                os.path.dirname(__file__),
                FILES_FOLDER,
                device["name"],
                "device_private_key",
            )
        if "device_client_id_blob_filename" in device:
            self.device_client_id_blob_filename = os.path.join(
                os.path.dirname(__file__),
                FILES_FOLDER,
                device["name"],
                device["device_client_id_blob_filename"],
            )
        else:
            self.device_client_id_blob_filename = os.path.join(
                os.path.dirname(__file__),
                FILES_FOLDER,
                device["name"],
                "device_client_id_blob",
            )
        if "device_vmp_blob_filename" in device:
            self.device_vmp_blob_filename = os.path.join(
                os.path.dirname(__file__),
                FILES_FOLDER,
                device["name"],
                device["device_vmp_blob_filename"],
            )
        else:
            self.device_vmp_blob_filename = os.path.join(
                os.path.dirname(__file__),
                FILES_FOLDER,
                device["name"],
                "device_vmp_blob",
            )

    def __repr__(self):
        return (
            "DeviceConfig(name={}, description={}, security_level={}, session_id_type={}, private_key_available={}, vmp={})"
        ).format(
            self.device_name,
            self.description,
            self.security_level,
            self.session_id_type,
            self.private_key_available,
            self.vmp,
        )
