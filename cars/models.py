from django.db import models


class Car(models.Model):
    car_model = models.CharField(max_length=255, help_text="Car model and brand")
    license_start = models.DateField(help_text="License start date")
    license_end = models.DateField(help_text="License expiration date")
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Car'
        verbose_name_plural = 'Cars'
    
    def __str__(self):
        return f"{self.car_model} (License: {self.license_start} to {self.license_end})"
