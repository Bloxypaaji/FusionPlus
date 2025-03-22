import nltk
from nltk import pos_tag, word_tokenize, ne_chunk, sent_tokenize
from nltk.tree import Tree
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
import re
import string
import random
from collections import Counter


class EnhancedNotAI:
    """An enhanced AI for answering questions based on note content with deeper analysis capabilities."""

    def __init__(self):
        # Download necessary NLTK resources
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            print(f"Error downloading NLTK resources: {e}")

        self.stopwords = set(stopwords.words('english'))

        # Add question words to track question types
        self.question_words = {
            'what': 'definition',
            'who': 'person',
            'where': 'location',
            'when': 'time',
            'why': 'reason',
            'how': 'method',
            'which': 'selection',
            'can': 'ability',
            'could': 'possibility',
            'would': 'hypothetical',
            'should': 'advice',
            'is': 'confirmation',
            'are': 'confirmation',
            'do': 'action',
            'does': 'action'
        }

    def extract_entities(self, text):
        """Extract named entities from text."""
        entities = {'PERSON': [], 'GPE': [], 'LOCATION': [], 'ORGANIZATION': [], 'DATE': [], 'TIME': [], 'MONEY': [],
                    'PERCENT': []}

        try:
            sentences = sent_tokenize(text)
            for sentence in sentences:
                chunks = ne_chunk(pos_tag(word_tokenize(sentence)))

                for chunk in chunks:
                    if isinstance(chunk, Tree):
                        entity_type = chunk.label()
                        entity_text = " ".join([word for word, tag in chunk.leaves()])
                        if entity_type in entities:
                            entities[entity_type].append(entity_text)
        except Exception as e:
            print(f"Error extracting entities: {e}")

        # Filter out duplicates
        for entity_type, entity_list in entities.items():
            entities[entity_type] = list(set(entity_list))

        return entities

    def extract_keywords(self, text):
        """Extract important keywords from text."""
        try:
            # Tokenize and get POS tags
            tokens = word_tokenize(text.lower())
            tagged = pos_tag(tokens)

            # Get content words (nouns, verbs, adjectives, adverbs)
            important_tags = ['NN', 'NNS', 'NNP', 'NNPS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'JJ', 'JJR', 'JJS',
                              'RB', 'RBR', 'RBS']
            content_words = [word.lower() for word, tag in tagged if
                             tag in important_tags and word.lower() not in self.stopwords]

            # Count frequency
            word_freq = Counter(content_words)

            # Return top 10 keywords
            return [word for word, _ in word_freq.most_common(10)]
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []

    def find_relevant_sentences(self, question, note_content):
        """Find sentences in the note that are relevant to the question."""
        try:
            # Extract question keywords
            question_keywords = self.extract_keywords(question)

            # Split note into sentences
            sentences = sent_tokenize(note_content)

            # Score sentences based on keyword overlap
            scored_sentences = []
            for sentence in sentences:
                score = sum(1 for keyword in question_keywords if keyword in sentence.lower())
                if score > 0:
                    scored_sentences.append((sentence, score))

            # Sort by relevance score
            scored_sentences.sort(key=lambda x: x[1], reverse=True)

            # Return top relevant sentences
            return [sentence for sentence, score in scored_sentences[:3]]
        except Exception as e:
            print(f"Error finding relevant sentences: {e}")
            return []

    def determine_question_type(self, question):
        """Determine the type of question being asked."""
        question_lower = question.lower()
        tokens = word_tokenize(question_lower)

        # Check for question words
        for token in tokens:
            if token in self.question_words:
                return self.question_words[token]

        # Default question type if no match
        return 'general'

    def answer_question(self, question, note_content):
        """Answer a question based on the note content with improved comprehension."""
        if not question or not note_content:
            return "I need both a question and note content to provide an answer."

        try:
            # Extract question type
            question_type = self.determine_question_type(question)

            # Find relevant sentences in the note
            relevant_sentences = self.find_relevant_sentences(question, note_content)

            # Extract entities from the note content
            entities = self.extract_entities(note_content)

            # Extract keywords from question
            question_keywords = self.extract_keywords(question)

            # If no relevant sentences found
            if not relevant_sentences:
                return "I couldn't find information in your note that answers this question directly."

            # Generate response based on question type and relevant content
            if question_type == 'person':
                if entities['PERSON']:
                    people_context = self.find_context_for_entities(entities['PERSON'], note_content)
                    return f"Based on your note, {','.join(entities['PERSON'])} {'are' if len(entities['PERSON']) > 1 else 'is'} mentioned. {people_context}"
                else:
                    return "I couldn't find any specific people mentioned in your note."

            elif question_type == 'location':
                locations = entities['GPE'] + entities['LOCATION']
                if locations:
                    location_context = self.find_context_for_entities(locations, note_content)
                    return f"The note mentions these locations: {', '.join(locations)}. {location_context}"
                else:
                    return "I couldn't find any specific locations in your note."

            elif question_type == 'time':
                time_entities = entities['DATE'] + entities['TIME']
                if time_entities:
                    return f"Time references in your note include: {', '.join(time_entities)}."
                else:
                    # Look for time-related words
                    time_words = ['today', 'yesterday', 'tomorrow', 'morning', 'afternoon', 'evening', 'night', 'month',
                                  'year', 'week', 'day']
                    time_contexts = [sent for sent in sent_tokenize(note_content) if
                                     any(word in sent.lower() for word in time_words)]
                    if time_contexts:
                        return f"Your note includes these time references: {' '.join(time_contexts[:2])}"
                    return "I couldn't find specific time references in your note."

            elif question_type == 'reason':
                reason_indicators = ['because', 'since', 'as', 'due to', 'result of', 'reason', 'why']
                reason_sentences = [sent for sent in sent_tokenize(note_content) if
                                    any(indicator in sent.lower() for indicator in reason_indicators)]
                if reason_sentences:
                    return f"The reason mentioned in your note appears to be: {reason_sentences[0]}"
                else:
                    return "I found these relevant details: " + " ".join(relevant_sentences)

            elif question_type == 'method':
                method_indicators = ['how', 'steps', 'process', 'procedure', 'way', 'method']
                method_sentences = [sent for sent in sent_tokenize(note_content) if
                                    any(indicator in sent.lower() for indicator in method_indicators)]
                if method_sentences:
                    return f"Here's the method described in your note: {' '.join(method_sentences[:2])}"
                else:
                    return "I found these relevant details: " + " ".join(relevant_sentences)

            elif question_type == 'definition':
                definition_patterns = [r"is a", r"refers to", r"defined as", r"means", r"is an"]
                definition_sentences = []
                for sent in sent_tokenize(note_content):
                    if any(re.search(pattern, sent.lower()) for pattern in definition_patterns):
                        definition_sentences.append(sent)

                if definition_sentences:
                    return f"According to your note: {definition_sentences[0]}"
                else:
                    return "I found these relevant details: " + " ".join(relevant_sentences)

            else:
                # For general questions, return the most relevant sentences
                return "Based on your note: " + " ".join(relevant_sentences)

        except Exception as e:
            print(f"Error answering question: {e}")
            return "I encountered an error while processing your question. Please try asking in a different way."

    def find_context_for_entities(self, entities, note_content):
        """Find context sentences for entities."""
        context = []
        sentences = sent_tokenize(note_content)

        for entity in entities[:2]:  # Limit to first 2 entities
            for sentence in sentences:
                if entity in sentence:
                    context.append(sentence)
                    break  # Just get first mention

        if context:
            return " " + " ".join(context[:2])  # Limit context
        return ""

    def extract_main_topics(self, note_content):
        """Extract the main topics from the note content."""
        try:
            # Get keywords
            keywords = self.extract_keywords(note_content)

            # Extract entities
            entities = self.extract_entities(note_content)
            all_entities = []
            for entity_type, entity_list in entities.items():
                all_entities.extend(entity_list)

            # Combine keywords and entities
            topics = keywords + all_entities

            # Remove duplicates and limit to top 5
            return list(dict.fromkeys(topics))[:5]
        except Exception as e:
            print(f"Error extracting topics: {e}")
            return []

    def summarize_content(self, note_content):
        """Generate a brief summary of the note content."""
        try:
            # Get the main topics
            main_topics = self.extract_main_topics(note_content)

            # Get the most important sentences
            sentences = sent_tokenize(note_content)
            important_sentences = []

            if sentences:
                # First sentence is often important
                if len(sentences) > 0:
                    important_sentences.append(sentences[0])

                # Add sentences with main topics
                for sentence in sentences[1:]:
                    if any(topic.lower() in sentence.lower() for topic in main_topics):
                        important_sentences.append(sentence)
                        if len(important_sentences) >= 3:
                            break

            # Combine into summary
            if important_sentences:
                return " ".join(important_sentences)
            else:
                return "This note contains: " + ", ".join(
                    main_topics) if main_topics else "I couldn't generate a meaningful summary."
        except Exception as e:
            print(f"Error summarizing content: {e}")
            return "I couldn't generate a summary for this content."