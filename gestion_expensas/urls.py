from django.urls import path
from .views import MisExpensasList, CrearPagoView, PagosDeExpensaList, AprobarPagoSimple

urlpatterns = [
    path("mis-expensas/", MisExpensasList.as_view()),
    path("pagos/", CrearPagoView.as_view()),
    path("expensas/<int:pk>/pagos/", PagosDeExpensaList.as_view()),
    path("pagos/<int:pk>/aprobar/", AprobarPagoSimple.as_view()),
]
