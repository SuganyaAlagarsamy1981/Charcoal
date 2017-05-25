from math import (
    exp, log, log2, log10, sqrt, sin, cos, tan, asin, acos, atan, floor, ceil
)
from functools import reduce, lru_cache

try:
    from regex import (
        match, search, split, sub, findall,
        compile as re_compile, escape as re_escape,
        M as multiline_flag
    )
    def multilineify(function):
        def wrap_function(*args, **kwargs):
            kwargs['flags'] = multiline_flag
            return function(*args, **kwargs)
        return wrap_function
    match, search, split, sub, findall = (
        multilineify(match),
        multilineify(search),
        multilineify(split),
        multilineify(sub),
        multilineify(findall)
    )
except:
    print("Please install the 'regex' module: 'sudo -H pip3 install regex'")
    __import__("sys").exit()

# TODO: chain plus/minus for less precision needed
# TODO: tests for rational ops

r_whitespace = re_compile("\s+")
prime_cache = [2, 3]


def prime_gen():
    global prime_cache
    for number in prime_cache:
        yield number
    n = prime_cache[-1]
    while True:
        if all(n % number for number in prime_cache):
            prime_cache += [n]
            yield n
        n += 2


def flatten(iterable):
    return [item for element in iterable for item in (
        flatten(element)
        if hasattr(element, '__iter__') and not isinstance(element, str) else
        [element]
    )]

heads = []
headifies = []


def headify(clazz):
    global heads
    global headifies
    if clazz not in heads:
        heads += [clazz]
        fn = lambda leaves, precision=10: clazz(*leaves)
        headifies += [fn]
        return fn
    return headifies[heads.index(clazz)]


def create_expression(value):
    value_type = type(value)
    if value is None:
        return None
    elif isinstance(value, Expression):
        return value
    elif value_type == complex:
        return Complex(value)
    elif value_type == str:
        return String(value)
    elif value_type == list:
        return List(*[create_expression(item) for item in value])
    elif value_type != int and value % 1:
        exponent = 0
        while value % 1:
            value *= 10
            exponent -= 1
        return Real(value, exponent)
    else:
        exponent = 0
        while not value % 10:
            value //= 10
            exponent += 1
        return Integer(value, exponent)

cx = create_expression


def boolean(value):
    return _True if value else _False

class Expression(object):

    __slots__ = ("head", "leaves", "run")

    def __init__(self, head=None, leaves=[], run=None):
        self.head = head
        self.leaves = [create_expression(leaf) for leaf in leaves]
        if run:
            self.run = lambda precision=10: run(precision)
        else:
            self.run = lambda precision=10: self.head(self.leaves, precision)

    def __add__(self, other):
        return Expression(
            None, [],
            lambda precision=10: self.run(precision + 2) + (
                create_expression(other).run(precision + 2)
            )
        )

    def __sub__(self, other):
        return Expression(
            None, [],
            lambda precision=10: self.run(precision + 2) - (
                create_expression(other).run(precision + 2)
            )
        )

    def __rsub__(self, other):
        return Expression(
            None, [],
            lambda precision=10: (
                create_expression(other).run(precision + 2)
            ) - self.run(precision + 2)
        )

    def __mul__(self, other):
        return Expression(
            None, [],
            lambda precision=10: self.run(precision + 2) * (
                create_expression(other).run(precision + 2)
            )
        )

    def __truediv__(self, other):
        return Expression(
            None, [],
            lambda precision=10: self.run(precision + 2) / (
                create_expression(other).run(precision + 2)
            )
        )

    def __rtruediv__(self, other):
        return Expression(
            None, [],
            lambda precision=10: (
                create_expression(other).run(precision + 2)
            ) / self.run(precision + 2)
        )

    def to_number(self):
        return self.run().to_number()

    def to_precision(self, precision=10):
        return self.run().to_precision(precision)

    def is_integer(self):
        return self.run().is_integer()

    def is_odd(self):
        return self.run().is_odd()

    def is_even(self):
        return self.run().is_even()

# Options
IgnoreCase = Expression()

class Number(Expression):
    def __init__(self, head=None):
        super().__init__(head=head)

