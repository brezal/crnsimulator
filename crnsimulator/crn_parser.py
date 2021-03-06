#
# Parser for formal chemical reaction networks.
# 
# Written by Stefan Badelt (badelt@caltech.edu).
#
# This file was adapted from the python package: `Nuskell`
# Developed at the *DNA and Natural Algorithms Group*, Caltech.
# originally written by Seung Woo Shin (seungwoo.theory@gmail.com).
#
# Use at your own risk. 
#
#

from pyparsing import (Word, Literal, Group, Suppress, Combine, Optional, 
    alphas, nums, alphanums, delimitedList, StringStart, StringEnd, LineEnd, 
    ZeroOrMore, OneOrMore, pythonStyleComment, ParseElementEnhance)

def crn_document_setup(modular = False):
  """Parse a formal chemical reaction network. 

  Args: 
    modular <optional:bool>: Adds an additional nesting for modules within a
      CRN. Use one line per module (';' separates reactions).

  Format:
    # A list of reactions, optionally with reaction rates:
    # <- this is a comment!
    B + B -> C    # [k = 1]
    C + A <=> D   # [kf = 1, kr = 1]
    <=> A  [kf = 15, kr = 6]

    # Note that you can write multiple reactions in one line:
    A + 2C -> E [k = 13.78]; E + F <=> 2A  [kf = 13, kr = 14]

  Returns:

  """
  # NOTE: If you want to add support for multiple modules per line, you can use
  # the '|' character.
  
  W = Word
  G = Group
  S = Suppress
  O = Optional
  C = Combine
  L = Literal
  
  def T(x, tag):
    """ Return a *Tag* to distinguish (ir)reversible reactions """
    def TPA(tag):
      return lambda s, l, t: [tag] + t.asList()
    return x.setParseAction(TPA(tag))
  
  crn_DWC = "".join(
      [x for x in ParseElementEnhance.DEFAULT_WHITE_CHARS if x != "\n"])
  ParseElementEnhance.setDefaultWhitespaceChars(crn_DWC)
  
  identifier = W(alphas, alphanums+"_")

  multiplier = W(nums)
  species = G(O(multiplier) + identifier)

  rate = C(W(nums) + O((L('.') + W(nums)) | (L('e') + O('-') + W(nums))))

  k = G(S('[') + S('k') + S('=') + rate + S(']'))
  rev_k = G(S('[') + S('kf') + S('=') + rate + S(',') + \
                     S('kr') + S('=') + rate + S(']'))

  reaction = T(G(O(delimitedList(species, "+"))) + \
             S("->") + \
             G(O(delimitedList(species, "+"))) + O(k), 'irreversible')

  rev_reaction = T(G(O(delimitedList(species, "+"))) + \
                 S("<=>") + \
                 G(O(delimitedList(species, "+"))) + O(rev_k), 'reversible')
  

  expr = G(reaction | rev_reaction) 

  if modular :
    module = G(expr + ZeroOrMore(S(";") + expr))
  else :
    module = expr + ZeroOrMore(S(";") + expr)

  crn = OneOrMore(module + ZeroOrMore(S(LineEnd())))
  
  document = StringStart() + ZeroOrMore(S(LineEnd())) + crn + StringEnd()
  document.ignore(pythonStyleComment)
  return document

def post_process(crn):
  """Process a parsed CRN.

  Does:
   - remove 'reversible' and 'irreversible' tags.
      (this information is stored implicitly with one or two rates).
   - Translates species multipliers to multisets
   - Extracts the set of all species in the CRN.
   - Adds 'None' as reaction rate if no rate was specified.

  Does not:
   - Check if reactions are specified twice
   - Check stochiometry
  
  """
  def remove_multipliers(species) :
    flat = []
    for s in species:
      if len(s) == 1:
        flat.append(s[0])
      elif len(s) == 2:
        ss = [s[1]] * int(s[0])
        flat.extend(ss)
    return flat

  new = []
  species = set()
  for line in crn:
    if len(line) == 3:
      # No rate specified
      t, r, p = line
      r = remove_multipliers(r)
      p = remove_multipliers(p)
      if t == 'reversible':
        new.append([r,p,[None, None]])
      elif t == 'irreversible':
        new.append([r,p,[None]])
      else :
        raise ValueError('Wrong CRN format!')
    elif len(line) == 4:
      t, r, p, k = line
      r = remove_multipliers(r)
      p = remove_multipliers(p)
      if t == 'reversible':
        assert len(k) == 2
        new.append([r,p,k])
      elif t == 'irreversible':
        assert len(k) == 1
        new.append([r,p,k])
      else :
        raise ValueError('Wrong CRN format!')
    else :
      raise ValueError('Wrong CRN format!')
    species = species.union(r).union(p)
  return new, sorted(list(species))

def parse_crn_file(filename, process=True):
  """Parses a CRN from a file. 

  Args:
    filename (<str>): The name of the file for parsing.
    process (optional <bool>): Process the format of the returned CRN.

  Returns:
    crn (<lol>): List of list representation of a CRN
    species (<set()>): A set of all involved species (only when process=True)
  
  """
  crn_document = crn_document_setup()
  if process:
    return post_process(crn_document.parseFile(filename, parseAll = True).asList())
  else :
    return crn_document.parseFile(filename, parseAll = True).asList()

def parse_crn_string(data, process=True):
  """Parses a CRN from a string. 

  Args:
    filename (<str>): The name of the file for parsing.
    process (optional <bool>): Process the format of the returned CRN.

  Returns:
    crn (<lol>): List of list representation of a CRN
    species (<set()>): A set of all involved species (only when process=True)
  
  """
  crn_document = crn_document_setup()
  if process :
    return post_process(crn_document.parseString(data).asList())
  else :
    return crn_document.parseString(data).asList()

