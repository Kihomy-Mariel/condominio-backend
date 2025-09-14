from django.urls import path
from .views import (
    GenerarExpensasMensuales,
    ExpensasList, MisExpensasList,
    CrearPagoView, PagosDeExpensaList,
    AprobarPago, RechazarPago,
)

urlpatterns = [
    # CU06
    path("expensas/generar/", GenerarExpensasMensuales.as_view()),

    # Listados / consultas
    path("expensas/", ExpensasList.as_view()),          # Admin/Guardia/Empleado; Copropietario ve las suyas (filtro en QS)
    path("mis-expensas/", MisExpensasList.as_view()),   # Copropietario

    # CU07
    path("pagos/", CrearPagoView.as_view()),

    # CU09 pagos de una expensa
    path("expensas/<int:pk>/pagos/", PagosDeExpensaList.as_view()),

    # CU08
    path("pagos/<int:pk>/aprobar/", AprobarPago.as_view()),
    path("pagos/<int:pk>/rechazar/", RechazarPago.as_view()),
]
