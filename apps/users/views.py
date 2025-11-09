from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Profile  # Assuming you have a Profile model
from django.db import IntegrityError

def user_login(request):
    """Handle user login using email as identifier"""
    # Check if already logged in
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin:index')
        return redirect('donations:dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('username')  # Form field is 'username' but contains email
        password = request.POST.get('password')
        
        # Find user by email first
        try:
            user = User.objects.get(email=email)
            # Authenticate with username and password
            auth_user = authenticate(request, username=user.username, password=password)
            
            if auth_user is not None:
                login(request, auth_user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                
                if auth_user.is_staff:
                    return redirect('admin:index')
                else:
                    return redirect('donations:dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
            
    return render(request, 'users/login.html')

def donor_signup(request):
    """Handle new user registration with email as primary identifier"""
    if request.user.is_authenticated:
        return redirect('donations:dashboard')
        
    if request.method == 'POST':
        # Basic info
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        terms = request.POST.get('terms')
        category = request.POST.get('category')
        
        # Organization fields
        organization_name = request.POST.get('organization_name', '')
        country = request.POST.get('country', '')
        city = request.POST.get('city', '')
        address = request.POST.get('address', '')
        payment_type = request.POST.get('payment_type', '')
        
        # Validate form data
        if not all([email, first_name, last_name, password1, password2, category]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'users/signup.html')
            
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/signup.html')
            
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'users/signup.html')
            
        if not terms:
            messages.error(request, 'You must agree to the terms of service.')
            return render(request, 'users/signup.html')
            
        # Organization validation
        if category in ['Company CSR', 'NGO']:
            if not organization_name:
                messages.error(request, 'Please provide your organization name.')
                return render(request, 'users/signup.html')
                
            if not all([country, city]):
                messages.error(request, 'Please provide your organization location details.')
                return render(request, 'users/signup.html')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'users/signup.html')
            
        try:
            # Create user with email as username
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile without phone
            profile = Profile(
                user=user,
                is_donor=True,
                donor_type=category,
            )
            
            # Add organization details if applicable
            if category in ['Company CSR', 'NGO']:
                profile.organization_name = organization_name
                profile.country = country
                profile.city = city
                profile.address = address
                profile.payment_preference = payment_type
            
            profile.save()
            
            # Django's built-in login
            login(request, user)
            
            messages.success(request, f"Welcome to RHCI, {first_name}! Your account has been created.")
            return redirect('donations:dashboard')

        except IntegrityError:
            messages.success(request, f"An account has been created proceed with Login In.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            
    return render(request, 'users/signup.html')

@login_required(login_url='/login/')
def donor_dashboard_view(request):
    """Display the donor dashboard using Django's authentication"""
    # Django's authentication handles session automatically
    
    # Get donor statistics - this is a placeholder for your actual data fetching
    context = {
        'total_donated': '0 TZS',
        'donations_count': 0,
        'patients_count': 0,
        'impact_score': '0/100',
    }
    
    return render(request, 'donor/dashboard.html', context)

def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')

@login_required
def update_profile(request):
    """Handle profile updates"""
    if request.method == 'POST':
        # Update profile
        try:
            profile = request.user.profile
            # Update other fields as needed
            profile.save()
            
            messages.success(request, "Your profile has been updated successfully.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            
    return redirect('donor_profile')

def user_logout(request):
    """Handle user logout"""
    logout(request)
    return redirect('login')

@login_required
def profile(request):
    """
    Display the user's profile information
    """
    try:
        # Get user profile if it exists
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Create profile if it doesn't exist
        user_profile = Profile(user=request.user)
        user_profile.save()
        
    context = {
        'profile': user_profile,
        'user': request.user
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    """
    Allow users to edit their profile information
    """
    try:
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        user_profile = Profile(user=request.user)
        user_profile.save()
        
    if request.method == 'POST':
        # Process form submission
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # Update profile fields - adjust these based on your actual Profile model
        user_profile.phone = request.POST.get('phone', '')
        user_profile.address = request.POST.get('address', '')
        user_profile.city = request.POST.get('city', '')
        user_profile.bio = request.POST.get('bio', '')
        
        # Handle profile picture if included
        if 'profile_picture' in request.FILES:
            user_profile.profile_picture = request.FILES['profile_picture']
            
        user_profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
        
    context = {
        'profile': user_profile,
        'user': request.user
    }
    
    return render(request, 'users/edit_profile.html', context)

@login_required
def dashboard(request):
    """
    Display the user's dashboard with statistics and recent activity
    """
    # Get user donations
    from apps.donations.models import Donation
    
    donations = Donation.objects.filter(donor=request.user).order_by('-created_at')
    total_donated = sum(donation.amount for donation in donations if donation.status == 'Succeeded')
    
    # Get active cases the user has donated to
    active_cases = Donation.objects.filter(
        donor=request.user, 
        status='Succeeded'
    ).values_list('case', flat=True).distinct().count()
    
    context = {
        'donations': donations[:5],  # Most recent 5 donations
        'donation_count': donations.count(),
        'total_donated': f"{total_donated:,.0f} TZS",
        'active_cases': active_cases,
        'impact_score': calculate_impact_score(request.user),
    }

    return render(request, 'donations/dashboard.html', context)

def calculate_impact_score(user):
    """
    Calculate an impact score for the user based on their donation history
    """
    from apps.donations.models import Donation
    
    donations = Donation.objects.filter(donor=user, status='Succeeded')
    
    if not donations.exists():
        return "0/100"
    
    # Calculate based on number of donations, total amount, and consistency
    donation_count = donations.count()
    unique_cases = donations.values_list('case', flat=True).distinct().count()
    
    # Simple scoring algorithm - adjust as needed
    base_score = min(donation_count * 5, 40)  # Max 40 points from number of donations
    diversity_score = min(unique_cases * 10, 30)  # Max 30 points from unique cases
    consistency_score = min(donation_count, 3) * 10  # Max 30 points from consistency
    
    total_score = base_score + diversity_score + consistency_score
    final_score = min(total_score, 100)  # Cap at 100
    
    return f"{final_score}/100"

# Add these functions if they don't already exist
@login_required
def donor_profile(request):
    """View for donor profile"""
    return render(request, 'donations/profile.html')

@login_required
def donor_dashboard(request):
    """Donor dashboard view"""
    context = {
        'total_donated': '0 TZS',
        'donations_count': 0,
        'patients_count': 0,
        'impact_score': '0/100',
    }
    return render(request, 'donations/dashboard.html', context)
