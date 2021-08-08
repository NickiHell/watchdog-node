from tortoise import Model, fields


class Net(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64)
    path = fields.CharField(max_length=128)
