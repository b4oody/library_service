from django.contrib import admin

from library.models import (
    User,
    Author,
    Genre,
    Book,
    Reservation,
    Purchase,
    LikedBook,

)

admin.site.register(User)
admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(Reservation)
admin.site.register(Purchase)
admin.site.register(LikedBook)
