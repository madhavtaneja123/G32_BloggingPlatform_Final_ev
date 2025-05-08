from django.shortcuts import render,redirect,get_object_or_404
from .models import Blog,Comment,Bookmark
from .forms import BlogForm,CommentForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .forms import ContactForm
from django.core.mail import send_mail
from django.conf import settings
from .forms import FeedbackForm
from .models import ContactMessage
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, ProfileUpdateForm
from django.contrib.auth.models import User 
from django.shortcuts import render,redirect
from django.contrib.auth import login
from .forms import RegisterForm
from django.contrib import messages
import requests
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator


def register_view(request):
    if request.method=='POST':
        form=RegisterForm(request.POST)
        if form.is_valid():
            user=form.save()
            login(request, user)
            return redirect('login')
    else:
        form=RegisterForm()
    return render(request, 'register.html',{'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('blog_create')
    return render(request,'login.html')

@login_required
def profile_view(request):
    return render(request, 'profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'edit_profile.html', {'form': form})

def blog_detail(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if request.method == 'POST':
        if 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.blog = blog
                new_comment.user = request.user
                new_comment.save()
                return redirect('blog_detail', blog_id=blog.id)
        elif 'delete_comment' in request.POST:
            comment_id = request.POST.get('comment_id')
            comment = get_object_or_404(Comment, id=comment_id)
            if request.user == comment.user or request.user.is_superuser:
                comment.delete()
            return redirect('blog_detail', blog_id=blog.id)
    comment_form = CommentForm()
    return render(request, 'blog_detail.html', {
        'blog': blog,
        'comment_form': comment_form
    })


def search_by_category(request):
    query = request.GET.get('category', '')
    blogs = Blog.objects.filter(category__icontains=query).order_by('-created_at') if query else []
    message = f"Showing results for category: {query}" if blogs else f"No blogs found in category: {query}" if query else "Please select a category to search"

    return render(request, 'categories.html', {
        'blogs': blogs,
        'query': query,
        'message': message,
        'category_choices': [choice[0] for choice in Blog.CATEGORY_CHOICES],  
    })

def search_by_tag(request):
    tag_query = request.GET.get('tag', '')
    blogs = Blog.objects.filter(tags__icontains=tag_query).order_by('-created_at') if tag_query else []
    message = f"Showing results for tag: {tag_query}" if blogs else f"No blogs found with tag: {tag_query}" if tag_query else "Please enter a tag to search"

    return render(request, 'categories.html', {
        'blogs': blogs,
        'tag_query': tag_query,
        'message': message,
        'category_choices': [choice[0] for choice in Blog.CATEGORY_CHOICES],  
        'query': '',
    })

@login_required
@csrf_exempt
@require_POST
def like_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    try:
        data = json.loads(request.body)
        if data.get('action') == 'like':
            blog.likes += 1
        else:
            blog.likes = max(0, blog.likes - 1)
        blog.save()
        return JsonResponse({'success': True, 'like_count': blog.likes})
    except json.JSONDecodeError:
        return JsonResponse({'success': False}, status=400)

@login_required
def blog_display(request):
    try:
        response = requests.get('http://localhost:5000/api/blogs')
        if response.status_code == 200:
            flask_blogs = response.json().get('blogs', [])
        else:
            messages.warning(request, "Could not fetch blogs from Flask API.")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Flask API connection error: {e}")

    return render(request, 'blog_display.html', {'blogs': flask_blogs})

@login_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['author_name'] == request.user.username:
                blog_data = {
                    "title": form.cleaned_data['title'],
                    "content": form.cleaned_data['content'],
                    "category": form.cleaned_data['category'],
                    "author_name": request.user.username,
                    "author_email": request.user.email,
                }

                try:
                    response = requests.post('http://localhost:5000/api/blogs', json=blog_data)
                    if response.status_code == 201:
                        flask_response = response.json()  
                        messages.success(request, "Blog created successfully!")
                        return redirect('blog_display')
                    else:
                        messages.error(request, f"Flask API failed: {response.text}")
                except requests.exceptions.RequestException as e:
                    messages.error(request, f"Could not connect to Flask API: {e}")
            else:
                messages.error(request, "You can only create a blog with your registered username.")
    else:
        form = BlogForm(initial={
            'author_name': request.user.username,
            'author_email': request.user.email,
        })
    return render(request, 'blog_create.html', {'form': form})


@login_required
def blog_edit(request, blog_id):
    try:
        response = requests.get(f'http://localhost:5000/api/blogs/{blog_id}')
        if response.status_code == 200:
            flask_blog = response.json()
        else:
            messages.error(request, f"Blog not found in Flask API.")
            return redirect('blog_display')
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Flask API error: {e}")
        return redirect('blog_display')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        author_name = request.POST.get('author_name')
        author_email = request.POST.get('author_email')

        flask_blog_id = flask_blog.get('id')
        flask_api_url = f'http://localhost:5000/api/blogs/{flask_blog_id}'
        data = {
            'title': title,
            'content': content,
            'author_name': author_name,
            'author_email': author_email,
        }

        try:
            response = requests.put(flask_api_url, json=data)
            if response.status_code == 200:
                messages.success(request, "Blog updated successfully in Flask!")
            else:
                messages.warning(request, f"Flask API update failed: {response.text}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Flask API error: {e}")

        return redirect('blog_display')

    return render(request, 'blog_edit.html', {'blog': flask_blog})

@login_required
@csrf_exempt
@require_POST
def delete_blog(request, blog_id):
    try:
        response = requests.delete(f'http://localhost:5000/api/blogs/{blog_id}')
        if response.status_code == 200:
            return JsonResponse({'success': True})
        elif response.status_code == 404:
            return JsonResponse({'success': True, 'warning': 'Blog already deleted from Flask'})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to delete from Flask'}, status=500)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            send_mail(
                subject=f"Message from {form.cleaned_data['name']}",
                message=form.cleaned_data['message'],
                from_email=form.cleaned_data['email'],
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
            )
            return render(request, 'contact.html')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def about_view(request):
    return render(request, 'about.html')

def contact_page(request):
    return render(request, 'contact.html')

def privacy_view(request):
    return render(request, 'privacy_policy.html')

def index_view(request):
    return render(request, 'index.html')

@login_required
def feedback_thanks(request):
    return render(request, 'feedback_thanks.html')

def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            rating = form.cleaned_data['rating']
            feedback_message = form.cleaned_data['feedback_message']

            try:
                response = requests.post('http://localhost:5000/api/feedbacks', json={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'rating': rating,
                    'feedback_message': feedback_message
                })
                if response.status_code == 201:
                    return redirect('feedback_thanks')
                else:
                    messages.error(request, "Flask API failed to save feedback.")
            except requests.exceptions.RequestException as e:
                messages.error(request, f"Could not connect to Flask API: {e}")
    else:
        form = FeedbackForm()

    return render(request, 'feedback.html', {'form': form})

@csrf_exempt
def contact_view(request):
    if request.method=='POST':
        name=request.POST.get('name')
        email=request.POST.get('email')
        message=request.POST.get('message')

        ContactMessage.objects.create(name=name,email=email,message=message)
        return redirect('thank_you')

    return render(request,'contact.html')

def display_messages(request):
    messages=ContactMessage.objects.all().order_by('-submitted_at')
    return render(request,'all_messages.html',{'messages': messages})

def thank_you(request):
    return render(request,'thank_you.html')

@login_required
def add_bookmark(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if not Bookmark.objects.filter(blog=blog).exists():
        Bookmark.objects.create(blog=blog)

    return redirect('bookmark_list')

@login_required
def remove_bookmark(request, blog_id):
    bookmark = Bookmark.objects.filter(blog_id=blog_id).first()
    if bookmark:
        bookmark.delete()
    return redirect('bookmark_list')


@login_required
def bookmark_list(request):
    bookmarks = Bookmark.objects.select_related('blog')
    return render(request, 'bookmark_list.html', {'bookmarks': bookmarks})

def logout_view(request):
    logout(request)
    return redirect('login')