class Real(Number):
    slots = ("head", "leaves", "run", "is_int", "precision")

    def __init__(self, value, exponent=0, precision=0, is_int=False):
        super().__init__(head=headify(Real))
        self.precision = precision or floor(log10(abs(value) or 1))
        self.is_int = is_int
        self.leaves = [value, exponent]

    def __str__(self):
        exponent = self.leaves[1]
        string = str(self.leaves[0])
        zeroes = 1 - exponent - len(string)
        if zeroes > 0:
            string = "0" * zeroes + string
        return (
            string + "0" * exponent
            if exponent > 0 else
            (string[:exponent] + "." + string[exponent:])
            if exponent < 0 else
            string
        )

    def __repr__(self):
        return str(self)

    def __add__(self, other):
        if type(other) == Expression:
            return other + self
        if type(other) == Real:
            precision = max(0, min(self.precision, other.precision) - 2)
            exponent_difference = self.leaves[1] - other.leaves[1]
            if exponent_difference > 0:
                value = (
                    self.leaves[0] * 10 ** exponent_difference +
                    other.leaves[0]
                )
            else:
                value = (
                    self.leaves[0] +
                    other.leaves[0] * 10 ** -exponent_difference
                )
            actual_precision = floor(log10(abs(value) or 1))
            return Real(
                (
                    value * 10 ** (precision - actual_precision)
                    if precision - actual_precision > 1 else
                    value // 10 ** (actual_precision - precision) + bool(
                        value < 0 and
                        value % 10 ** (actual_precision - precision)
                    )
                ),
                (
                    min(self.leaves[1], other.leaves[1]) +
                    actual_precision -
                    precision
                ),
                precision=precision
            )

    def __sub__(self, other):
        if type(other) == Expression:
            return other.__rsub__(self)
        if type(other) == Real:
            precision = max(0, min(self.precision, other.precision) - 2)
            exponent_difference = self.leaves[1] - other.leaves[1]
            if exponent_difference > 0:
                value = (
                    self.leaves[0] * 10 ** exponent_difference -
                    other.leaves[0]
                )
            else:
                value = (
                    self.leaves[0] -
                    other.leaves[0] * 10 ** -exponent_difference
                )
            actual_precision = floor(log10(abs(value) or 1))
            return Real(
                (
                    value * 10 ** (precision - actual_precision)
                    if precision - actual_precision > 1 else
                    value // 10 ** (actual_precision - precision) + bool(
                        value < 0 and
                        value % 10 ** (actual_precision - precision)
                    )
                ),
                (
                    min(self.leaves[1], other.leaves[1]) +
                    actual_precision -
                    precision
                ),
                precision=precision
            )

    def __mul__(self, other):
        if type(other) == Expression:
            return other * self
        if type(other) == Real:
            precision = max(0, min(self.precision, other.precision) - 2)
            value = self.leaves[0] * other.leaves[0]
            actual_precision = floor(log10(abs(value) or 1))
            return Real(
                (
                    value * 10 ** (precision - actual_precision)
                    if precision - actual_precision > 1 else
                    value // 10 ** (actual_precision - precision) + bool(
                        value < 0 and
                        value % 10 ** (actual_precision - precision)
                    )
                ),
                (
                    self.leaves[1] +
                    other.leaves[1] +
                    actual_precision -
                    precision
                ),
                precision=precision
            )
        if type(other) == Rational or type(other) == Complex:
            return other * self
        return self * Real(other)

    def __truediv__(self, other):
        if type(other) == Expression:
            return other.__rtruediv__(self)
        if isinstance(other, Real):
            precision = max(0, min(self.precision, other.precision) - 2)
            pow10 = 10 ** precision * self.leaves[0]
            return Real(
                pow10 // other.leaves[0] + bool(
                    pow10 < 0 and pow10 % other.leaves[0]
                ),
                self.leaves[1] - other.leaves[1] - precision,
                precision=precision
            )
        other_type = type(other)
        if other_type == Rational:
            pass
        if other_type == Complex:
            pass # TODO

    def to_number(self):
        return self.leaves[0] * 10 ** self.leaves[1]

    def is_integer(self):
        return boolean(self.is_int or self.leaves[1] >= 0)

    def is_odd(self):
        return boolean(
            self.is_int or 
            self.leaves[1] > 0 or self.leaves[1] == 0 and (
                self.leaves[0] % 2 == 1
            )
        )

    def is_even(self):
        return boolean(
            self.is_int or 
            self.leaves[1] > 0 or self.leaves[1] == 0 and (
                self.leaves[0] % 2 == 0
            )
        )

class Integer(Real):
    def __init__(self, value, exponent=0):
        super().__init__(
            int(value), exponent, precision=float("inf"), is_int=True
        )
        self.head = headify(Integer)
        actual_precision = floor(log10(abs(value) or 1))
        self.run = lambda precision=10: Real(
            (
                value * 10 ** (precision - actual_precision - 1)
                if precision - actual_precision > 1 else
                value // 10 ** (1 + actual_precision - precision)
            ),
            self.leaves[1] - precision + actual_precision + 1,
            precision=precision
        )

    def __str__(self):
        string = str(self.leaves[0])
        return (
            string + "0" * self.leaves[1]
            if self.leaves[1] != 0 else
            string
        )

    def __repr__(self):
        return str(self)

    def to_number(self):
        return self.leaves[0] * 10 ** self.leaves[1]

    def is_integer(self):
        return One

    def is_odd(self):
        return boolean(self.leaves[1] > 0 or self.leaves[1] == 0 and (
            self.leaves[0] % 2 == 1
        ))

    def is_even(self):
        return boolean(self.leaves[1] > 0 or self.leaves[1] == 0 and (
            self.leaves[0] % 2 == 0
        ))

One = Integer(1)
_False = Integer(0)
_True = Integer(1)
setattr(_False, "__str__", lambda: "False")
setattr(_True, "__str__", lambda: "True")

