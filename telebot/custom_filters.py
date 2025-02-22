from abc import ABC
from typing import Optional, Union

from telebot import types


class SimpleCustomFilter(ABC):
    """
    Simple Custom Filter base class.
    Create child class with check() method.
    Accepts only message, returns bool value, that is compared with given in handler.
    """

    def check(self, message):
        """
        Perform a check.
        """
        pass


class AdvancedCustomFilter(ABC):
    """
    Simple Custom Filter base class.
    Create child class with check() method.
    Accepts two parameters, returns bool: True - filter passed, False - filter failed.
    message: Message class
    text: Filter value given in handler
    """

    def check(self, message, text):
        """
        Perform a check.
        """
        pass


class TextFilter:
    """
    Advanced text filter to check (types.Message, types.CallbackQuery, types.InlineQuery, types.Poll)

    example of usage is in examples/custom_filters/advanced_text_filter.py
    """

    def __init__(self,
                 equals: Optional[str] = None,
                 contains: Optional[Union[list, tuple]] = None,
                 starts_with: Optional[Union[str, list, tuple]] = None,
                 ends_with: Optional[Union[str, list, tuple]] = None,
                 ignore_case: bool = False):

        """
        :param equals: string, True if object's text is equal to passed string
        :param contains: list[str] or tuple[str], True if any string element of iterable is in text
        :param starts_with: string, True if object's text starts with passed string
        :param ends_with: string, True if object's text starts with passed string
        :param ignore_case: bool (default False), case insensitive
        """

        to_check = sum((pattern is not None for pattern in (equals, contains, starts_with, ends_with)))
        if to_check == 0:
            raise ValueError('None of the check modes was specified')

        self.equals = equals
        self.contains = self._check_iterable(contains, filter_name='contains')
        self.starts_with = self._check_iterable(starts_with, filter_name='starts_with')
        self.ends_with = self._check_iterable(ends_with, filter_name='ends_with')
        self.ignore_case = ignore_case

    def _check_iterable(self, iterable, filter_name: str):
        if not iterable:
            pass
        elif not isinstance(iterable, str) and not isinstance(iterable, list) and not isinstance(iterable, tuple):
            raise ValueError(f"Incorrect value of {filter_name!r}")
        elif isinstance(iterable, str):
            iterable = [iterable]
        elif isinstance(iterable, list) or isinstance(iterable, tuple):
            iterable = [i for i in iterable if isinstance(i, str)]
        return iterable

    def check(self, obj: Union[types.Message, types.CallbackQuery, types.InlineQuery, types.Poll]):

        if isinstance(obj, types.Poll):
            text = obj.question
        elif isinstance(obj, types.Message):
            text = obj.text or obj.caption
        elif isinstance(obj, types.CallbackQuery):
            text = obj.data
        elif isinstance(obj, types.InlineQuery):
            text = obj.query
        else:
            return False

        if self.ignore_case:
            text = text.lower()

            if self.equals:
                self.equals = self.equals.lower()
            elif self.contains:
                self.contains = tuple(map(str.lower, self.contains))
            elif self.starts_with:
                self.starts_with = tuple(map(str.lower, self.starts_with))
            elif self.ends_with:
                self.ends_with = tuple(map(str.lower, self.ends_with))

        if self.equals:
            result = self.equals == text
            if result:
                return True
            elif not result and not any((self.contains, self.starts_with, self.ends_with)):
                return False

        if self.contains:
            result = any([i in text for i in self.contains])
            if result:
                return True
            elif not result and not any((self.starts_with, self.ends_with)):
                return False

        if self.starts_with:
            result = any([text.startswith(i) for i in self.starts_with])
            if result:
                return True
            elif not result and not self.ends_with:
                return False

        if self.ends_with:
            return any([text.endswith(i) for i in self.ends_with])

        return False

class TextMatchFilter(AdvancedCustomFilter):
    """
    Filter to check Text message.
    key: text

    Example:
    @bot.message_handler(text=['account'])
    """

    key = 'text'

    def check(self, message, text):
        if isinstance(text, TextFilter):
            return text.check(message)
        elif type(text) is list:
            return message.text in text
        else:
            return text == message.text


class TextContainsFilter(AdvancedCustomFilter):
    """
    Filter to check Text message.
    key: text

    Example:
    # Will respond if any message.text contains word 'account'
    @bot.message_handler(text_contains=['account'])
    """

    key = 'text_contains'

    def check(self, message, text):
        if not isinstance(text, str) and not isinstance(text, list) and not isinstance(text, tuple):
            raise ValueError("Incorrect text_contains value")
        elif isinstance(text, str):
            text = [text]
        elif isinstance(text, list) or isinstance(text, tuple):
            text = [i for i in text if isinstance(i, str)]

        return any([i in message.text for i in text])


class TextStartsFilter(AdvancedCustomFilter):
    """
    Filter to check whether message starts with some text.

    Example:
    # Will work if message.text starts with 'Sir'.
    @bot.message_handler(text_startswith='Sir')
    """

    key = 'text_startswith'

    def check(self, message, text):
        return message.text.startswith(text)


class ChatFilter(AdvancedCustomFilter):
    """
    Check whether chat_id corresponds to given chat_id.

    Example:
    @bot.message_handler(chat_id=[99999])
    """

    key = 'chat_id'

    def check(self, message, text):
        return message.chat.id in text


class ForwardFilter(SimpleCustomFilter):
    """
    Check whether message was forwarded from channel or group.

    Example:

    @bot.message_handler(is_forwarded=True)
    """

    key = 'is_forwarded'

    def check(self, message):
        return message.forward_from_chat is not None


class IsReplyFilter(SimpleCustomFilter):
    """
    Check whether message is a reply.

    Example:

    @bot.message_handler(is_reply=True)
    """

    key = 'is_reply'

    def check(self, message):
        return message.reply_to_message is not None


class LanguageFilter(AdvancedCustomFilter):
    """
    Check users language_code.

    Example:

    @bot.message_handler(language_code=['ru'])
    """

    key = 'language_code'

    def check(self, message, text):
        if type(text) is list:
            return message.from_user.language_code in text
        else:
            return message.from_user.language_code == text


class IsAdminFilter(SimpleCustomFilter):
    """
    Check whether the user is administrator / owner of the chat.

    Example:
    @bot.message_handler(chat_types=['supergroup'], is_chat_admin=True)
    """

    key = 'is_chat_admin'

    def __init__(self, bot):
        self._bot = bot

    def check(self, message):
        return self._bot.get_chat_member(message.chat.id, message.from_user.id).status in ['creator', 'administrator']


class StateFilter(AdvancedCustomFilter):
    """
    Filter to check state.

    Example:
    @bot.message_handler(state=1)
    """

    def __init__(self, bot):
        self.bot = bot

    key = 'state'

    def check(self, message, text):
        if text == '*': return True

        if isinstance(text, list):
            new_text = [i.name for i in text]
            text = new_text
        elif isinstance(text, object):
            text = text.name
        if message.chat.type == 'group':
            group_state = self.bot.current_states.get_state(message.chat.id, message.from_user.id)
            if group_state == text:
                return True
            elif group_state in text and type(text) is list:
                return True


        else:
            user_state = self.bot.current_states.get_state(message.chat.id, message.from_user.id)
            if user_state == text:
                return True
            elif type(text) is list and user_state in text:
                return True


class IsDigitFilter(SimpleCustomFilter):
    """
    Filter to check whether the string is made up of only digits.

    Example:
    @bot.message_handler(is_digit=True)
    """
    key = 'is_digit'

    def check(self, message):
        return message.text.isdigit()
