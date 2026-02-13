from django.shortcuts import render
from django.db.models import Avg, Prefetch
from django.views.generic import ListView
from .models import Category, FoodItem
from django.shortcuts import render, get_object_or_404, redirect

class MenuView(ListView):
    model = Category
    template_name = "menu/menu.html"
    context_object_name = "categories"

    def get_queryset(self):
        food_qs = FoodItem.objects.annotate(
            avg_rating=Avg("reservation_foods__reservation__comment__rating")
        )
        return Category.objects.prefetch_related(
            Prefetch("food_items", queryset=food_qs)
        )

    def  get_context_data(self ,**Kwargs):
        context = super().get_context_data(**Kwargs)
        context['all_category'] = Category.objects.all()
        context['select_category']  = self.request.get('category')
        return context
    
def food_detail(request , pk):
        food = get_object_or_404(FoodItem , pk =pk , is_availble=True)
        food.final_price = food.get_discounted_price()
        comments = comments.object.filter(reservation__reservation_foods__food_item=food
         ).select_related('user').prefetch_related('replies')
        
        context = {
        'food': food,
        'comments': comments,
    }
        return render(request, 'food_detail.html', context)




def add_to_reservation(request):
        if request.method =='Post':
            food_id =request.POST.get('food_id')
            quantitiy = request.POST.get('quantitiy')

        return redirect('menu')