class Rational(Number):
    def __init__(self, numerator, denominator, exponent=0):
        super().__init__(head=headify(Rational))
        gen = prime_gen()
        square = 0
        while numerator % 1:
            numerator *= 10
            exponent -= 1
        while denominator % 1:
            denominator *= 10
            exponent += 1
        while not numerator % 10:
            numerator //= 10
            exponent += 1
        while not denominator % 10:
            denominator //= 10
            exponent -= 1
        numerator, denominator = int(numerator), int(denominator)
        while numerator > square and denominator > square:
            prime = next(gen)
            square = prime * prime
            while (not numerator % prime) and (not denominator % prime):
                numerator //= prime
                denominator //= prime
        self.leaves = [numerator, denominator, exponent]
        # TODO: make it create integer directly somehow
        if denominator == 1:
            self.run = lambda precision=10: (
                Integer(self.leaves[0], self.leaves[3])
            )

    def __str__(self):
        return str(self.leaves[0]) + "/" + str(self.leaves[1])

    def __repr__(self):
        return str(self)

    def __add__(self, other):
        if isinstance(other, Expression):
            return other + self

    def __mul__(self, other):
        if isinstance(other, Expression):
            return other * self
        if isinstance(other, Rational):
            return Rational(
                self.leaves[0] * other.leaves[0],
                self.leaves[1] * other.leaves[1]
            )

    def __truediv__(self, other):
        if isinstance(other, Rational):
            return Rational(
                self.leaves[0] * other.leaves[1],
                self.leaves[1] * other.leaves[0]
            )

    def to_number(self):
        return float(self.leaves[0]) / self.leaves[1]

    def is_integer(self):
        return boolean(self.leaves[1] == 1)

    def is_odd(self):
        return boolean(self.leaves[1] == 1 and (self.leaves[0] % 2 == 1))

    def is_even(self):
        return boolean(self.leaves[1] == 1 and (self.leaves[0] % 2 == 0))

class Complex(Number):
    def __init__(self, real, imaginary=0):
        super.__init__(head=headify(Complex))
        if isinstance(real, complex):
            self.real = create_expression(real).run()
            self.imaginary = create_expression(imaginary).run()
        self.leaves = [real, imaginary]

    def __str__(self):
        return str(self.leaves[0]) + " + " + str(self.leaves[1]) + "j"

    def __repr__(self):
        return str(self)

class List(Expression):
    # TODO: operators
    def __init__(self, *items):
        super().__init__(head=headify(List))
        self.leaves = list(filter(lambda x: x is not None, items))

    def __getitem__(self, i):
        return self.leaves.__getitem__(i)

    def __setitem__(self, i, value):
        self.leaves.__setitem__(i, value)

    def __iter__(self):
        return iter(self.leaves)

class String(Expression):
    def __init__(self, value):
        super().__init__(head=headify(String))
        self.leaves = [value]

    def __str__(self):
        return self.leaves[0]

    def __repr__(self):
        return repr(self.leaves[0])

    def __getitem__(self, i):
        return self.leaves[0].__getitem__(i)

    def __iter__(self):
        return iter(self.leaves[0])

    def __add__(self, other):
        if isinstance(other, String):
            return String(self.leaves[0] + other.leaves[0])

    def __or__(self, other):
        other_type = type(other)
        if other_type == String:
            return List(self.leaves[0], other.leaves[0])
        if other_type == List:
            return List(*(other.leaves + self.leaves))

class Rule(Expression):
    def __init__(self, match, replacement):
        super().__init__(head=headify(Rule))
        self.leaves = [match, replacement]

class DelayedRule(Expression):
    def __init__(self, match, replacement):
        super().__init__(head=headify(DelayedRule))
        self.leaves = [match, replacement]

class Pattern(Expression):
    def __init__(self, regex):
        super().__init__(head=headify(Pattern))
        self.leaves = [regex]

    def __str__(self):
        return self.leaves[0]

    def __repr__(self):
        return repr(self.leaves[0])

    def __add__(self, other):
        other_type = type(other)
        if other_type == Pattern:
            return Pattern(self.leaves[0] + other.leaves[0])
        if other_type == String:
            return Pattern(self.leaves[0] + re_escape(other.leaves[0]))

    def __radd__(self, other):
        if isinstance(other, String):
            return Pattern(re_escape(other.leaves[0]) + self.leaves[0])

    def __hash__(self):
        return hash(self.leaves[0])

    def __eq__(self, other):
        return self.leaves[0] == other.leaves[0]

_ = Pattern(r".")
__ = Pattern(r".+")
___ = Pattern(r".*")
StartOfString = Pattern(r"^")
EndOfString = Pattern(r"$")
StartOfLine = Pattern(r"\A")
EndOfLine = Pattern(r"\Z")
Whitespace = Pattern(r"\s+")
NumberString = Pattern(r"\d+.?\d*")
WordCharacter = Pattern(r"(?:\p{L}|[0-9])")
LetterCharacter = Pattern(r"\p{L}")
DigitCharacter = Pattern(r"[0-9]")
HexadecimalCharacter = Pattern(r"[0-9a-fA-F]")
WhitespaceCharacter = Pattern(r"\s")
PunctuationCharacter = Pattern(r"\p{P}")
WordBoundary = Pattern(r"\b")

