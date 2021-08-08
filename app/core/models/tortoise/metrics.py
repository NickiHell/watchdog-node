from tortoise import Model, fields


class NetReply(Model):
    id = fields.IntField(pk=True)
    text = fields.TextField()
    reply = fields.TextField()

    def __dict__(self):
        return {
            'id': self.id,
            'text': self.text,
            'reply': self.reply,
        }

    def __str__(self):
        return f'{self.text} -> {self.reply}'
