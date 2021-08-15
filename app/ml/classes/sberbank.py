import json
import random

from transformers import GPT2LMHeadModel, GPT2Tokenizer


class SmallGPT3:
    def __init__(self, model_name: str, params: dict = None):
        self._model_name: str = model_name
        self._model: GPT2LMHeadModel = GPT2LMHeadModel.from_pretrained(self._model_name)
        self._tokinizer: GPT2Tokenizer = GPT2Tokenizer.from_pretrained(self._model_name)
        self._memory = []
        self._params: dict = params or {
            'top_k': 5,
            'top_p': 0.95,
            'temperature': 0.85,
            'repetition_penalty': 3.0,
            'max_length': 128,
            'num_beams': 3,
            'do_sample': True,
            'no_repeat_ngram_size': 3,
            'bos_token_id': self._tokinizer.encode('Я')[0],
            'eos_token_id': self._tokinizer.encode('.')[0],
            'length_penalty': 0.95,
            'num_return_sequences': random.randint(1, 5),
        }

    def _create_dataset(self):
        with open('result.json', 'r') as file:
            data: dict = json.loads(file.read())['messages']
        replies = tuple(x for x in data if
                        x['type'] == 'message' and x['text'] != '' and x.get('reply_to_message_id') and isinstance(
                            x['text'], str))
        messages = tuple(x for x in data if x['type'] == 'message' and x['text'] != '' and isinstance(x['text'], str))
        with open('train.txt', 'w') as train:
            train.write('\n'.join([x['text'] for x in messages]))

        with open('valid.txt', 'w') as valid:
            valid.write('\n'.join([x['text'] for x in replies]))

    def _generate(self, text: str) -> str:
        input_ids = self._tokinizer.encode(text, return_tensors="pt")
        out = self._model.generate(
            input_ids,
            **self._params,
        )
        return [self._tokinizer.decode(x) for x in out][0]

    @staticmethod
    def _text_post_processing(message: str, text: str) -> str:
        text: str = text.replace(message, '')
        text: str = ' '.join(text.split()).strip().capitalize()
        return text

    def __call__(self, *args, **kwargs):
        message: str = args[0]
        output: str = self._text_post_processing(message, self._generate(message))
        return output
