from django.db import models


class TokenRevocation(models.Model):
    KIND_SESSION = "session"
    KIND_TOKEN = "token"
    KIND_USER = "user"
    KIND_CHOICES = [
        (KIND_SESSION, "会话"),
        (KIND_TOKEN, "单令牌"),
        (KIND_USER, "停用账号"),
    ]

    kind = models.CharField(max_length=16, choices=KIND_CHOICES, verbose_name="吊销粒度")
    ref = models.CharField(max_length=64, verbose_name="会话标识或令牌标识")
    expires_at = models.DateTimeField(verbose_name="失效时刻")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="写入时刻")

    class Meta:
        db_table = "acc_token_revocations"
        constraints = [
            models.UniqueConstraint(fields=["kind", "ref"], name="uniq_acc_revocation_kind_ref"),
        ]
        indexes = [
            models.Index(fields=["expires_at"], name="idx_acc_revocation_expires"),
        ]
        verbose_name = "令牌吊销记录"
        verbose_name_plural = "令牌吊销记录"

    def __str__(self) -> str:
        return f"{self.kind}:{self.ref} -> {self.expires_at:%Y-%m-%d %H:%M:%S}"
