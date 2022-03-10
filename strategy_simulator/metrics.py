import typing
from functools import wraps

if typing.TYPE_CHECKING:
    from .device import Device, AnyMessage


def _count_sent_messages(device: 'Device', msg: 'AnyMessage'):
    sent_messages = device._stats.setdefault('sent_messages', {})
    msg_type = str(type(msg))
    sent_messages[msg_type] = sent_messages.get(msg_type, 0) + 1


def counted(method):
    @wraps(method)
    def _impl(self: 'Device', *args, **kwargs):
        m_name = method.__name__
        if m_name in _COUNTER_IMPLS:
            _COUNTER_IMPLS[m_name](self, *args, **kwargs)
        else:
            stats = self._stats
            label = method.__name__
            stats[label] = stats.get(label, 0) + 1

        method(self, *args, **kwargs)

    return _impl


_COUNTER_IMPLS = {
    'send_message': _count_sent_messages
}
