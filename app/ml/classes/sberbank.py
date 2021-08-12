from loguru import logger
from transformers import GPT2LMHeadModel, GPT2Tokenizer, GPT2TokenizerFast


class SberbankSmallGPT3:
    """
    GPT3 от Сбера маленького размера
    """

    def __init__(self, model_name: str):
        self._model_name: str = model_name
        self._tokinizer: GPT2Tokenizer = GPT2Tokenizer.from_pretrained(self._model_name)
        self._model: GPT2LMHeadModel = GPT2LMHeadModel.from_pretrained(self._model_name)
        self._top_k: int = 5
        self._top_p: float = 0.95
        self._temperature: int = 1
        self._repetition_penalty = 5.0
        self._max_length: int = 64
        self._num_beams: None = 1
        self._no_repeat_ngram_size: int = 5

    def _tuning(self):
        pass

    def _generate(self, text: str, max_length: int = None) -> str:
        input_ids = self._tokinizer.encode(text, return_tensors="pt")
        out = self._model.generate(
            input_ids,
            max_length=max_length or self._max_length,
            repetition_penalty=self._repetition_penalty,
            do_sample=True,
            bos_token_id=1358,
            # unk_token=24,
            eos_token_id=18,
            pad_token_id=0,
            top_k=self._top_k, top_p=self._top_p, temperature=self._temperature,
            num_beams=self._num_beams, no_repeat_ngram_size=self._no_repeat_ngram_size
        )
        return list(map(self._tokinizer.decode, out))[0]

    @staticmethod
    def _text_post_processing(message: str, text: str) -> str:
        text: str = text.replace(message, '').strip().capitalize()
        text: str = text[1:] if text[0] == ',' else text
        text: str = ' '.join([x for x in text.split() if x])
        return text

    def __call__(self, *args, **kwargs):
        message: str = kwargs.get('message', 'test')
        max_length: int = kwargs.get('max_length', self._max_length)
        output: str = self._text_post_processing(message, self._generate(message, max_length))
        return output
