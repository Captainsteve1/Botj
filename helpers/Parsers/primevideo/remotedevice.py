from requests import Session
from base64 import b64decode
from json.decoder import JSONDecodeError

class RemoteDevice:

    def __init__(self, host:str, token:str):
        self.host = host
        self.token = token
        self.session = Session()

    def _post_request(self, method:str, params:dict) -> dict:
        try:
            params = {'method': method, 'params': params, 'token': self.token}
            res = self.session.post(self.host, json=params, verify=False)
        finally:
            pass
        return res.json()['message']

    def get_license_challenge(self, pssh:str, cert) -> tuple[(bytes, bytes)]:
        print('Getting challenge')
        response = self._post_request(method='GetChallenge', params={'init': pssh, 'cert': cert})
        if response is None:
            raise 'No challenge response. Exiting'
        session_id = response['session_id']
        challenge = response['challenge']
        return (session_id, b64decode(challenge))

    def get_keys(self, lic_b64:str, session_id:bytes):
        print('Getting keys')
        response = self._post_request(method='GetKeys', params={'session_id': session_id, 'cdmkeyresponse': lic_b64})
        return response['keys']