import json
from requests import Session
from base64 import b64decode
from binascii import unhexlify
from json.decoder import JSONDecodeError
DEFAULT_CERTIFICATE = 'CAUSwwUKvQIIAxIQ5US6QAvBDzfTtjb4tU/7QxiH8c+TBSKOAjCCAQoCggEBAObzvlu2hZRsapAPx4Aa4GUZj4/GjxgXUtBH4THSkM40x63wQeyVxlEEo1D/T1FkVM/S+tiKbJiIGaT0Yb5LTAHcJEhODB40TXlwPfcxBjJLfOkF3jP6wIlqbb6OPVkDi6KMTZ3EYL6BEFGfD1ag/LDsPxG6EZIn3k4S3ODcej6YSzG4TnGD0szj5m6uj/2azPZsWAlSNBRUejmP6Tiota7g5u6AWZz0MsgCiEvnxRHmTRee+LO6U4dswzF3Odr2XBPD/hIAtp0RX8JlcGazBS0GABMMo2qNfCiSiGdyl2xZJq4fq99LoVfCLNChkn1N2NIYLrStQHa35pgObvhwi7ECAwEAAToQdGVzdC5uZXRmbGl4LmNvbRKAA4TTLzJbDZaKfozb9vDv5qpW5A/DNL9gbnJJi/AIZB3QOW2veGmKT3xaKNQ4NSvo/EyfVlhc4ujd4QPrFgYztGLNrxeyRF0J8XzGOPsvv9Mc9uLHKfiZQuy21KZYWF7HNedJ4qpAe6gqZ6uq7Se7f2JbelzENX8rsTpppKvkgPRIKLspFwv0EJQLPWD1zjew2PjoGEwJYlKbSbHVcUNygplaGmPkUCBThDh7p/5Lx5ff2d/oPpIlFvhqntmfOfumt4i+ZL3fFaObvkjpQFVAajqmfipY0KAtiUYYJAJSbm2DnrqP7+DmO9hmRMm9uJkXC2MxbmeNtJHAHdbgKsqjLHDiqwk1JplFMoC9KNMp2pUNdX9TkcrtJoEDqIn3zX9p+itdt3a9mVFc7/ZL4xpraYdQvOwP5LmXj9galK3s+eQJ7bkX6cCi+2X+iBmCMx4R0XJ3/1gxiM5LiStibCnfInub1nNgJDojxFA3jH/IuUcblEf/5Y0s1SzokBnR8V0KbA=='

def dump_json(dic):
    return json.dumps(dic, indent=4, ensure_ascii=False)

INVALID_TOKEN = 1
INVALID_HOST = 2
NOT_SUPPORTED = 3

class RemoteDevice:

    def __init__(self, host, token):
        self.host = host
        self.token = token
        self.session = Session()

    def _post_request(self, method, params):
        try:
            params = {'method': method, 'params': params, 'token': self.token}
            res = self.session.post(self.host, json=params, verify=False)
        finally:
            pass
        return res.json()['message']

    def get_license_challenge(self, pssh):
        print('Getting challenge')
        response = self._post_request(method='GetChallenge', params={'init': pssh, 'cert': DEFAULT_CERTIFICATE})
        if response is None:
            raise 'No challenge response. Exiting'
        session_id = response['session_id']
        challenge = response['challenge']
        return (session_id, b64decode(challenge))

    def get_msl_challenge(self):
        print('Getting MSL Challenge')
        response = self._post_request(method='GetMSL', params={'cert': DEFAULT_CERTIFICATE})
        if response is None:
            raise 'No challenge response. Exiting'
        session_id = response.get('session_id')
        challenge = response.get('challenge')
        return (session_id, b64decode(challenge))

    def get_encryption_and_sign_key(self, license_b64, session_id):
        print('Getting encryption and sign key')
        response = self._post_request(method='GetSignKey', params={'session_id': session_id, 'cdmkeyresponse': license_b64})
        encryption_key = response.get('encryption_key')
        sign_key = response.get('sign_key')
        print('Encryption Key', encryption_key)
        print('Sign Key', sign_key)
        return (unhexlify(encryption_key), unhexlify(sign_key))

    def get_keys(self, lic_b64, session_id):
        print('Getting keys')
        response = self._post_request(method='GetKeys', params={'session_id': session_id, 'cdmkeyresponse': lic_b64})
        return response['keys']