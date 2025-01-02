import shortuuid
from django.conf import settings
from django.db import models


# Create your models here.
class Course(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    code = models.CharField(unique=True, editable=False, max_length=6)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'user_type': 't'})
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='courses', blank=True)

    def save(self, *args, **kwargs):
        if not self.code: # PUT, PATCH 시 미적용
            while True:
                new_code = shortuuid.ShortUUID().random(length=6)
                if not Course.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Code: {self.code})"