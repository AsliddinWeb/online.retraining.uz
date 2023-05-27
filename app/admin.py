from django.contrib import admin

from .models import *

class WhatYouLearnTabularInline(admin.TabularInline):
    model = WhatYouLearn

class RequirementsTabularInline(admin.TabularInline):
    model = Requirements

class Video_TabularInline(admin.TabularInline):
    model = Video

class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', )}
    inlines = (WhatYouLearnTabularInline, RequirementsTabularInline, Video_TabularInline)



admin.site.register(Categories)
admin.site.register(Author)
admin.site.register(Course, CourseAdmin)
admin.site.register(Level)



admin.site.register(WhatYouLearn)
admin.site.register(Requirements)

admin.site.register(Lesson)
admin.site.register(Video)
admin.site.register(Language)
admin.site.register(UserCourse)
admin.site.register(Payment)