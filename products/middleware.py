"""
Middleware for admin redirects and customizations
"""
from django.shortcuts import redirect
from django.urls import reverse


class AdminRedirectMiddleware:
    """Middleware to redirect admin requests to product catalog"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is an admin index request
        if request.path == '/admin/' and request.user.is_authenticated and request.user.is_staff:
            # Redirect to product catalog control center
            return redirect('/admin/products/product/')
        
        response = self.get_response(request)
        return response 