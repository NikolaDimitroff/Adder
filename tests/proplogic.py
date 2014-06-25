# Depends on: adder
from adder import proplogic
import os
import unittest

import tests.config as config

class DefiniteClausesTests(unittest.TestCase):
    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)

        implications = """A
                B
                L & M => P
                B & L => M
                A & P => L
                A & B => L
                P => Q
        """

        self.kb = proplogic.DefiniteKnowledgeBase(implications)

    def test_parsing_kb(self):
        dnf = """A
                B
                !L | !M | P
                !B | !L | M
                !A | !P | L
                !A | !B | L
                !P | Q
        """
        
        parsed_dnf = proplogic.DefiniteKnowledgeBase(dnf)
        self.assertEqual(parsed_dnf, self.kb)

    def test_fc_sample(self):
        q = proplogic.forward_chaining(self.kb.raw_kb, "Q")
        not_q = proplogic.forward_chaining(self.kb.raw_kb, "!Q")
        self.assertTrue(q)
        self.assertFalse(not_q)


        
    def test_bs_sample(self):
        q = proplogic.backward_chaining(self.kb.raw_kb, "Q")
        not_q = proplogic.backward_chaining(self.kb.raw_kb, "!Q")
        self.assertTrue(q)
        self.assertFalse(not_q)

    def test_failure(self):
        result_bc = proplogic.backward_chaining(self.kb.raw_kb, "T")
        result_fc = proplogic.forward_chaining(self.kb.raw_kb, "T")
        self.assertFalse(result_bc)
        self.assertFalse(result_fc)


class CnfConverterTests(unittest.TestCase):
    def test_conversion(self):
        formula_equivalences = [
            ("!(A <=> B)", "(!A | !B) & (A | B)"),
            ("(A <=> B)", "(!A | B) & (A | !B)"),
            ("!((A <=> B) => ((A => B) & (B => A)))", "!A & !B & (A | B)"),
            ("(A <=> B) => ((A => B) & (B => A))", ""),
            ("(P & !Q) | (R & S) | (Q & R & !S)", "(P | Q | S) & (P | R) & (!Q | R)"),
            ("(A => (B & C)) => B", "A | B"),
            ("((!A | B) & (!A | C)) => B", "A | B"),
            ("!(A => (B & C))", "A & (!B | !C)"),
            ("(A => B) => C", "(A | C) & (!B | C)"),
            ("(B11 => (P12 | P21)) & ((P12 | P21) => B11)", "(!B11 | P12 | P21) & (!P12 | B11) & (!P21 | B11)"),
            ("(B11 <=> (P12 | P21))", "(!B11 | P12 | P21) & (!P12 | B11) & (!P21 | B11)"),
            ("(A | B) => C", "(!A | C) & (!B | C)")
        ]

        for formula, cnf in formula_equivalences:
            result = proplogic.parse_cnf_sentence(formula)
            result2 = proplogic.parse_cnf_sentence(cnf)
            expected_cnf = [{symbol.strip() for symbol in 
                             disjunct.replace(")", "").replace("(", "").split("|")
                             }
                            for disjunct in cnf.split("&")
                            if len(disjunct) != 0
                            ]
            self.assertCountEqual(result, result2)
            self.assertCountEqual(result, expected_cnf)

    def test_is_operator(self):
        formula_equivalences = [
            ("(A <=> B) => ((A => B) & (B => A))", "=>"),
            ("(P | !Q) | (R & S) | (Q & R & !S)", "|"),
            ('!(P12 | P21) | B11', "|"),
            ("A => B & C => B", "=>"),
            ("(A => B) <=> (C => B)", "<=>"),
            ("!(A => B <=> (C => B))", "!")
        ]

        for formula, operator in formula_equivalences:
            parsed = proplogic.parse_sentence(formula)
            result_operator = parsed[0]
            self.assertEqual(result_operator, operator, msg="{}/{}".format(formula, operator))

    def test_is_not_operator(self):
        formula_lies = [
            ("(A <=> B) => ((A => B) & (B => A))", "&"),
            ("(A <=> B) => ((A => B) & (B => A))", "<=>"),
            ("(P & !Q) | (R & S) | (Q & R & !S)", "!"),
            ("(A => B) <=> (C => B)", "=>")
        ]
        for formula, operator in formula_lies:
            parsed = proplogic.parse_sentence(formula)
            result_operator = parsed[0]
            self.assertNotEqual(result_operator, operator, msg="{}/{}".format(formula, operator))

        
    def test_kb_parsing(self):
        formulae = [
            "(A => B | D)",
            "((A & B) => C)",
            "(C <=> !D)",
        ]
        kb = proplogic.PlKnowledgeBase("\n".join(formulae))
        expected = "(!A | B | D) & (!A | !B | C) & (!C | !D) & (C | D)"
        expected_cnf = proplogic.parse_cnf_sentence(expected)
        self.assertCountEqual(kb.raw_kb, expected_cnf)

        and_concatenation = proplogic.parse_cnf_sentence(" & ".join(formulae))
        self.assertCountEqual(kb.raw_kb, and_concatenation)


class ResolutionProverTests(unittest.TestCase):
    def test_prover_truth(self):
        # Wumpus sample, aima p.256 
        #    (B11 <=> (P12 | P21)) & !B11
        formulae = "(B11 <=> (P12 | P21)) & !B11"
        kb = proplogic.PlKnowledgeBase(formulae)
        query = "!P12"

        result = kb.ask(query)
        self.assertTrue(result)

    def test_prover_false(self):
        # Wumpus sample, aima p.256 
        formulae = "(B11 <=> (P12 | P21)) & !B11"
        kb = proplogic.PlKnowledgeBase(formulae)
        query = "P12"
        
        result = kb.ask(query)
        self.assertFalse(result)

        
        formulae = "A | B"
        kb = proplogic.PlKnowledgeBase(formulae, information_rich=False)
        query = "A"
        
        result = kb.ask(query)
        self.assertFalse(result)

    def test_wumpus_sample_kb(self):
        kb = proplogic.PlKnowledgeBase("""!Breeze_0
            WumpusAlive_0
            !Stench_0
            L11_0
            !P11
            !W11
            B11 <=> (P12 | P21)
            S11 <=> (W21 | W12)
            L11_0 => (Stench_0 <=> S11)
            L11_0 => (Breeze_0 <=> B11)
            OK12_0 <=> !P12 & (!W12 | !WumpusAlive_0)
        """, max_clause_len=3)  

        self.assertTrue(kb.ask("OK12_0"))
        self.assertFalse(kb.ask("!OK12_0"))

