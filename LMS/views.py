from time import time
import razorpay
from django.views.decorators.csrf import csrf_exempt

from .settings import KEY_ID, KEY_SECRET

from django.shortcuts import redirect, render
from app.models import Categories, Course, Level, Lesson, Video, UserCourse, Payment
from django.db.models import Sum
from django.contrib import messages

# AJAX
from django.template.loader import render_to_string
from django.http import JsonResponse

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

def BASE(request):
    return render(request, 'base.html')


def HOME(request):
    category = Categories.objects.all().order_by('id')[0:5]
    course = Course.objects.filter(status="PUBLISH").order_by('-id')

    ctx = {
        'category': category,
        'course': course,
    }

    return render(request, 'Main/home.html', ctx)


def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    level = Level.objects.all()
    course = Course.objects.all()
    FreeCourse_count = Course.objects.filter(price = 0).count()
    PaidCourse_count = course.count() - FreeCourse_count

    ctx = {
        'category': category,
        'level': level,
        'course': course,
        'FreeCourse_count': FreeCourse_count,
        'PaidCourse_count': PaidCourse_count
    }

    return render(request, 'Main/single_course.html', ctx)

def CONTACT_US(request):
    category = Categories.get_all_category(Categories)

    ctx = {
        'category': category
    }

    return render(request, 'Main/contact_us.html', ctx)

def ABOUT_US(request):
    category = Categories.get_all_category(Categories)

    ctx = {
        'category': category
    }
    return render(request, 'Main/about_us.html', ctx)

def filter_data(request):
    categories = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')


    if price == ['pricefree']:
       course = Course.objects.filter(price=0)
    elif price == ['pricepaid']:
       course = Course.objects.filter(price__gte=1)
    elif price == ['priceall']:
       course = Course.objects.all()
    elif categories:
       course = Course.objects.filter(category__id__in=categories).order_by('-id')
    elif level:
       course = Course.objects.filter(level__id__in = level).order_by('-id')
    else:
       course = Course.objects.all().order_by('-id')


    t = render_to_string('ajax/course.html', {'course': course})

    return JsonResponse({'data': t})

def SEARCH_COURSE(request):

    category = Categories.get_all_category(Categories)

    query = request.GET['query']
    course = Course.objects.filter(title__icontains = query)
    ctx = {
        'category': category,

        'course': course,
    }
    return render(request, 'search/search.html', ctx)

def COURSE_DETAILS(request, slug):
    category = Categories.get_all_category(Categories)

    course = Course.objects.filter(slug=slug)
    time_duration = Video.objects.filter(course__slug=slug).aggregate(sum=Sum('time_duration'))

    try:
        check_enroll = UserCourse.objects.get(user=request.user, course=course.first())

    except:
        check_enroll = None

    if course.exists():
        course = course.first()
    else:
        return redirect('404')

    ctx = {
        'category': category,
        'course': course,
        'time_duration': time_duration,
        'check_enroll': check_enroll
    }

    return render(request, 'course/course_details.html', ctx)

def PAGE_NOT_FOUND(request):
    category = Categories.get_all_category(Categories)

    ctx = {
        'category': category
    }
    return render(request, 'error/404.html', ctx)

def CHECKOUT(request, slug):
    course = Course.objects.get(slug=slug)
    action = request.GET.get('action')
    order = None

    if course.price == 0:
        course = UserCourse(
            user=request.user,
            course=course
        )
        course.save()
        messages.success(request, "Tabriklaymiz! Siz kursga muvaffaqqiyatli ro'yhatdan o'tdingiz!")
        return redirect('my_course')
    elif action == 'create_payment':
        if request.method == "POST":
            first_name = request.POST.get('billing_first_name')
            last_name = request.POST.get('billing_last_name')
            country = request.POST.get('billing_country')
            address_1 = request.POST.get('billing_address_1')
            address_2 = request.POST.get('billing_address_2')
            city = request.POST.get('billing_city')
            state = request.POST.get('billing_state')
            postcode = request.POST.get('billing_postcode')
            postcode = request.POST.get('billing_postcode')
            phone = request.POST.get('billing_phone')
            email = request.POST.get('billing_email')
            order_comments = request.POST.get('order_comments')

            amount_cal = course.price - (course.price * course.discount / 100)
            amount = int(amount_cal) * 100
            currency = "INR"
            notes = {
                "name": f"{first_name} {last_name}",
                "country": country,
                "address": f"{address_1} {address_2}",
                "city": city,
                "state": state,
                "postcode": postcode,
                "phone": phone,
                "email": email,
                "order_comments": order_comments
            }

            receipt = f"Skola - {int(time())}"
            order = client.order.create(
                {
                    'receipt': receipt,
                    'notes': notes,
                    'amount': amount,
                    'currency': currency,
                }
            )
            payment = Payment(
                course=course,
                user=request.user,
                order_id=order.get('id')
            )
            payment.save()

    ctx = {
        'course': course,
        'order': order
    }

    return render(request, 'checkout/checkout.html', ctx)

def MY_COURSE(request):
    course = UserCourse.objects.filter(user=request.user)

    ctx = {
        'course': course
    }

    return render(request, 'course/my_course.html', ctx)


@csrf_exempt
def VERIFY_PAYMENT(request):
    if request.method == "POST":
        data = request.POST
        print(data)
        try:
            client.utility.verify_payment_signature(data)
            razorpay_order_id = data['razorpay_order_id']
            razorpay_payment_id = data['razorpay_order_id']

            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.status = True

            usercourse = UserCourse(
                user = payment.user,
                course = payment.course,
            )
            usercourse.save()
            payment.user_course = usercourse
            payment.save()

            ctx = {
                'data': data,
                'payment': payment
            }
            return render(request, 'verify_payment/success.html', ctx)
        except:
            return render(request, 'verify_payment/fail.html', ctx)


def WATCH_COURSE(request, slug):
    lecture = request.GET.get('lecture')
    print(lecture)
    course_id = Course.objects.get(slug=slug)
    course = Course.objects.filter(slug=slug)

    try:
        check_enroll = UserCourse.objects.get(user=request.user, course=course_id)
        video = Video.objects.get(id=lecture)
        if course.exists():
            course = course.first()
        else:
            return redirect('404')
    except UserCourse.DoesNotExist:
        return redirect('404')

    ctx = {
        'course': course,
        'video': video,
        'lecture': lecture
    }

    return render(request, 'course/watch_list.html', ctx)


    return render(request, 'course/watch-course.html')