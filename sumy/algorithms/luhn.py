# -*- coding: utf8 -*-

from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals

from .._compat import Counter
from ._method import AbstractSummarizationMethod


class LuhnMethod(AbstractSummarizationMethod):
    max_gap_size = 4
    significant_percentage = 1
    _stop_words = frozenset()

    @property
    def stop_words(self):
        return self._stop_words

    @stop_words.setter
    def stop_words(self, words):
        self._stop_words = frozenset(map(self.normalize_word, words))

    def __call__(self, sentences_count):
        words = self._get_significant_words(self._document.words)
        return self._get_best_sentences(self._document.sentences,
            sentences_count, self.rate_sentence, words)

    def _get_significant_words(self, words):
        words = tuple(self.stem_word(w) for w in words
            if w not in self._stop_words)

        # sort words by number of occurrences
        words = sorted(((c, w) for w, c in Counter(words).items()), reverse=True)

        # take only best `significant_percentage` % words
        best_words_count = int(len(words) * self.significant_percentage)
        return tuple(w for _, w in words)[:best_words_count]

    def rate_sentence(self, sentence, significant_stems):
        ratings = self._get_chunk_ratings(sentence, significant_stems)
        return max(ratings) if ratings else 0

    def _get_chunk_ratings(self, sentence, significant_stems):
        chunks = []
        NONSIGNIFICANT_CHUNK = [0]*self.max_gap_size

        in_chunk = False
        for order, word in enumerate(sentence.words):
            stem = self.stem_word(word)
            # new chunk
            if stem in significant_stems and not in_chunk:
                in_chunk = True
                chunks.append([1])
            # append word to chunk
            elif in_chunk:
                is_significant_word = int(stem in significant_stems)
                chunks[-1].append(is_significant_word)

            # end of chunk
            if chunks and chunks[-1][-self.max_gap_size:] == NONSIGNIFICANT_CHUNK:
                in_chunk = False

        return tuple(map(self._get_chunk_rating, chunks))

    def _get_chunk_rating(self, chunk):
        chunk = self.__remove_trailing_zeros(chunk)
        words_count = len(chunk)
        assert words_count > 0

        significant_words = sum(chunk)
        if significant_words == 1:
            return 0
        else:
            return significant_words**2 / words_count

    def __remove_trailing_zeros(self, collection):
        """Removes trailing zeroes from indexable collection of numbers"""
        index = len(collection) - 1
        while index >= 0 and collection[index] == 0:
            index -= 1

        return collection[:index + 1]
