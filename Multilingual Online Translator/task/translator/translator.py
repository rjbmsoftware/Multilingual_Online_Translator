import re
import requests
import sys
from bs4 import BeautifulSoup


class Translator:
    supported_languages = (
        'Arabic', 'German', 'English', 'Spanish', 'French',
        'Hebrew', 'Japanese', 'Dutch', 'Polish', 'Portuguese',
        'Romanian', 'Russian', 'Turkish',
    )

    def __init__(self, lang_from, lang_to=None):
        self.lang_from = self.supported_languages[lang_from].lower()
        self.lang_to = self.supported_languages[lang_to].lower() if lang_to else None

    @staticmethod
    def translation_text_tidy(trans_text: str) -> str:
        formatted = trans_text.replace(',', '').replace('"', '')
        pattern = r'^(\S+ ?){5}'
        match = re.search(pattern, formatted)
        if match:
            return match.group(0).strip() + '...'
        else:
            return formatted

    def get_content(self, word, output_language=None):
        translate_to_language = self.lang_to if output_language is None else output_language
        service_url = 'https://context.reverso.net/translation'
        url = f'{service_url}/{self.lang_from}-{translate_to_language}/{word}'
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            print(f'Sorry unable to find {word}')
            sys.exit()
        except requests.exceptions.RequestException:
            print('Something wrong with your internet connection')
            sys.exit()

        return response

    @staticmethod
    def direct_translations(soup: BeautifulSoup, limit=1):
        value = soup.find(id='translations-content').findChildren('a', recursive=False)
        translations = [child.text.strip() for child in value]

        return translations[:limit]

    def print_five_example_uses(self, soup: BeautifulSoup):
        print()
        print(self.lang_to.title(), 'Examples')
        examples = soup.find(id='examples-content').findChildren('span', attrs={'class': 'text'}, recursive=True)
        for i in range(0, 20, 2):
            print(self.translation_text_tidy(examples[i].text.strip() + ':'))
            print(self.translation_text_tidy(examples[i + 1].text.strip()))

    @staticmethod
    def translate_all_template(lang, direct, example_from, example_to) -> []:
        output = [f'{lang} Translations:', '\n', direct, '\n', '\n',
                  f'{lang.title()} examples:', '\n', example_from, '\n', example_to,
                  '\n', '\n']

        return output

    def translate_all(self, word):
        output = []
        for supported_language in self.supported_languages:
            if supported_language.lower() == self.lang_from:
                continue

            response = self.get_content(word, supported_language.lower())
            soup = BeautifulSoup(response.text, 'html.parser')
            direct_trans = self.direct_translations(soup)[0]
            examples = soup.find(id='examples-content').findChildren('span', attrs={'class': 'text'}, recursive=True)
            example_from = examples[0].text.strip() + ':'
            example_to = examples[1].text.strip()

            output += self.translate_all_template(supported_language, direct_trans, example_from, example_to)

        with open(f'{word}.txt', 'w') as translations_file:
            translations_file.writelines(output)
        print(*output, sep='')

    def translate(self, word):
        if self.lang_to is None:
            return self.translate_all(word)

        response = self.get_content(word)
        print(response.status_code, response.reason)
        print()
        soup = BeautifulSoup(response.text, 'html.parser')
        print('Context example:')
        print()
        print(self.lang_to, 'Translations:')
        print(*self.direct_translations(soup, 5), sep='\n')
        self.print_five_example_uses(soup)


def validate_translator(value: int or str, another_value=None) -> Translator:
    return TranslatorValidator.factory(value, another_value)


class TranslatorValidator:
    @staticmethod
    def factory(lang: int or str, second_lang=None) -> Translator:
        second = None
        try:
            if isinstance(lang, int) and TranslatorValidator.in_range(lang):
                first = lang
            else:
                first = TranslatorValidator.in_supported(lang)
            if second_lang:
                if isinstance(lang, int) and TranslatorValidator.in_range(second_lang):
                    second = second_lang
                else:
                    second = TranslatorValidator.in_supported(second_lang)

            if second_lang:
                return Translator(first, second)
            else:
                return Translator(first)
        except ValueError as ve:
            print(ve)
            sys.exit()

    @staticmethod
    def in_range(value: int) -> bool:
        if 0 <= value < len(Translator.supported_languages):
            return True
        raise ValueError('Sorry unsupported language')

    @staticmethod
    def in_supported(lang) -> int:
        lang = lang.title()
        if lang in Translator.supported_languages:
            return Translator.supported_languages.index(lang)
        raise ValueError(f"Sorry, the program doesn't support {lang}")


if __name__ == '__main__':
    if len(sys.argv) == 4:  # has been called from cli
        input_lang = sys.argv[1]
        if sys.argv[2] == 'all':
            output_lang = 0
        else:
            output_lang = sys.argv[2]
        text = sys.argv[3]
    else:
        print("Hello, you're welcome to the translator. Translator supports:")
        for index, language in enumerate(Translator.supported_languages, start=1):
            print(f'{index}. {language}')

        input_lang = int(input('Type the number of your language:')) - 1
        instruction = "Type the number of a language you want to translate to or '0' to translate to all languages:"
        output_lang = int(input(instruction)) - 1
        text = input('Type the word you want to translate:')

    if output_lang == 0:
        translator = validate_translator(input_lang)
    else:
        translator = validate_translator(input_lang, output_lang)

    translator.translate(text)
