from os import path
import json

from dFL.Security.crypto import AES
from dFL.Utils.util import c2b, c2s, hash_msg


def save_file(data, file_path, file_name, node):
    aes = AES()
    nonce, cipher = aes.encrypt(data)
    hash_cipher = hash_msg(cipher)
    signature = node.secure_communication.signer.sign_message(hash_cipher)

    try:
        with open(path.join(file_path, file_name), 'wb') as f:
            f.write(cipher)
            with open(path.join(file_path, f'{path.splitext(file_name)[0]}_info.json'), 'w') as d:
                info = {
                    "aes_key": c2s(aes.key),
                    "nonce": c2s(nonce),
                    "hash": c2s(hash_cipher),
                    "signature": c2s(signature),
                    "size": len(cipher)
                }
                d.write(json.dumps(info))
        return True
    except:
        return False


def save_peer_file(cipher, file_path, file_name, info):
    try:
        with open(path.join(file_path, file_name), 'wb') as f:
            f.write(cipher)
            with open(path.join(file_path, f'{path.splitext(file_name)[0]}_info.json'), 'w') as d:
                d.write(json.dumps(info))
        return True
    except:
        return False


def read_file(file_path, file_name, info_only=False):
    with open(path.join(file_path, f'{path.splitext(file_name)[0]}_info.json'), 'r') as f:
        info = json.loads(f.read())
        if info_only:
            return info

        aes_key = c2b(info['aes_key'])
        nonce = c2b(info['nonce'])
        aes = AES(aes_key, nonce)
        with open(path.join(file_path, file_name), 'rb') as d:
            data= aes.decrypt(d.read())
            if data is not None:
                return data, info

    return None, None




