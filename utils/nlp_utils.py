import spacy
from spacy.matcher import Matcher
nlp = spacy.load("en_core_web_sm") 

def extract_entity_pairs(sent):
  head = ''
  tail = ''

  prefix = ''             # variable for storing compound noun phrases
  prev_token_dep = ''     # dependency tag of previous token in the sentence
  prev_token_text = ''    # previous token in the sentence


  for token in sent:
    # if it's a punctuation mark, do nothing and move on to the next token
    if token.dep_ == 'punct':
      continue

    # Condition #1: subj is the head entity
    if token.dep_.find('subj') == True:
      head = f'{prefix} {token.text}'

      # Reset placeholder variables, to be reused by succeeding entities
      prefix = ''
      prev_token_dep = ''
      prev_token_text = ''

    # Condition #2: obj is the tail entity
    if token.dep_.find('obj') == True:
      tail = f'{prefix} {token.text}'

    # Condition #3: entities may be composed of several tokens
    if token.dep_ == "compound":
      # if the previous word was also a 'compound' then add the current word to it
      if prev_token_dep == "compound":
        prefix = f'{prev_token_text} {token.text}'
      # if not, then this is the first token in the noun phrase
      else:
        prefix = token.text

    # Placeholders for compound cases.
    prev_token_dep = token.dep_
    prev_token_text = token.text
  #############################################################

  return [head.strip(), tail.strip()]


def extract_relation(sent):

  # Rule-based pattern matching class
  matcher = Matcher(nlp.vocab)

  # define the patterns according to the dependency graph tags
  pattern = [{'DEP':'ROOT'},                # verbs are often root
            {'DEP':'prep','OP':"?"},
            {'DEP':'attr','OP':"?"},
            {'DEP':'det','OP':"?"},
            {'DEP':'agent','OP':"?"}]

  matcher.add("relation",[pattern])

  matches = matcher(sent)
  k = len(matches) - 1

  span = sent[matches[k][1]:matches[k][2]]

  return(span.text)