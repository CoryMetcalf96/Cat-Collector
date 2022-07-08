import uuid
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from .models import Cat, Toy, Photo
from .forms import FeedingForm
import uuid
import boto3

S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'ga-catcollector-13'

# Create your views here.

# def home(request):
#     '''
#     this is where we return a response
#     in most cases we  would render a template
#     and we'll need some data for that template
#     '''
#     return HttpResponse('<h1> Hello World </h1>')

def home(request):
  return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')

def cats_index(request):
  cats = Cat.objects.all()
  return render(request, 'cats/index.html', { 'cats': cats })

def cats_detail(request, cat_id):
  cat = Cat.objects.get(id=cat_id)
  feeding_form = FeedingForm()
  toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))
  return render(request, 'cats/detail.html', {
    # include the cat and feeding_form in the context
    'cat': cat, 'feeding_form': feeding_form,
    'toys': toys_cat_doesnt_have
  })

def add_feeding(request, cat_id):
  # create the ModelForm using the data in request.POST
  form = FeedingForm(request.POST)
  # validate the form
  if form.is_valid():
    # don't save the form to the db until it
    # has the cat_id assigned
    new_feeding = form.save(commit=False)
    new_feeding.cat_id = cat_id
    new_feeding.save()
  return redirect('detail', cat_id=cat_id)

def assoc_toy(request, cat_id, toy_id):
  Cat.objects.get(id=cat_id).toys.add(toy_id)
  return redirect('detail', cat_id=cat_id)

def assoc_toy_delete(request, cat_id, toy_id):
  Cat.objects.get(id=cat_id).toys.remove(toy_id)
  return redirect('detail', cat_id=cat_id)

def add_photo(request, cat_id):
  # Attempt to collect the photo file data
  photo_file = request.FILES.get('photo-file', None)
  # Use conditional logic to determin if the file is present
  if photo_file:
    # Create a reference for the boto3 client
    s3 = boto3.client('s3')
    # Create a unique id for each photo file
    # funnt_cat.png = jdbw7f.png
    key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
    try:
      s3.upload_fileobj(photo_file, BUCKET, key)
      # take the exchanged url and save it to the database
      url = f"{S3_BASE_URL}{BUCKET}/{key}"
      # create photo instance with photo model and provide cat_id as foreign key value
      photo = Photo(url=url, cat_id=cat_id)
      # save the photo instance to your database
      photo.save()
    except Exception as error:
      print("Error uploading photo: ", error)
  return redirect('detail', cat_id=cat_id)
    

class CatCreate(CreateView):
  model = Cat
  fields = ['name', 'breed', 'description', 'age']
  success_url = '/cats/'

  # Assign the logged-in user as the user associated with the created cat
  def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

class CatUpdate(UpdateView):
  model = Cat
  # Let's disallow the renaming of a cat by excluding the name field!
  fields = [ 'breed', 'description', 'age']

class CatDelete(DeleteView):
  model = Cat
  success_url = '/cats/'

class ToyList(ListView):
  model = Toy
  template_name = 'toys/index.html'

class ToyDetail(DetailView):
  model = Toy
  template_name = 'toys/detail.html'

class ToyCreate(CreateView):
    model = Toy
    fields = ['name', 'color']


class ToyUpdate(UpdateView):
    model = Toy
    fields = ['name', 'color']


class ToyDelete(DeleteView):
    model = Toy
    success_url = '/toys/'