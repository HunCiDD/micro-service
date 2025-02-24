class SSHSecurityOptions:
    ...

    # 安全加密算法
    ciphers = (
        'chacha20-poly1305@openssh.com',
        'aes128-ctr',
        'aes256-ctr',
        'aes128-gcm@openssh.com',
        'aes256-gcm@openssh.com',
    )

    # 安全秘钥交换算法
    kex = (
        'ecdh-sha2-nistp256',
        'ecdh-sha2-nistp384',
        'ecdh-sha2-nistp521',
        'diffie-hellman-group15-sha512',
        'diffie-hellman-group16-sha512',
        'diffie-hellman-group17-sha512',
        'diffie-hellman-group18-sha512',
        'diffie-hellman-group-exchange-sha256',
    )

    # 消息验证码（MAC）算法
    digests = (
        'hmac-sha2-256',
        'hmac-sha2-512',
        'hmac-sha2-256-etm@openssh.com',
        'hmac-sha2-512-etm@openssh.com',
    )

    # 签名算法
    key_types = ('rsa-sha2-256' 'rsa-sha2-512',)


class TLSSecurityOptions:
    ciphers = ('TLS_AES_256_GCM_SHA384',)
