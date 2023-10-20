from speakerpy.lib_sl_text import SeleroText
from speakerpy.lib_speak import Speaker


if __name__ == '__main__':
    text = SeleroText('Я отправил "%s"' % msg.data)
    speaker = Speaker(model_id="ru_v3", language="ru", speaker="kelthuzad",
                      device="cpu")
    speaker.speak(text=text, sample_rate=48000, speed=1.0)