# TODO: PatternTest (_ ? LetterQ)

class RegularExpression(Pattern):
    def __init__(self, regex):
        super().__init__(regex)
        self.head = headify(RegularExpression)

class Repeated(Pattern):
    def __init__(self, item):
        if isinstance(item, Pattern):
            super().__init__("(?:" + str(item) + ")+")
        else:
            super().__init__("(?:" + re_escape(str(item)) + ")+")
        self.head = headify(Repeated)

class RepeatedNull(Pattern):
    def __init__(self, item):
        if isinstance(item, Pattern):
            super().__init__("(?:" + str(item) + ")+")
        else:
            super().__init__("(?:" + re_escape(str(item)) + ")+")
        self.head = headify(RepeatedNull)

# TODO: AlphabetData (from lazy ranges)

class Span(Expression):
    __slots__ = ("head", "leaves", "process")

    def __init__(self, start=None, stop=None, step=None):
        super().__init__(head=headify(Span))

        def modify(number, iterable):
            if isinstance(number, Expression):
                number = number.to_number()
            if number == 1:
                return -len(iterable)
            return number + ((len(iterable) + 1) if number < 0 else 0)

        if start is not None:
            if stop is not None:
                if step is not None:
                    self.process = lambda iterable: (lambda start, end: (
                        iterable[start - 1:end:step]
                        if step > 0 else
                        iterable[start:end - 1:step]
                    ))(modify(start, iterable), modify(stop, iterable))
                else:
                    self.process = lambda iterable: iterable[
                        modify(start, iterable) - 1:modify(stop, iterable)
                    ]
            else:
                if step is not None:
                    self.process = lambda iterable: iterable[
                        modify(start, iterable) - 1::step
                    ]
                else:
                    self.process = lambda iterable: iterable[
                        modify(start, iterable) - 1:
                    ]
        else:
            if stop is not None:
                if step is not None:
                    self.process = lambda iterable: iterable[
                        :modify(stop, iterable):step
                    ]
                else:
                    self.process = lambda iterable: iterable[
                        :modify(stop, iterable)
                    ]
            else:
                if step is not None:
                    self.process = lambda iterable: iterable[::step]
                else:
                    # TODO: clone or no
                    self.process = lambda iterable: iterable[:]

def integerQ(number):
    return int(
        isinstance(number, int) or
        (isinstance(number, float) and not (number % 1))
    )

def oddQ(number):
    return int(integerQ(number) and number % 2)

def evenQ(number):
    return int(integerQ(number) and not (number % 2))

def n(number, digits=0):
    return number - number % 10 ** -digits

#TODO: round, log

