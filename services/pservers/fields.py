from datetime import datetime
from motorengine.fields import DateTimeField

FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class PsDateTimeField(DateTimeField):

    def to_son(self, value):
        value = super(DateTimeField, self).to_son(value)
        return str(value)

    def from_son(self, value):
        value = super(DateTimeField, self).from_son(value)
        return datetime.strptime(value, FORMAT)
