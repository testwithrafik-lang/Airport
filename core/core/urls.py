from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from assistant.views import AirportAiPageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/locations/', include('locations.urls')), 
    path('api/fleet/', include('fleet.urls')),         
    path('api/flights/', include('flights.urls')),     
    path('api/users/', include('users.urls')),        
    path('api/payments/', include('payments.urls')), 
    path('api/assistant/', include('assistant.urls')),
    path('ai/', AirportAiPageView.as_view()),
    path('__debug__/', include('debug_toolbar.urls')),
    path('success/', lambda request: HttpResponse("Thank you! Payment was successful. Check your email."), name='payment-success'),
]
