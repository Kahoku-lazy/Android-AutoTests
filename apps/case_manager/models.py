"""case-manager ORM models — cm_ prefix tables."""
from django.db import models


class TestDefinition(models.Model):
    """Executable test case definition → cm_test_definitions."""
    id = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=500)
    category = models.CharField(max_length=200, default='', blank=True)
    description = models.TextField(default='', blank=True)
    steps = models.TextField(default='', blank=True)
    steps_json = models.TextField(default='[]')
    enabled = models.BooleanField(default=True)
    package_name = models.CharField(max_length=200, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cm_test_definitions'

    def __str__(self):
        return self.title


class TestCaseCache(models.Model):
    """YAML export cache → cm_test_cases."""
    name = models.CharField(max_length=500)
    description = models.TextField(default='', blank=True)
    yaml_content = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cm_test_cases'

    def __str__(self):
        return self.name
