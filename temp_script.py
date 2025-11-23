from users.models import Role

for r in Role.objects.all():
    print(r.id, r.name)
