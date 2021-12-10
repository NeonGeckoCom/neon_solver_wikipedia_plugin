# # NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# # All trademark and other rights reserved by their respective owners
# # Copyright 2008-2021 Neongecko.com Inc.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import simplematch
import wikipedia_for_humans
from neon_utterance_RAKE_plugin import RAKEExtractor

from neon_solvers import AbstractSolver


class WikipediaSolver(AbstractSolver):
    def __init__(self):
        super(WikipediaSolver, self).__init__(name="Wikipedia")
        self.rake = RAKEExtractor()
        self.cache.clear()

    def extract_keyword(self, query, lang="en"):
        query = query.lower()

        # regex from narrow to broader matches
        match = None
        if lang == "en":
            match = simplematch.match("who is {query}", query) or \
                    simplematch.match("what is {query}", query) or \
                    simplematch.match("when is {query}", query) or \
                    simplematch.match("tell me about {query}", query)
        # TODO localization
        if match:
            match = match["query"]
        else:
            # let's try to extract the best keyword and use it as query
            _, context = self.rake.transform([query], {"lang": lang})
            kwords = context.get("keywords")
            if not kwords:
                return query
            match = kwords[0][0]

        return match

    def get_secondary_search(self, query, lang="en"):
        if lang == "en":
            match = simplematch.match("what is the {subquery} of {query}", query)
            if match:
                return match["query"], match["subquery"]
        query = self.extract_keyword(query, lang)
        return query, None

    def extract_and_search(self, query, context=None):
        context = context or {}
        lang = context.get("lang") or self.default_lang
        lang = lang.split("-")[0]
        # extract the best keyword with some regexes or fallback to RAKE
        query = self.extract_keyword(query, lang)
        return self.search(query, context)

    # officially exported Solver methods
    def get_data(self, query, context=None):
        """
       query assured to be in self.default_lang
       return a dict response
       """
        context = context or {}
        lang = context.get("lang") or self.default_lang
        lang = lang.split("-")[0]

        page_data = wikipedia_for_humans.page_data(query, lang=lang)
        data = {
            "short_answer": wikipedia_for_humans.tldr(query, lang=lang),
            "summary": wikipedia_for_humans.summary(query, lang=lang)
        }
        if not page_data:
            query, subquery = self.get_secondary_search(query, lang)
            if subquery:
                data = {
                    "short_answer": wikipedia_for_humans.tldr_about(subquery, query, lang=lang),
                    "summary": wikipedia_for_humans.ask_about(subquery, query, lang=lang)
                }
            else:
                data = {
                    "short_answer": wikipedia_for_humans.tldr(query, lang=lang),
                    "summary": wikipedia_for_humans.summary(query, lang=lang)
                }
        page_data.update(data)
        return page_data

    def get_spoken_answer(self, query, context=None):
        data = self.extract_and_search(query, context)
        return  data.get("summary", "")

    def get_image(self, query, context=None):
        """
        query assured to be in self.default_lang
        return path/url to a single image to acompany spoken_answer
        """
        data = self.extract_and_search(query, context)
        try:
            return data["images"][0]
        except:
            return None

    def get_expanded_answer(self, query, context=None):
        """
        query assured to be in self.default_lang
        return a list of ordered steps to expand the answer, eg, "tell me more"

        {
            "title": "optional",
            "summary": "speak this",
            "img": "optional/path/or/url
        }

        """
        data = self.get_data(query, context)
        img = self.get_image(query, context)
        steps = [{
                "title": query,
                "summary": s,
                "img": img
            }
            # skip first sentence since it was retrieve in spoken answer
            for s in self.sentence_split(data["summary"], -1)[1:]]
        for sec in data.get("sections", []):
            steps += [{
                "title": sec.get("title") or query,
                "summary": s,
                "img": img
            }
            for s in self.sentence_split(sec["text"], -1)]
        return steps
