import hashlib
import base64
import uuid
from Crypto.Cipher import AES

SECRET = '89155cc4e8634ec5b1b6364013b23e3e'

def encrypt_aes(plaintext: str, key: str) -> bytes:
    """
    对传入的明文字符串使用 AES 进行加密，返回加密后的二进制数据。
    注意：AES 的密钥长度必须为 16、24 或 32 字节。
    """
    key_bytes = key.encode('utf-8')
    plaintext_bytes = plaintext.encode('utf-8')
    padded_plaintext = pad(plaintext_bytes)

    # 使用 AES 的 ECB 模式，等价于 Java 默认的 "AES/ECB/PKCS5Padding"
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    encrypted_bytes = cipher.encrypt(padded_plaintext)
    return encrypted_bytes

def pad(data: bytes) -> bytes:
    """
    使用 PKCS5/PKCS7 填充数据，使其长度为 AES 块大小的整数倍。
    """
    pad_len = AES.block_size - (len(data) % AES.block_size)
    return data + bytes([pad_len] * pad_len)

class Calculate:
    @staticmethod
    def generate_sign(params: dict) -> str:
        # 1. 按参数名升序排序
        sorted_keys = sorted(params.keys())

        # 2. 拼接所有参数值
        values_str = ''.join([str(params[key]) for key in sorted_keys])

        # 3. 追加密钥
        sign_str = values_str + SECRET

        # 4. 计算MD5
        return hashlib.md5(sign_str.encode()).hexdigest()
    
    @staticmethod
    def aes_base64_encode(plaintext: str) -> str:
        key = SECRET[-16:]
        encrypted_bytes = encrypt_aes(plaintext, key)
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    
    @staticmethod
    def get_random_device_id() -> str:
        return str(uuid.uuid4()).replace("-", "").lower()