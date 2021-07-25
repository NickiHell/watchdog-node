from loguru import logger
from transformers import GPT2LMHeadModel, GPT2Tokenizer


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
        self._num_beams: None = None
        self._no_repeat_ngram_size: int = 3

    def _generate(self, text: str, max_length: int = None) -> str:
        input_ids = self._tokinizer.encode(text, return_tensors="pt")
        out = self._model.generate(
            input_ids,
            max_length=max_length or self._max_length,
            repetition_penalty=self._repetition_penalty,
            do_sample=True,
            top_k=self._top_k, top_p=self._top_p, temperature=self._temperature,
            num_beams=self._num_beams, no_repeat_ngram_size=self._no_repeat_ngram_size
        )
        return list(map(self._tokinizer.decode, out))[0]

    def __call__(self, *args, **kwargs):
        logger.info('Model call')
        message: str = kwargs.get('message', 'test')
        max_length: int = kwargs.get('max_length', self._max_length)
        output: str = self._generate(message, max_length)
        logger.info(f'Message: {message} -> {output}')
        return output
