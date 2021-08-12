from tortoise import Model, fields


class Net(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64)
    path = fields.CharField(max_length=128)


class Dataset(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=64)
    data = fields.JSONField()


class QuestionsAnswers(Model):
    id = fields.IntField(pk=True)
    message = fields.TextField()
    reply = fields.TextField()

    def __dict__(self):
        return {
            'id': self.id,
            'message': self.message,
            'reply': self.reply,
        }

    def __str__(self):
        return f'{self.message} -> {self.reply}'
