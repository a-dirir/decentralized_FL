import pickle
from os import urandom

from dFL.Security.crypto import AES, ECKeyExchange, DigitalSigner
from dFL.Utils.util import c2b, c2s



class SecureCommunication:
    def __init__(self, node_id=None, storage_directory_keys=None):
        if node_id is not None:
            self.node_id = node_id
            self.encryptor = ECKeyExchange(directory_path=storage_directory_keys)
            self.signer = DigitalSigner(directory_path=storage_directory_keys)
        else:
            self.node_id = -99
            self.encryptor = ECKeyExchange(generate_keys=True)
            self.signer = DigitalSigner(generate_keys=True)
        self.lookup = {}

    def outgress(self, msg: dict, pek: bytes = None):
        msg = pickle.dumps(msg)
        if self.lookup.get(c2s(pek)) is None:
            shared_key = self.encryptor.get_shared_key(pek)
            nonce = urandom(16)
            self.lookup[c2s(pek)] = [shared_key, nonce]
        else:
            shared_key = self.lookup[c2s(pek)][0]
            nonce = self.lookup[c2s(pek)][1]
            self.lookup.pop(c2s(pek))

        aes = AES(key=shared_key, nonce=nonce)
        _, msg_cipher = aes.encrypt(msg)
        signature = self.signer.sign_message(msg)

        if signature is None or msg_cipher is None:
            return None

        out_msg = {
            "node_id": self.node_id,
            "content": msg_cipher,
            "nonce": nonce,
            "signature": signature,
            "ek": self.encryptor.get_public_key(),
            "sk": self.signer.get_public_key()
        }

        for key, value in out_msg.items():
            if key != "node_id":
                out_msg[key] = c2s(value)

        return out_msg

    def ingress(self, msg, return_response=False):
        pek = msg["ek"]
        for key, value in msg.items():
            if key != "node_id":
                msg[key] = c2b(value)

        if self.lookup.get(pek) is not None:
            shared_key = self.lookup[pek][0]
            nonce = self.lookup[pek][1]
            self.lookup.pop(pek)
        else:
            shared_key = self.encryptor.get_shared_key(msg["ek"])
            nonce = msg["nonce"]
            self.lookup[pek] = [shared_key, nonce]

        aes = AES(shared_key, nonce)
        out_msg = aes.decrypt(msg["content"])

        if out_msg is not None and self.signer.verify_other_signatures(msg["signature"], out_msg, msg["sk"]):
            if return_response:
                return [pickle.loads(out_msg), msg]
            else:
                return pickle.loads(out_msg)
        else:
            return None

