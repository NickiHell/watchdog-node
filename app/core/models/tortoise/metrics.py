from tortoise import Model, fields


class NetReply(Model):
    id = fields.IntField(pk=True)
    text = fields.TextField()
    reply = fields.TextField()

    def __str__(self):
        return f'{self.text} -> {self.reply}'
