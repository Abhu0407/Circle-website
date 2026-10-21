"""Keep chat in step with who belongs to which community.

Joining starts your read marker at the newest message (old history isn't
"unread"), and joining or leaving tells your open sockets to resubscribe,
so someone who leaves stops getting that chat's messages right away.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from . import services
from .models import Message

Membership = get_user_model().join_community.through


def _changed(reverse, instance, pk_set):
    """(user ids, community ids) touched by this change."""
    if reverse:  # community.members.add(users)
        return list(pk_set), [instance.pk]
    return [instance.pk], list(pk_set)  # user.join_community.add(communities)


@receiver(m2m_changed, sender=Membership)
def membership_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action == 'pre_clear':
        # clear() doesn't say who/what is removed, so note it first.
        if reverse:
            instance._chat_cleared = list(instance.members.values_list('pk', flat=True))
        else:
            instance._chat_cleared = list(instance.join_community.values_list('pk', flat=True))
        return
    if action == 'post_clear':
        pk_set = set(getattr(instance, '_chat_cleared', []))
    elif action not in ('post_add', 'post_remove'):
        return
    if not pk_set:
        return

    user_ids, community_ids = _changed(reverse, instance, pk_set)
    if action == 'post_add':
        services.start_reading_from_now(user_ids, community_ids)

    def notify():
        for user_id in user_ids:
            services.broadcast(services.user_group(user_id), {'type': 'chat.membership'})

    transaction.on_commit(notify)


@receiver(post_delete, sender=Message)
def delete_attachment(sender, instance, **kwargs):
    """Remove a message's file from disk with it (also when its community is deleted)."""
    if instance.attachment:
        name, storage = instance.attachment.name, instance.attachment.storage
        transaction.on_commit(lambda: storage.delete(name))