class Wolfram(object):

    def Head(leaves, precision=10):
        return leaves[0].head
    
    def UpTo(leaves, precision=10):
        return leaves[0]

    #TODO: named (which are chained) operators - these don't use the
    #default + etc
    # change default to use an internal method with precision passable
    # which both e.g. Plus and __add__ can use

    def N(leaves, precision=10):
        # Leaves: number, precision (accuracy?)
        return [
            None, lambda: leaves[0].run(10), lambda: leaves[0].run(leaves[1])
        ][len(leaves)]()

    def StringQ(leaves, precision=10):
        return Integer(isinstance(leaves[0], str))

    def NumberQ(leaves, precision=10):
        return Integer(isinstance(leaves[0], Number))

    def IntegerQ(leaves, precision=10):
        return leaves[0].is_integer()

    def OddQ(leaves, precision=10):
        return leaves[0].is_odd()

    def EvenQ(leaves, precision=10):
        return leaves[0].is_even()

    def TrueQ(leaves, precision=10):
        return leaves[0] == _True

    def FalseQ(leaves, precision=10):
        return leaves[0] == _False

    def Sqrt(leaves, precision=10):

        def calculate_sqrt(n, precision):
            # TODO: there's too much precisions
            if isinstance(precision, Expression):
                precision = precision.to_number()
            precision = max(precision, 1)
            digits = int(log10(n) + 1) // 2
            try: # TODO: avoid try
                result = (
                    int(sqrt(n) * 10 ** (precision - digits))
                    if precision > digits else
                    int(sqrt(n)) // 10 ** (digits - precision)
                )
            except:
                result = (
                    int(exp(log(n) / 2) * 10 ** (precision - digits))
                    if precision > digits else
                    int(exp(log(n) / 2)) // 10 ** (digits - precision)
                )
            if precision > digits:
                n *= 10 ** ((precision - digits) * 2)
            else:
                n //= 10 ** ((digits - precision) * 2)
            difference = result * result - n
            while difference >= result or difference <= -result:
                result = result - ((difference + result) // (2 * result))
                difference = result * result - n
            while not result % 10:
                result //= 10
                precision -= 1
            return Real(result, -precision + digits)

        return calculate_sqrt(leaves[0].to_number(), precision)

    pattern_test_lookup = {}

    def PatternTest(leaves, precision=10):
        if leaves[0] == _:
            return Wolfram.pattern_test_lookup[leaves[1]]
        if leaves[0] == __:
            return Pattern(
                "(?:%s)+" * str(pattern_test_lookup[leaves[1]])
            )
        if leaves[0] == ___:
            return Pattern(
                "(?:%s)*" * str(pattern_test_lookup[leaves[1]])
            )

    # https://reference.wolfram.com/language/ref/Flatten.html
    # TODO: test, implement fourth overload
    def Flatten(leaves, precision=10):
        n = leaves[1] - 1 if len(leaves) > 1 else -1
        correct_head = (
            (lambda x: x.head == leaves[2])
            if len(leaves) > 2 else
            lambda x: True
        )
        if not n:
            return leaves[0]
        head = leaves[0].head
        if len(leaves) > 1 and isinstance(leaves[1], List):
            next_indices = [
                list(filter(None, map(lambda n: n - 1, sublist)))
                for sublist in leaves[1]
            ]
            lookup = {}
        if type(head) == type and issubclass(head, Expression):
            return leaves[0].head(*[
                item
                for element in leaves[0].leaves
                for item in (
                    Wolfram.Flatten([element, n - 1] + leaves[2:]).leaves
                    if (
                        isinstance(element, Expression) and
                        len(element.leaves) and correct_head(element)
                    ) else
                    [element]
                )
            ])
        return Expression(
            head, 
            [item for element in leaves[0].leaves for item in (
                Wolfram.Flatten([element, n - 1] + leaves[2:]).leaves
                if (
                    isinstance(element, Expression) and
                    len(element.leaves) and correct_head(element)
                ) else
                [element]
            )]
        )

    def StringJoin(leaves, precision=10):
        return String(
            "".join(map(str, Wolfram.Flatten([List(*leaves)]).leaves))
        )

    def StringLength(leaves, precision=10):
        if isinstance(leaves[0], List):
            return List(*[
                Wolfram.StringLength([item])
                for item in leaves[0].leaves
            ])
        return Integer(len(leaves[0].leaves[0]))

    def StringSplit(leaves, precision=10):
        # TODO: implement patterns, RegularExpression
        if isinstance(leaves[0], List):
            other_leaves = leaves[1:]
            return create_expression([
               Wolfram.StringSplit([item] + other_leaves)
               for item in leaves[0].leaves
            ])
        ignorecase, maxsplit = (
            (
                ["(?i)" * (leaves[2].leaves == [IgnoreCase, _True]), 0]
                if type(leaves[2]) == Rule else
                ["", leaves[2].to_number()]
            )
            if len(leaves) > 2 else
            ["", 0]
        )
        string = str(leaves[0])
        if len(leaves) == 1:
            result = r_whitespace.split(string, maxsplit)
            return create_expression(result[
                not result[0]:
                max(1, len(result) - (not(result[-1])))
            ])
        splitter = leaves[1]
        splitter_type = type(leaves[1])
        if splitter_type == String:
            result = (
                split(ignorecase + re_escape(str(splitter)), string, maxsplit)
            )
            return create_expression(result[
                not result[0]:
                max(1, len(result) - (not(result[-1])))
            ])
        if isinstance(splitter, Pattern):
            result = split(ignorecase + str(splitter), string, maxsplit)
            return create_expression(result[
                not result[0]:
                max(1, len(result) - (not(result[-1])))
            ])
        if splitter_type == List:
            if isinstance(splitter.leaves[0], Pattern):
                result = split(
                    ignorecase + "(" + "|".join(list(map(
                        str, splitter.leaves
                    ))) + ")",
                    string,
                    maxsplit
                )
            if isinstance(splitter.leaves[0], Rule):
                lookup = {}
                for rule in splitter.leaves:
                    lookup[rule.leaves[0]] = rule.leaves[1]
                result = split(
                    ignorecase + "(" + "|".join(list(map(
                        lambda l: re_escape(str(l.leaves[0])),
                        splitter.leaves
                    ))) + ")",
                    string,
                    maxsplit
                )
                for i in range(1, len(result), 2):
                    result[i] = lookup[result[i]]
                return create_expression(result[
                    not result[0]:
                    max(1, len(result) - (not(result[-1])))
                ])
            result = split(
                ignorecase + "|".join(list(map(
                    lambda string: re_escape(str(string)),
                    splitter.leaves
                ))),
                string,
                maxsplit
            )
            return create_expression(result[
                not result[0]:
                max(1, len(result) - (not(result[-1])))
            ])
        # Assume Rule
        result = []
        splitted = split(
            ignorecase + re_escape(str(splitter.leaves[0])), string, maxsplit
        )
        for string in splitted:
            result += [string, splitter.leaves[1]]
        return create_expression(result[not result[0]:-1 - (not result[-1])])

    def StringTake(leaves, precision=10):
        if type(leaves[0]) == List:
            return List(*[
                Wolfram.StringTake([item, leaves[1]])
                for item in leaves[0].leaves
            ])
        string = str(leaves[0])
        if isinstance(leaves[1], Number):
            n = int(leaves[1].to_number())
            if n < 0:
                return String(string[n:])
            return String(string[:n])
        if leaves[1].head == Wolfram.UpTo:
            return String(string[:int(leaves[1].to_number())])
        # Assume List
        if (
            isinstance(leaves[1].leaves[0], List) or
            leaves[1].leaves[0].head == Wolfram.UpTo
        ):
            return List(*[
                Wolfram.StringTake([leaves[0], item])
                for item in leaves[1].leaves
            ])
        length = len(leaves[1].leaves)
        leaves = list(map(
            lambda n: n + ((len(string) + 1) if n < 0 else 0),
            map(lambda n: n.to_number(), leaves[1].leaves)
        ))
        if length == 1:
            return String(string[leaves[0] - 1])
        if length == 2:
            return String(string[leaves[0] - 1:leaves[1]:])
        return String(string[leaves[0] - 1:leaves[1]:leaves[2]])

    def StringDrop(leaves, precision=10):
        if type(leaves[0]) == List:
            return List(*[
                Wolfram.StringDrop([item, leaves[1]])
                for item in leaves[0].leaves
            ])
        string = str(leaves[0])
        if isinstance(leaves[1], Number):
            n = int(leaves[1].to_number())
            if n < 0:
                return String(string[:n])
            return String(string[n:])
        if leaves[1].head == Wolfram.UpTo:
            return String(string[int(leaves[1].to_number()):])
        # Assume List
        if (
            isinstance(leaves[1].leaves[0], List) or
            leaves[1].leaves[0].head == Wolfram.UpTo
        ):
            return List(*[
                Wolfram.StringDrop([leaves[0], item])
                for item in leaves[1].leaves
            ])
        length = len(leaves[1].leaves)
        leaves = list(map(
            lambda n: n + ((len(string) + 1) if n < 0 else 0),
            map(lambda n: n.to_number(), leaves[1].leaves)
        ))
        if length == 1:
            return String(string[:leaves[0] - 1] + string[leaves[0]:])
        if length == 2:
            return String(string[:leaves[0] - 1] + string[leaves[1]:])
        # TODO: more performant
        middle = list(string[leaves[0] - 1:leaves[1]])
        del middle[::leaves[2]]
        return String(
            string[:leaves[0] - 1] +
            "".join(middle) +
            string[leaves[1]:]
        )

    def StringPart(leaves, precision=10):
        if type(leaves[0]) == List:
            return List(*[
                Wolfram.StringPart([item, leaves[1]])
                for item in leaves[0].leaves
            ])
        string = str(leaves[0])
        if isinstance(leaves[1], Number):
            number = int(leaves[1].to_number())
            number += ((len(string) + 1) if number < 0 else 0)
            return String(string[number - 1])
        if isinstance(leaves[1], List):
            leaves = list(map(
                lambda n: n + ((len(string) + 1) if n < 0 else 0),
                map(lambda n: n.to_number(), leaves[1].leaves)
            ))
            return List(*[
                String(string[leaf - 1])
                for leaf in leaves
            ])
        # Assume Span
        return List(*[
            String(char)
            for char in leaves[1].process(string)
        ])
# TODO: Except, StringExtract

    def StringReplace(leaves, precision=10):
        if isinstance(leaves[0], List):
            other_leaves = leaves[1:]
            return List(*[
                Wolfram.StringReplace([item] + other_leaves)
                for item in leaves[0].leaves
            ])
        ignorecase, maxreplace = (
            (
                ["(?i)" * (leaves[2].leaves == [IgnoreCase, _True]), 0]
                if type(leaves[2]) == Rule else
                ["", leaves[2].to_number()]
            )
            if len(leaves) > 2 else
            ["", 0]
        )
        string = str(leaves[0])
        string = str(leaves[0])
        if len(leaves) == 1:
            return lambda items: StringReplace([items, leaves[0]])
        replacer = leaves[1]
        replacer_type = type(leaves[1])
        if replacer_type == String:
            return create_expression(sub(
                ignorecase + re_escape(str(replacer)),
                string,
                maxreplace
            ))
        if replacer_type == List:
            #Assume Rule
            lookup = {}
            for rule in replacer.leaves:
                lookup[rule.leaves[0]] = rule.leaves[1]
            result = split(
                "(" + "|".join(list(map(
                    lambda l: re_escape(str(l.leaves[0])),
                    replacer.leaves
                ))) + ")",
                string,
                maxreplace
            )
            for i in range(1, len(result), 2):
                result[i] = lookup[result[i]]
            return String("".join(result))
        # Assume Rule
        result = []
        splitted = split(
            ignorecase + re_escape(str(replacer.leaves[0])), string, maxreplace
        )
        for string in splitted:
            result += [string, replacer.leaves[1]]
        return String("".join(result[:-1]))

    def StringCount(leaves, precision=10):
        if isinstance(leaves[0], List):
            other_leaves = leaves[1:]
            return List(*[
                Wolfram.StringCount([item] + other_leaves)
                for item in leaves[0].leaves
            ])
        if isinstance(leaves[1], List):
            return Integer(len(findall("|".join(list(map(
                lambda l: re_escape(str(l.leaves[0])),
                leaves[1].leaves
            ))))))
        # assume String
        return Integer(str(leaves[0]).count(str(leaves[1])))

    def StringStartsQ(leaves, precision=10):
        if len(leaves) == 1:
            return lambda *things: Wolfram.StringStartsQ(leaves[0] + things)
        if isinstance(leaves[0], List):
            return List(*[
                Wolfram.StringStartsQ([item] + leaves[1:])
                for item in leaves[0].leaves
            ])
        if (
            len(leaves) > 2 and
            type(leaves[2]) == Rule and
            leaves[2].leaves == [IgnoreCase, _True]
        ):
            return boolean(
                match("(?i)" + re_escape(str(leaves[1])), str(leaves[0]))
            )
        return boolean(str(leaves[0]).startswith(str(leaves[1])))

    def StringEndsQ(leaves, precision=10):
        if len(leaves) == 1:
            return lambda *things: Wolfram.StringStartsQ(leaves[0] + things)
        if isinstance(leaves[0], List):
            return List(*[
                Wolfram.StringEndsQ([item] + leaves[1:])
                for item in leaves[0].leaves
            ])
        if (
            len(leaves) > 2 and
            type(leaves[2]) == Rule and
            leaves[2].leaves == [IgnoreCase, _True]
        ):
            return boolean(
                search("(?i)" + re_escape(str(leaves[1])) + "$", str(leaves[0]))
            )
        return boolean(str(leaves[0]).endswith(str(leaves[1])))

    def StringContainsQ(leaves, precision=10):
        if len(leaves) == 1:
            return lambda *things: Wolfram.StringContainsQ(leaves[0] + things)
        if isinstance(leaves[0], List):
            other_leaves = leaves[1:]
            return List(*[
                Wolfram.StringContainsQ([item] + other_leaves)
                for item in leaves[0].leaves
            ])
        if (
            len(leaves) > 2 and
            type(leaves[2]) == Rule and
            leaves[2].leaves == [IgnoreCase, _True]
        ):
            return boolean(
                search("(?i)" + re_escape(str(leaves[1])), str(leaves[0]))
            )
        return boolean(str(leaves[1]) in str(leaves[0]))

    def PrintableAsciiQ(leaves, precision=10):
        if isinstance(leaves[0], List):
            return List(*[
                Wolfram.PrintableAsciiQ([item])
                for item in leaves[0].leaves
            ])
        return boolean(match("[ -~]*$", str(leaves[0])))

    def LetterQ(leaves, precision=10):
        return boolean(match("\p{L}*$", str(leaves[0])))

    def UpperCaseQ(leaves, precision=10):
        return boolean(match("\p{Lu}*$", str(leaves[0])))

    def LowerCaseQ(leaves, precision=10):
        return boolean(match("\p{Ll}*$", str(leaves[0])))

    def DigitQ(leaves, precision=10):
        return boolean(match("\d*$", str(leaves[0])))

    def CharacterRange(leaves, precision=10):
        if isinstance(leaves[0], String):
            start, end = ord(leaves[0]), ord(leaves[1])
            return List(*map(chr, range(start, end)))
        return List(*map(chr, range(leaves[0], leaves[1])))

    date_pattern_lookup = {
        "Second": "(?:[0-5]\d|60)",
        "Minute": "(?:[0-5]\d|60)",
        "Hour": "(?:[01]\d|2[0-4])",
    }
    # TODO: date pattern, need to test on mathematica e.g. feb 30 and hour 24

    ### Constants

    def ChamperowneNumber(leaves, precision=10):

        def calculate_champerowne(precision, base=10):
            # TODO redo, it's not done at all
            if isinstance(precision, Expression):
                precision = precision.to_number()
            precision = max(precision - 1, 0)
            number = 0
            numerator = 10 ** (precision + 2)
            denominator = base
            multiplier = base
            i = 1
            next_power = base
            j = 1
            division = numerator // denominator
            while division:
                number = number + division
                denominator *= multiplier
                i += 1
                if i >= next_power:
                     number *= base
                     numerator *= base
                     multiplier *= base
                     next_power *= base
                     j += 1
                division = numerator // denominator
            return Real(
                number // (10 * next_power),
                -precision,
                precision=precision
            )

        return Expression(
            None,
            [],
            lambda precision=10: Wolfram.calculate_champerowne(
                precision,
                leaves[0]
            )
        ) if len(leaves) else Expression(
            None,
            [],
            lambda precision=10: Wolfram.calculate_champerowne(precision)
        )

    # TODO: hide this function from scope
    def calculate_e(precision):
        if isinstance(precision, Expression):
            precision = precision.to_number()
        precision = max(precision - 1, 0)
        number = 0
        numerator = 10 ** (precision + 2)
        denominator = 1
        i = 1
        next_power_of_10 = 10
        j = 1
        division = numerator // denominator
        while division:
            number = number + division
            denominator *= i
            i += 1
            if i >= next_power_of_10:
                 number *= 10
                 numerator *= 10
                 next_power_of_10 *= 10
                 j += 1
            division = numerator // denominator
        return Real(
            number // (10 * next_power_of_10),
            -precision,
            precision=precision
        )

    E = Expression(
        None, [], lambda precision=10: Wolfram.calculate_e(precision)
    )

    # From https://www.craig-wood.com/nick/pub/pymath/pi_chudnovsky_bs.py

    def calculate_pi(precision):
        if isinstance(precision, Expression):
            precision = precision.to_number()
        precision = max(precision - 1, 0)
        # C = 640320,  C ** 3 // 24:
        C3_OVER_24 = 10939058860032000

        def pi_sqrt(n, one):
            floating_point_precision = 10**16
            n_float = (
                float((n * floating_point_precision) // one) /
                floating_point_precision
            )
            x = (
                int(floating_point_precision *
                sqrt(n_float)) * one
            ) // floating_point_precision
            n_one = n * one
            while 1:
                x_old = x
                x = (x + n_one // x) // 2
                if x == x_old:
                    break
            return x

        def bs(a, b):
            if b - a == 1:
                if a == 0:
                    Pab = Qab = 1
                else:
                    Pab = (6 * a - 5) * (2 * a - 1) * (6 * a - 1)
                    Qab = a * a * a * C3_OVER_24
                Tab = Pab * (13591409 + 545140134 * a)
                if a & 1:
                    Tab = -Tab
            else:
                m = (a + b) // 2
                Pam, Qam, Tam = bs(a, m)
                Pmb, Qmb, Tmb = bs(m, b)
                Pab, Qab, Tab = Pam * Pmb, Qam * Qmb, Qmb * Tam + Pam * Tmb
            return Pab, Qab, Tab

        N = (precision + 1) // 14 + 1
        _, Q, T = bs(0, N)
        one = 10 ** precision
        sqrtC = pi_sqrt(10005 * one, one)
        return Real((Q * 426880 * sqrtC) // T, -precision, precision=precision)

    Pi = Expression(
        None, [],
        lambda precision=10: Wolfram.calculate_pi(precision)
    )

    Degree = Pi / 180 # TODO: make sure this still accepts precision arg

def functionify(head):
    return lambda *leaves: Expression(head, leaves)

iq = integerQ
oq = oddQ
eq = evenQ
F = _False
T = _True
IC = IgnoreCase
Pi = Wolfram.Pi
E = Wolfram.E
Deg = Degree = Wolfram.Degree
Rt = Sqrt = functionify(Wolfram.Sqrt)
UT = UpTo = functionify(Wolfram.UpTo)
N = functionify(Wolfram.N)
PT = PatternTest = functionify(Wolfram.PatternTest)
SQ = StringQ = functionify(Wolfram.StringQ)
NQ = NumberQ = functionify(Wolfram.NumberQ)
IQ = IntegerQ = functionify(Wolfram.IntegerQ)
OQ = OddQ = functionify(Wolfram.OddQ)
EQ = EvenQ = functionify(Wolfram.EvenQ)
TQ = TrueQ = functionify(Wolfram.TrueQ)
FQ = FalseQ = functionify(Wolfram.FalseQ)
PAQ = PrintableAsciiQ = functionify(Wolfram.PrintableAsciiQ)
LQ = LetterQ = functionify(Wolfram.LetterQ)
LCQ = LowerCaseQ = functionify(Wolfram.LowerCaseQ)
UCQ = UpperCaseQ = functionify(Wolfram.UpperCaseQ)
DQ = DigitQ = functionify(Wolfram.DigitQ)
Flatten = functionify(Wolfram.Flatten)
SJ = StringJoin = functionify(Wolfram.StringJoin)
SL = StringLength = functionify(Wolfram.StringLength)
SS = StringSplit = functionify(Wolfram.StringSplit)
ST = StringTake = functionify(Wolfram.StringTake)
SD = StringDrop = functionify(Wolfram.StringDrop)
SP = StringPart = functionify(Wolfram.StringPart)
SR = StringReplace = functionify(Wolfram.StringReplace)
SC = StringCount = functionify(Wolfram.StringCount)
SSQ = StringStartsQ = functionify(Wolfram.StringStartsQ)
SEQ = StringEndsQ = functionify(Wolfram.StringEndsQ)
SCQ = StringContainsQ = functionify(Wolfram.StringContainsQ)
# TODO: make capital form arbitrary precision
l2 = Log2 = log2
la = Log10 = log10
ln = Log = log
rt = functionify(Wolfram.Sqrt)
#Sin = sin
#Cos = cos
#Tan = tan
#ArcSin = asin
#ArcCos = acos
#ArcTan = atan

for key, value in (
    (LetterQ, LetterCharacter),
    (LowerCaseQ, Pattern(r"\p{Ll}")),
    (UpperCaseQ, Pattern(r"\p{Lu}")),
    (DigitQ, DigitCharacter)
):
    Wolfram.pattern_test_lookup[key] = value
