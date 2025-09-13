from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Pago

@receiver(post_save, sender=Pago)
def pago_post_save(sender, instance: Pago, created, **kwargs):
    if created and instance.estado == "APROBADO":
        instance.aplicar_en_expensa(+1)

@receiver(pre_save, sender=Pago)
def pago_pre_save(sender, instance: Pago, **kwargs):
    if not instance.pk: return
    prev = Pago.objects.get(pk=instance.pk)
    if prev.estado != instance.estado:
        if prev.estado == "APROBADO" and instance.estado != "APROBADO":
            prev.aplicar_en_expensa(-1)
        if prev.estado != "APROBADO" and instance.estado == "APROBADO":
            instance.aplicar_en_expensa(+1)

@receiver(post_delete, sender=Pago)
def pago_post_delete(sender, instance: Pago, **kwargs):
    if instance.estado == "APROBADO":
        instance.aplicar_en_expensa(-1)
