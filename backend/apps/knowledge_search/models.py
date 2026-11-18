"""知识库检索数据模型：模块登记（平台侧真相源）。"""

from django.db import models


class KnowledgeModule(models.Model):
    """知识库模块登记 → ks_modules。

    一行 = 一个模块 = 一个服务器本地只读资料目录。库名即引擎向量集合名；
    资料目录只读，索引与检索仍在 engines/ae_harness/knowledge。
    写库一律经本 App 的 api.py；检索库目录 yaml 由 registry.py 从本表派生。
    """

    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=200)
    data_dir = models.CharField(max_length=500)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ks_modules"
        ordering = ["name"]
        verbose_name = "知识库模块"
        verbose_name_plural = "知识库模块"

    def __str__(self):
        return f"{self.name} [{'启用' if self.enabled else '禁用'}]"
