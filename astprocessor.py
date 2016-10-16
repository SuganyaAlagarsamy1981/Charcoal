from charcoaltoken import CharcoalToken
from unicodegrammars import UnicodeGrammars


def PassThrough(result):
    return result

ASTProcessor = {
    CharcoalToken.Arrow: [
        lambda result: "Left",
        lambda result: "Up",
        lambda result: "Right",
        lambda result: "Down",
        lambda result: "Up Left",
        lambda result: "Up Right",
        lambda result: "Down Right",
        lambda result: "Down Left"
    ],
    CharcoalToken.Multidirectional: [
        lambda result: ["Multidirectional"] + result
    ] + [
        lambda result: [result[1][0], result[0]] + result[1][1:]
    ] * (len(UnicodeGrammars[CharcoalToken.Multidirectional]) - 2) + [
        lambda result: ["Multidirectional"]
    ],
    CharcoalToken.Side: [
        lambda result: ["Side"] + result
    ],
    CharcoalToken.String: [
        lambda result: ["String \"%s\"" % result[0]]
    ],
    CharcoalToken.Number: [
        lambda result: ["Number %s" % str(result[0])]
    ],
    CharcoalToken.Name: [
        lambda result: ["Identifier %s" % str(result[0])]
    ],
    CharcoalToken.Separator: [
        lambda result: None,
        lambda result: None
    ],

    CharcoalToken.Arrows: [
        lambda result: [result[1][0], result[0]] + result[1][1:],
        lambda result: ["Arrows", result[0]]
    ],
    CharcoalToken.Sides: [
        lambda result: ["Sides", result[0]] + result[1][1:],
        lambda result: ["Sides", result[0]]
    ],
    CharcoalToken.Expressions: [
        lambda result: ["Expressions", result[0]] + result[2][1:],
        lambda result: ["Expressions", result[0]]
    ],

    CharcoalToken.List: [
        lambda result: ["List"] + result[1][1:]
    ],
    CharcoalToken.ArrowList: [
        lambda result: ["Arrow list"] + result[1][1:]
    ],

    CharcoalToken.Expression: [
        lambda result: result[0],
        lambda result: result[0],
        lambda result: result[0],
        lambda result: result[0],
        lambda result: result,
        lambda result: result,
        lambda result: result[0]
    ],
    CharcoalToken.Niladic: [
        lambda result: "Input String",
        lambda result: "Input Number",
        lambda result: "Random"
    ],
    CharcoalToken.Monadic: [
        lambda result: "Negative",
        lambda result: "Length",
        lambda result: "Not",
        lambda result: "Cast",
        lambda result: "Random",
        lambda result: "Evaluate"
    ],
    CharcoalToken.Dyadic: [
        lambda result: "Sum",
        lambda result: "Difference",
        lambda result: "Product",
        lambda result: "Quotient",
        lambda result: "Modulo",
        lambda result: "Equals",
        lambda result: "Less Than",
        lambda result: "Greater Than",
        lambda result: "And",
        lambda result: "Or",
        lambda result: "Cycle and chop"
    ],

    CharcoalToken.Program: [
        lambda result:  [result[1][0], result[0]] + result[1][1:],
        lambda result: ["Program"]
    ],
    CharcoalToken.Body: [
        lambda result: result[1],
        lambda result: result[0]
    ],
    CharcoalToken.Command: [
        lambda result: ["Input String", result[1]],
        lambda result: ["Input Number", result[1]],
        lambda result: ["Evaluate", result[1]],
        lambda result: ["Print"] + result,
        lambda result: ["Print"] + result,
        lambda result: ["Multiprint"] + result[1:],
        lambda result: ["Multiprint"] + result[1:],
        lambda result: ["Rectangle"] + result[1:],
        lambda result: ["Box"] + result[1:],
        lambda result: ["Polygon"] + result[1:],
        lambda result: ["Polygon"] + result[1:],
        lambda result: ["Move"] + result,
        lambda result: ["Move"] + result[1:],
        lambda result: ["Move"] + result[1:],
        lambda result: ["Pivot Left", result[1]],
        lambda result: ["Pivot Left"],
        lambda result: ["Pivot Right", result[1]],
        lambda result: ["Pivot Right"],
        lambda result: ["Jump"] + result[1:],
        lambda result: ["Rotate copy"] + result[1:],
        lambda result: ["Reflect copy"] + result[1:],
        lambda result: ["Rotate overlap"] + result[1:],
        lambda result: ["Reflect overlap"] + result[1:],
        lambda result: ["Rotate"] + result[1:],
        lambda result: ["Reflect"] + result[1:],
        lambda result: ["Copy"] + result[1:],
        lambda result: ["For"] + result[1:],
        lambda result: ["While"] + result[1:],
        lambda result: ["If"] + result[1:],
        lambda result: ["If"] + result[1:],
        lambda result: ["Assign"] + result[1:],
        lambda result: ["Fill"] + result[1:],
        lambda result: ["SetBackground", result[1]],
        lambda result: ["Dump"],
        lambda result: ["Refresh for"] + result[1:],
        lambda result: ["Refresh while"] + result[1:],
        lambda result: ["Refresh", result[1]],
        lambda result: ["Refresh"]
    ]
}