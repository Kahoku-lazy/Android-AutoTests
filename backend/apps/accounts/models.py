"""登录鉴权的持久化模型。

本模块的业务功能如下：
1. TokenRevocation: 记录已吊销的会话（sid）与单个令牌（jti），让登出立即生效。
"""

from django.db import models


class TokenRevocation(models.Model):
    """
    令牌吊销记录 → acc_token_revocations。

    `kind` 区分粒度：`session` 对应一次登录的会话（sid，access 与 refresh 一起失效），
    `token` 对应单个令牌（jti，兜底没有 sid 的旧令牌）。判定只看未过期的行，
    过期行由写入方顺手清理。写库一律经本 App 的 `api.py`。

    Attributes:
        kind: 吊销粒度（session / token）。
        ref: 会话标识或令牌标识。
        expires_at: 记录失效时刻；超过后不再参与判定。
        created_at: 写入时刻（排障用）。
    """

    KIND_SESSION = "session"
    KIND_TOKEN = "token"
    KIND_CHOICES = [
        (KIND_SESSION, "会话"),
        (KIND_TOKEN, "单令牌"),
    ]

    kind = models.CharField(max_length=16, choices=KIND_CHOICES, verbose_name="吊销粒度")
    ref = models.CharField(max_length=64, verbose_name="会话标识或令牌标识")
    expires_at = models.DateTimeField(verbose_name="失效时刻")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="写入时刻")

    class Meta:
        db_table = "acc_token_revocations"
        constraints = [
            # 同一粒度的同一标识只留一行：重复登出用 update_or_create 幂等覆盖
            models.UniqueConstraint(fields=["kind", "ref"], name="uniq_acc_revocation_kind_ref"),
        ]
        indexes = [
            models.Index(fields=["expires_at"], name="idx_acc_revocation_expires"),
        ]
        verbose_name = "令牌吊销记录"
        verbose_name_plural = "令牌吊销记录"

    def __str__(self) -> str:
        return f"{self.kind}:{self.ref} -> {self.expires_at:%Y-%m-%d %H:%M:%S}"
