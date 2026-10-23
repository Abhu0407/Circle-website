from django.db import migrations

# Old free-text interests -> community category keys. Unknown ones are dropped.
OLD_TO_NEW = {
    'sports': 'sports', 'sport': 'sports', 'cricket': 'sports', 'football': 'sports',
    'fitness': 'fitness', 'gym': 'fitness',
    'outdoors': 'outdoors', 'hiking': 'outdoors', 'trekking': 'outdoors',
    'adventure': 'adventure', 'travel': 'adventure',
    'tech': 'tech', 'technology': 'tech', 'coding': 'tech',
    'arts': 'arts', 'art': 'arts', 'photography': 'arts',
    'culture': 'culture',
    'music': 'music',
    'food': 'food', 'cooking': 'food',
    'drinks': 'drinks', 'coffee': 'drinks',
    'games': 'games', 'gaming': 'games',
    'learning': 'learning', 'books': 'learning', 'reading': 'learning',
    'education': 'education',
    'social': 'social', 'networking': 'networking',
    'health': 'health', 'wellness': 'wellness', 'yoga': 'wellness',
    'other': 'other',
}


def to_categories(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.exclude(interested_category=[]):
        keys = [OLD_TO_NEW.get(str(name).strip().lower()) for name in user.interested_category]
        user.interested_category = list(dict.fromkeys(k for k in keys if k))
        user.save(update_fields=['interested_category'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_interested_category_user_join_community_and_more'),
    ]

    operations = [
        migrations.RunPython(to_categories, migrations.RunPython.noop),
    ]
