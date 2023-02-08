# external
from random import randint

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM

        tokenizer = AutoTokenizer.from_pretrained('tinkoff-ai/ruDialoGPT-medium')
        model = AutoModelForCausalLM.from_pretrained('tinkoff-ai/ruDialoGPT-medium')
        # inputs = tokenizer('@@ПЕРВЫЙ@@ привет @@ВТОРОЙ@@ привет @@ПЕРВЫЙ@@ как дела? @@ВТОРОЙ@@', return_tensors='pt')
        text = '@@ПЕРВЫЙ@@ Расскажи как начать флирт с девушкой @@ВТОРОЙ@@ Ну есть разные способы флирта @@ПЕРВЫЙ@@ Какие же? @@ВТОРОЙ@@'

        inputs = tokenizer(text, return_tensors='pt')
        generated_token_ids = model.generate(
            **inputs,
            top_k=10,
            top_p=0.95,
            num_beams=3,
            num_return_sequences=1,
            do_sample=True,
            no_repeat_ngram_size=2,
            temperature=1.2,
            repetition_penalty=1.2,
            length_penalty=1.0,
            eos_token_id=50257,
            max_new_tokens=randint(64, 128),
        )
        context_with_response = [tokenizer.decode(sample_token_ids) for sample_token_ids in generated_token_ids]
        print(context_with_response[0].replace(text, ''))
