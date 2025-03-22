import nltk
from nltk import sent_tokenize, word_tokenize
from nltk import pos_tag, ne_chunk
from nltk.tree import Tree
from nltk.corpus import wordnet, stopwords
import random
import sys
import re
from string import punctuation


class EnhancedQAGenerator:
    """An enhanced question-answer generator using NLTK with multiple question types."""
    
    def __init__(self):
        # Download necessary NLTK resources
        nltk.download('punkt', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('maxent_ne_chunker', quiet=True)
        nltk.download('words', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('stopwords', quiet=True)

        self.stopwords = set(stopwords.words('english'))

    def extract_entities(self, sentence):
        """Extract named entities from a sentence."""
        chunks = ne_chunk(pos_tag(word_tokenize(sentence)))
        entities = []

        for chunk in chunks:
            if isinstance(chunk, Tree):
                entity_type = chunk.label()
                entity_text = " ".join([word for word, tag in chunk.leaves()])
                entities.append((entity_text, entity_type))

        return entities

    def get_key_nouns(self, pos_tags):
        """Get the key nouns from POS tagged words."""
        nouns = [word for word, tag in pos_tags if tag.startswith('NN') and word.lower() not in self.stopwords]
        return nouns

    def get_key_verbs(self, pos_tags):
        """Get the key verbs from POS tagged words."""
        verbs = [word for word, tag in pos_tags if tag.startswith('VB') and word.lower() not in self.stopwords]
        return verbs

    def get_key_adjectives(self, pos_tags):
        """Get the key adjectives from POS tagged words."""
        adjectives = [word for word, tag in pos_tags if tag.startswith('JJ') and word.lower() not in self.stopwords]
        return adjectives

    def clean_answer(self, text):
        """Clean the answer text for better readability."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def generate_definition_question(self, sentence, pos_tags):
        """Generate a definition-style question."""
        nouns = self.get_key_nouns(pos_tags)
        if nouns:
            target_noun = random.choice(nouns)
            question = f"What is {target_noun}?"
            return {'question': question, 'answer': self.clean_answer(sentence)}
        return None

    def generate_who_question(self, sentence, entities):
        """Generate a who question based on named entities."""
        person_entities = [entity for entity, entity_type in entities if entity_type == 'PERSON']

        if person_entities:
            target_person = random.choice(person_entities)
            # Replace the person's name with "who" to create the question
            pattern = re.compile(r'\b' + re.escape(target_person) + r'\b', re.IGNORECASE)
            question_text = pattern.sub("who", sentence, 1) + "?"

            # Clean up question formatting
            question_text = question_text[0].upper() + question_text[1:]
            question_text = re.sub(r'[\.\?!]\s*\?$', '?', question_text)

            return {'question': question_text, 'answer': self.clean_answer(sentence)}
        return None

    def generate_where_question(self, sentence, entities):
        """Generate a where question based on location entities."""
        location_entities = [entity for entity, entity_type in entities if entity_type in ['GPE', 'LOCATION']]

        if location_entities:
            target_location = random.choice(location_entities)
            # Replace the location with "where" to create the question
            pattern = re.compile(r'\b' + re.escape(target_location) + r'\b', re.IGNORECASE)
            question_text = pattern.sub("where", sentence, 1) + "?"

            # Clean up question formatting
            question_text = question_text[0].upper() + question_text[1:]
            question_text = re.sub(r'[\.\?!]\s*\?$', '?', question_text)

            return {'question': question_text, 'answer': self.clean_answer(sentence)}
        return None

    def generate_when_question(self, sentence, pos_tags):
        """Generate a when question based on time expressions."""
        # Simple detection of time expressions
        time_indicators = ['yesterday', 'today', 'tomorrow', 'morning', 'afternoon', 'evening',
                           'night', 'January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December',
                           'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
                           'last week', 'next week', 'last month', 'next month',
                           'year', 'decade', 'century']

        words = [word for word, _ in pos_tags]
        for indicator in time_indicators:
            if indicator.lower() in [w.lower() for w in words]:
                question_text = sentence.replace(indicator, "when") + "?"

                # Clean up question formatting
                question_text = question_text[0].upper() + question_text[1:]
                question_text = re.sub(r'[\.\?!]\s*\?$', '?', question_text)

                return {'question': question_text, 'answer': self.clean_answer(sentence)}
        return None

    def generate_how_question(self, sentence, pos_tags):
        """Generate a how question based on adverbs."""
        adverbs = [word for word, tag in pos_tags if tag.startswith('RB') and word.lower() not in self.stopwords]

        if adverbs:
            target_adverb = random.choice(adverbs)
            question_text = sentence.replace(target_adverb, "how") + "?"

            # Clean up question formatting
            question_text = question_text[0].upper() + question_text[1:]
            question_text = re.sub(r'[\.\?!]\s*\?$', '?', question_text)

            return {'question': question_text, 'answer': self.clean_answer(sentence)}
        return None

    def generate_why_question(self, sentence):
        """Generate a why question for sentences with causal relationships."""
        causal_indicators = ['because', 'since', 'as', 'due to', 'caused by', 'result of']

        for indicator in causal_indicators:
            if indicator in sentence.lower():
                question = f"Why {sentence.replace(indicator, '').strip()}?"
                return {'question': question, 'answer': self.clean_answer(sentence)}
        return None

    def generate_true_false_question(self, sentence):
        """Generate a true/false question by modifying the original sentence."""
        words = word_tokenize(sentence)
        pos_tags = pos_tag(words)

        # Find verbs to negate or nouns to replace
        verbs = [(i, word) for i, (word, tag) in enumerate(pos_tags) if tag.startswith('VB')]
        nouns = [(i, word) for i, (word, tag) in enumerate(pos_tags) if tag.startswith('NN')]

        if random.choice([True, False]) and verbs:  # Flip a verb (create false statement)
            verb_idx, verb = random.choice(verbs)
            if "not" in words or "n't" in [w.lower() for w in words]:
                # Remove negation
                if "not" in words:
                    not_idx = words.index("not")
                    new_words = words[:not_idx] + words[not_idx + 1:]
                else:
                    # Handle contractions
                    for i, word in enumerate(words):
                        if "n't" in word.lower():
                            words[i] = word.lower().replace("n't", "")
                            break
                    new_words = words

                modified_sentence = " ".join(new_words)
                answer = "False"
            else:
                # Add negation
                if verb_idx > 0 and pos_tags[verb_idx - 1][1].startswith('MD'):  # Modal verb
                    new_words = words[:verb_idx] + ["not"] + words[verb_idx:]
                else:
                    aux_verbs = ["do", "does", "did"]
                    # Select appropriate auxiliary verb
                    if pos_tags[verb_idx][1] == "VBP":  # Present tense
                        aux = "do not"
                    elif pos_tags[verb_idx][1] == "VBZ":  # 3rd person singular
                        aux = "does not"
                    else:  # Past tense or other
                        aux = "did not"

                    new_words = words[:verb_idx] + aux.split() + words[verb_idx + 1:]

                modified_sentence = " ".join(new_words)
                answer = "False"
        elif nouns:  # Replace a noun (create false statement)
            noun_idx, noun = random.choice(nouns)
            similar_nouns = []

            # Find similar but different nouns using WordNet
            for synset in wordnet.synsets(noun, pos=wordnet.NOUN):
                for hypernym in synset.hypernyms():
                    for hyponym in hypernym.hyponyms():
                        if hyponym.name().split('.')[0] != noun and hyponym.name().split('.')[0] not in similar_nouns:
                            similar_nouns.append(hyponym.name().split('.')[0])

            if similar_nouns:
                replacement = random.choice(similar_nouns)
                new_words = words[:noun_idx] + [replacement] + words[noun_idx + 1:]
                modified_sentence = " ".join(new_words)
                answer = "False"
            else:
                # If we can't find a replacement, just use the original (true statement)
                modified_sentence = sentence
                answer = "True"
        else:
            # Default to true statement
            modified_sentence = sentence
            answer = "True"

        # Clean up and format
        modified_sentence = modified_sentence[0].upper() + modified_sentence[1:].rstrip('.?!') + "."
        question = f"True or False: {modified_sentence}"

        return {'question': question, 'answer': answer}

    def generate_fill_in_blank(self, sentence, pos_tags):
        """Generate a fill-in-the-blank question."""
        candidates = []

        # Find important words to blank out
        for i, (word, tag) in enumerate(pos_tags):
            if (tag.startswith('NN') or tag.startswith('VB') or tag.startswith(
                    'JJ')) and word.lower() not in self.stopwords and len(word) > 3:
                candidates.append((i, word))

        if candidates:
            idx, word = random.choice(candidates)
            words = [w for w, _ in pos_tags]
            words[idx] = "________"

            question = " ".join(words)
            # Clean punctuation at the end
            question = question.rstrip('.?!') + "?"
            question = f"Fill in the blank: {question}"

            return {'question': question, 'answer': word}
        return None

    def generate_qa_pairs(self, text, num_pairs=5):
        """Generate diverse question-answer pairs from given text."""
        try:
            # Verify text input
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Input text must be a non-empty string")

            print("Starting enhanced text processing...")
            # Tokenize the text into sentences
            sentences = sent_tokenize(text)
            all_qa_pairs = []

            for sentence in sentences:
                # Skip sentences that are too short
                if len(sentence.split()) < 5:
                    continue

                # Tokenize and tag the sentence
                words = word_tokenize(sentence)
                pos_tags = pos_tag(words)
                entities = self.extract_entities(sentence)

                # Apply different question generation techniques
                question_generators = [
                    lambda: self.generate_definition_question(sentence, pos_tags),
                    lambda: self.generate_who_question(sentence, entities),
                    lambda: self.generate_where_question(sentence, entities),
                    lambda: self.generate_when_question(sentence, pos_tags),
                    lambda: self.generate_how_question(sentence, pos_tags),
                    lambda: self.generate_why_question(sentence),
                    lambda: self.generate_true_false_question(sentence),
                    lambda: self.generate_fill_in_blank(sentence, pos_tags)
                ]

                # Shuffle the generators for variety
                random.shuffle(question_generators)

                # Try each generator until we get a valid question
                for generator in question_generators:
                    qa_pair = generator()
                    if qa_pair:
                        all_qa_pairs.append(qa_pair)
                        break

            # Ensure we don't have duplicate questions
            unique_questions = {}
            for pair in all_qa_pairs:
                question = pair['question'].lower().strip()
                if question not in unique_questions:
                    unique_questions[question] = pair

            qa_pairs = list(unique_questions.values())
            print(f"Generated {len(qa_pairs)} total unique questions")

            # Shuffle and limit to requested number
            random.shuffle(qa_pairs)
            final_pairs = qa_pairs[:num_pairs] if qa_pairs and num_pairs < len(qa_pairs) else qa_pairs
            print(f"Returning {len(final_pairs)} questions")

            return final_pairs

        except Exception as e:
            error_msg = f"Error in generate_qa_pairs: {str(e)}"
            print(error_msg, file=sys.stderr)
            raise Exception(error_msg)